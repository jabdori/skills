import os
import subprocess
import tempfile
import unittest
from pathlib import Path


SOURCE = Path(__file__).with_name('get-agent-browser.sh')
HASHES = {
    'x86_64': 'd258593db4899577748a4b2a671a315f76f07a4553ba7fbbeaa95f0d16a4aaa8',
    'aarch64': '54eedbcaedcbd8b49f840098ea85dda653af0a036e28609b526ece068de6c0ab',
}


class InstallerTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.bin = self.root / 'bin'
        self.bin.mkdir()
        self.install = self.root / 'ab'
        source = SOURCE.read_text()
        assert '/tmp/ab' in source
        self.script = self.root / 'installer.sh'
        self.script.write_text(source.replace('/tmp/ab', str(self.install)))
        self.fake('uname', '#!/bin/sh\nprintf "%s\\n" "$MOCK_ARCH"\n')
        self.fake('curl', '#!/bin/sh\nwhile [ "$#" -gt 0 ]; do\n  if [ "$1" = --output ]; then shift; target=$1; fi\n  shift\ndone\n[ "$MOCK_CURL" = fail ] && exit 22\nprintf payload > "$target"\n')
        self.fake('sha256sum', '#!/bin/sh\nprintf "%s  %s\\n" "$MOCK_HASH" "$1"\n')
        self.fake('npm', '#!/bin/sh\nmkdir -p node_modules/.bin\nprintf "#!/bin/sh\\n[ \\"$MOCK_NPM_RUN\\" != fail ]\\n" > node_modules/.bin/agent-browser\nchmod +x node_modules/.bin/agent-browser\n')

    def fake(self, name, text):
        path = self.bin / name
        path.write_text(text)
        path.chmod(0o755)

    def run_script(self, **overrides):
        env = dict(os.environ, PATH=f'{self.bin}:{os.environ["PATH"]}',
                   MOCK_ARCH='x86_64', MOCK_HASH=HASHES['x86_64'], MOCK_CURL='ok', MOCK_NPM_RUN='ok')
        env.update(overrides)
        return subprocess.run(['bash', str(self.script)], env=env, text=True, capture_output=True)

    def test_verified_release_prints_executable_path(self):
        result = self.run_script()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), str(self.install / 'agent-browser'))
        self.assertTrue((self.install / 'agent-browser').stat().st_mode & 0o111)

    def test_arm64_selects_its_digest(self):
        result = self.run_script(MOCK_ARCH='aarch64', MOCK_HASH=HASHES['aarch64'])
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_bad_digest_deletes_download_and_does_not_fallback(self):
        result = self.run_script(MOCK_HASH='0' * 64)
        self.assertEqual(result.returncode, 1)
        self.assertIn('SHA-256 불일치', result.stderr)
        self.assertFalse((self.install / 'agent-browser').exists())
        self.assertFalse((self.install / 'node_modules').exists())

    def test_download_failure_uses_local_npm_only_if_cli_runs(self):
        result = self.run_script(MOCK_CURL='fail')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), str(self.install / 'node_modules/.bin/agent-browser'))

        unusable = self.run_script(MOCK_CURL='fail', MOCK_NPM_RUN='fail')
        self.assertEqual(unusable.returncode, 1)
        self.assertIn('curl로만 확인', unusable.stderr)


if __name__ == '__main__':
    unittest.main()
