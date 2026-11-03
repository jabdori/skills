"""임시 홈·작은 런타임 자료로 설치 실패와 기존 파일 보존을 검사합니다."""
import hashlib
import io
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import tarfile
import tempfile
import unittest

SHARED = Path(__file__).resolve().parents[1]
GO_FAILURE = 'Go 설치 실패 — 이미 설치된 Node.js 22나 Python 3.11 스택을 고려'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


class StackPackInstallerTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix='stack pack test ')
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.shared = self.root / 'shared'
        (self.shared / 'scripts').mkdir(parents=True)
        shutil.copy2(SHARED/'scripts/install-stack-pack.sh', self.shared/'scripts/install-stack-pack.sh')
        self.lock = json.loads((SHARED/'stack-packs.lock.json').read_text())
        for spec in self.lock['skills']:
            for relative in spec['files']:
                target = self.shared/'vendor'/spec['vendor']/relative
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(SHARED/'vendor'/spec['vendor']/relative, target)
        go_license = self.shared/'vendor/go-toolchain/LICENSE'
        go_license.parent.mkdir(parents=True)
        shutil.copy2(SHARED/'vendor/go-toolchain/LICENSE', go_license)
        self.home = self.root/'home'
        self.home.mkdir()
        self.config = self.home/'.codex/config.toml'
        self.config.parent.mkdir()
        self.config.write_text('model = "untouched-fixture"\n')
        self.bin = self.root/'bin'
        self.bin.mkdir()
        self.env = {**os.environ, 'HOME': str(self.home), 'XDG_CACHE_HOME': str(self.home/'.cache'),
                    'PATH': str(self.bin)+os.pathsep+os.environ['PATH']}
        self.git_log = self.root/'git-used'
        self.fake('git', '#!/bin/sh\nprintf used > "'+str(self.git_log)+'"\nexit 22\n')
        self.write_lock()

    def fake(self, name, text):
        path = self.bin/name
        path.write_text(text)
        path.chmod(0o755)

    def write_lock(self):
        (self.shared/'stack-packs.lock.json').write_text(json.dumps(self.lock))

    def run_installer(self, *args):
        return subprocess.run(['bash', str(self.shared/'scripts/install-stack-pack.sh'), *args],
                              env=self.env, text=True, capture_output=True, timeout=30)

    def installed(self):
        root = self.home/'.agents/skills'
        return sorted(p.name for p in root.iterdir()) if root.exists() else []

    def fake_go(self, malicious=False):
        if platform.system() != 'Linux':
            self.skipTest('Go 설치 단위 검사는 Linux 연습 컨테이너에서 실행합니다')
        arch = {'aarch64':'arm64', 'x86_64':'amd64'}[platform.machine()]
        variant = 'linux-'+arch
        spec = self.lock['go']['archives'][variant]
        tar_path = self.home/'.cache/stack-packs/downloads'/spec['filename']
        tar_path.parent.mkdir(parents=True, exist_ok=True)
        with tarfile.open(tar_path, 'w:gz') as archive:
            payload = ('#!/bin/sh\nprintf "go version '+self.lock['go']['version']+' linux/'+arch+'\\n"\n').encode()
            info = tarfile.TarInfo('go/bin/go')
            info.size, info.mode = len(payload), 0o755
            archive.addfile(info, io.BytesIO(payload))
            if malicious:
                info = tarfile.TarInfo('../outside')
                info.size = 1
                archive.addfile(info, io.BytesIO(b'x'))
        spec['sha256'] = digest(tar_path)
        cli = self.lock['go']['guidelines_cli']
        binary = self.shared/'vendor'/cli['binaries'][variant]['path']
        binary.parent.mkdir(parents=True, exist_ok=True)
        binary.write_text('#!/bin/sh\nprintf "'+cli['version']+'\\n"\n')
        binary.chmod(0o755)
        cli['binaries'][variant]['sha256'] = digest(binary)
        for relative in cli['licenses']:
            target = self.shared/'vendor'/relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(SHARED/'vendor'/relative, target)
        self.write_lock()
        return tar_path

    def seed_remote_cache(self):
        spec = self.lock['remote']
        cache = self.home/'.cache/stack-packs/remote'/spec['commit']
        snapshot = {'repo': spec['repo'], 'commit': spec['commit'], 'skills': {}}
        for name in spec['skills']:
            folder = cache/name
            folder.mkdir(parents=True)
            file = folder/'SKILL.md'
            file.write_text('---\nname: '+name+'\ndescription: Local test fixture\n---\n')
            snapshot['skills'][name] = {'SKILL.md': digest(file)}
        (cache/'snapshot.json').write_text(json.dumps(snapshot))
        return cache

    def test_common_is_offline_idempotent_and_keeps_config(self):
        before = self.config.read_bytes()
        first = self.run_installer('common', '--offline')
        self.assertEqual(first.returncode, 0, first.stderr)
        second = self.run_installer('common', '--offline')
        self.assertEqual(second.returncode, 0, second.stderr)
        self.assertEqual(self.installed(), ['find-skills'])
        self.assertTrue((self.home/'.agents/skills/find-skills/LICENSE').is_file())
        self.assertEqual(self.config.read_bytes(), before)
        self.assertFalse(self.git_log.exists())

    def test_unknown_pack_installs_nothing(self):
        result = self.run_installer('unknown')
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(self.installed(), [])

    def test_modified_vendor_is_rejected(self):
        file = self.shared/'vendor/find-skills/SKILL.md'
        file.write_text(file.read_text()+'\nchanged\n')
        result = self.run_installer('common', '--offline')
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('SHA-256', result.stderr)
        self.assertEqual(self.installed(), [])

    def test_existing_personal_skill_is_not_overwritten(self):
        folder = self.home/'.agents/skills/find-skills'
        folder.mkdir(parents=True)
        (folder/'SKILL.md').write_text('my skill')
        result = self.run_installer('common', '--offline')
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual((folder/'SKILL.md').read_text(), 'my skill')

    def test_cold_offline_react_does_not_fetch_or_partially_install(self):
        result = self.run_installer('react', '--offline')
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('오프라인', result.stderr)
        self.assertFalse(self.git_log.exists())
        self.assertEqual(self.installed(), [])

    def test_failed_online_fetch_installs_nothing(self):
        result = self.run_installer('react')
        self.assertNotEqual(result.returncode, 0)
        self.assertTrue(self.git_log.exists())
        self.assertEqual(self.installed(), [])

    def test_warm_offline_react_uses_verified_cache(self):
        self.seed_remote_cache()
        result = self.run_installer('react', '--offline')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.installed(), sorted(['find-skills', 'shadcn', *self.lock['remote']['skills']]))
        self.assertFalse(self.git_log.exists())

    def test_multiple_packs_share_common_and_keep_existing_config(self):
        self.fake_go()
        self.seed_remote_cache()
        result = self.run_installer('go', 'react', '--offline')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.installed(), sorted(['find-skills', 'use-modern-go', 'shadcn', *self.lock['remote']['skills']]))
        self.assertTrue((self.home/'.local/go/bin/go').is_file())
        self.assertEqual(self.config.read_text(), 'model = "untouched-fixture"\n')

    def test_tampered_remote_cache_is_rejected(self):
        cache = self.seed_remote_cache()
        file = cache/'web-design-guidelines/SKILL.md'
        file.write_text(file.read_text()+'changed')
        result = self.run_installer('react', '--offline')
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('SHA-256', result.stderr)
        self.assertEqual(self.installed(), [])

    def test_go_installs_to_home_and_is_idempotent(self):
        self.fake_go()
        result = self.run_installer('go', '--offline')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue((self.home/'.local/go/bin/go').is_file())
        self.assertIn('export PATH=', result.stdout)
        again = self.run_installer('go', '--offline')
        self.assertEqual(again.returncode, 0, again.stderr)
        self.assertEqual(self.config.read_text(), 'model = "untouched-fixture"\n')

    def test_cold_offline_go_only_prints_stack_alternative(self):
        result = self.run_installer('go', '--offline')
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(result.stdout, '')
        self.assertEqual(result.stderr, GO_FAILURE+'\n')
        self.assertEqual(self.installed(), [])
        self.assertFalse((self.home/'.local/go').exists())

    def test_unwritable_go_destination_only_prints_alternative(self):
        self.fake_go()
        folder = self.home/'.local'
        folder.mkdir()
        folder.chmod(0o500)
        self.addCleanup(folder.chmod, 0o700)
        result = self.run_installer('go', '--offline')
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(result.stderr, GO_FAILURE+'\n')
        self.assertEqual(result.stdout, '')
        self.assertEqual(self.installed(), [])

    def test_bad_go_archive_checksum_is_rejected_before_install(self):
        path = self.fake_go()
        path.write_bytes(path.read_bytes()+b'broken')
        result = self.run_installer('go', '--offline')
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(result.stderr.strip(), GO_FAILURE)
        self.assertFalse((self.home/'.local/go').exists())
        self.assertEqual(self.installed(), [])

    def test_go_archive_cannot_escape_installation_directory(self):
        self.fake_go(malicious=True)
        result = self.run_installer('go', '--offline')
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(result.stderr.strip(), GO_FAILURE)
        self.assertFalse(list(self.home.rglob('outside')))
        self.assertEqual(self.installed(), [])

    def test_unmanaged_existing_go_is_preserved(self):
        self.fake_go()
        folder = self.home/'.local/go'
        folder.mkdir(parents=True)
        (folder/'keep').write_text('existing SDK')
        result = self.run_installer('go', '--offline')
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual((folder/'keep').read_text(), 'existing SDK')
        self.assertEqual(self.installed(), [])

    def test_python_and_node_use_existing_runtimes(self):
        result = self.run_installer('python', 'node', '--offline')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('Python ', result.stdout)
        self.assertEqual(self.installed(), ['find-skills'])


if __name__ == '__main__':
    unittest.main()
