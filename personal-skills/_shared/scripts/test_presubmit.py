import os
import shutil
import subprocess
import sys
import tarfile
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).with_name('presubmit.py')
REHEARSAL_ARCHIVE = os.environ.get('PRESUBMIT_REHEARSAL_ARCHIVE')


class PresubmitTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.run_git('init', '-q')
        self.run_git('config', 'user.name', 'Test')
        self.run_git('config', 'user.email', 'test@example.invalid')
        (self.root / 'app.py').write_text('print("ok")\n')
        (self.root / 'README.md').write_text('# 과제 안내\n')
        (self.root / 'protected.txt').write_text('제공 파일\n')
        (self.root / 'obsolete.txt').write_text('old\n')
        self.run_git('add', '.')
        self.run_git('commit', '-qm', 'start')

    def run_git(self, *args):
        subprocess.run(['git', *args], cwd=self.root, check=True, capture_output=True)

    def check_script(self, *args):
        return subprocess.run([sys.executable, str(SCRIPT), *args], cwd=self.root,
                              text=True, capture_output=True)

    def test_reports_changes_artifacts_and_unmentioned_code_without_writing(self):
        (self.root / 'app.py').write_text('print("changed")\n')
        (self.root / 'obsolete.txt').unlink()
        (self.root / 'notes with space.py').write_text('pass\n')
        (self.root / '.env').write_text('SECRET=sample\n')
        (self.root / 'trace.log').write_text('sample\n')
        (self.root / '__pycache__').mkdir()
        (self.root / '__pycache__/app.pyc').write_bytes(b'compiled')
        (self.root / 'node_modules').mkdir()
        (self.root / 'node_modules/new.js').write_text('module.exports = 1\n')
        (self.root / 'big.bin').write_bytes(b'x' * (5 * 1024 * 1024 + 1))
        (self.root / 'DECISIONS.md').write_text('# 결정\n')

        result = self.check_script()

        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        for label in ('app.py', 'notes with space.py', '삭제 1', '__pycache__', '.pyc', '.env', 'trace.log', 'node_modules', 'big.bin', 'DECISIONS.md'):
            self.assertIn(label, result.stdout)
        self.assertEqual((self.root / 'app.py').read_text(), 'print("changed")\n')

    def test_python_test_command_prevents_bytecode(self):
        tests = self.root / 'tests'
        tests.mkdir()
        (tests / 'test_ok.py').write_text('import unittest\nclass Smoke(unittest.TestCase):\n def test_ok(self): self.assertTrue(True)\n')
        self.run_git('add', 'tests/test_ok.py')
        self.run_git('commit', '-qm', 'test: 기본 검사를 추가함')

        result = self.check_script('--test', f'{sys.executable} -m unittest discover -s tests -v')

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn('test exit 0', result.stdout)
        self.assertFalse(list(self.root.rglob('*.pyc')))

    @unittest.skipUnless(shutil.which('node'), 'Node.js가 필요합니다')
    def test_node_command_and_decision_document(self):
        (self.root / 'app.js').write_text('export const answer = 1;\n')
        (self.root / 'test.mjs').write_text('import { test } from "node:test";\ntest("smoke", () => {});\n')
        (self.root / 'DECISIONS.md').write_text('# 결정\n')
        command = 'node --test test.mjs'

        missing = self.check_script('--test', command)
        self.assertEqual(missing.returncode, 1, missing.stdout + missing.stderr)
        self.assertIn('app.js', missing.stdout)
        self.assertIn('test exit 0', missing.stdout)

        (self.root / 'DECISIONS.md').write_text('app.js와 test.mjs를 확인했습니다.\n')
        self.run_git('add', 'app.js', 'test.mjs', 'DECISIONS.md')
        self.run_git('commit', '-qm', 'test: 문서와 검사를 맞춤')
        covered = self.check_script('--test', command)
        self.assertEqual(covered.returncode, 0, covered.stdout + covered.stderr)

    def test_requires_git_workspace(self):
        with tempfile.TemporaryDirectory() as outside:
            result = subprocess.run([sys.executable, str(SCRIPT)], cwd=outside,
                                    text=True, capture_output=True)
        self.assertEqual(result.returncode, 1)
        self.assertIn('Git', result.stdout)

    def test_failing_test_command_needs_attention(self):
        result = self.check_script('--test', f'{sys.executable} -c "import sys; sys.exit(3)"')
        self.assertEqual(result.returncode, 1)
        self.assertIn('test exit 3', result.stdout)

    def test_committed_change_is_counted_and_base_can_be_overridden(self):
        (self.root / 'app.py').write_text('print("committed")\n')
        self.run_git('add', 'app.py')
        self.run_git('commit', '-qm', 'fix: 출력 값을 수정함')
        (self.root / 'DECISIONS.md').write_text('# 결정\n')

        default = self.check_script()
        self.assertEqual(default.returncode, 1, default.stdout + default.stderr)
        self.assertIn('수정 1', default.stdout)
        self.assertIn('결정 문서에 언급되지 않은 코드: app.py', default.stdout)
        self.assertIn('결정 문서 대조: 코드 1개', default.stdout)

        head = self.check_script('--base', 'HEAD')
        self.assertEqual(head.returncode, 1, head.stdout + head.stderr)
        self.assertIn('수정 0', head.stdout)
        self.assertIn('결정 문서 대조: 코드 0개', head.stdout)
        self.assertIn('검증된 단위 커밋 없음', head.stdout)

    def test_staged_unstaged_untracked_and_deleted_are_counted_together(self):
        (self.root / 'app.py').write_text('print("working")\n')
        (self.root / 'staged.py').write_text('pass\n')
        self.run_git('add', 'staged.py')
        (self.root / 'loose.py').write_text('pass\n')
        (self.root / 'obsolete.txt').unlink()

        result = self.check_script()
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn('수정 1 · 신규 2 · 삭제 1', result.stdout)
        self.assertIn('커밋 안 된 변경', result.stdout)
        for name in ('app.py', 'staged.py', 'loose.py', 'obsolete.txt'):
            self.assertIn(name, result.stdout)

    def test_readme_change_is_protected_and_not_reverted(self):
        (self.root / 'README.md').write_text('# 바뀐 과제 안내\n')
        result = self.check_script()
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn('수정 금지 파일 변경: README.md', result.stdout)
        self.assertIn('git checkout', result.stdout)
        self.assertEqual((self.root / 'README.md').read_text(), '# 바뀐 과제 안내\n')

        self.run_git('add', 'README.md')
        self.run_git('commit', '-qm', 'docs: 안내문 변경을 기록함')
        committed = self.check_script()
        self.assertEqual(committed.returncode, 1, committed.stdout + committed.stderr)
        self.assertIn('수정 금지 파일 변경: README.md', committed.stdout)

    def test_explicit_protected_file(self):
        (self.root / 'protected.txt').write_text('변경된 파일\n')
        result = self.check_script('--protect', 'protected.txt')
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn('수정 금지 파일 변경: protected.txt', result.stdout)
        self.assertEqual((self.root / 'protected.txt').read_text(), '변경된 파일\n')

    def test_project_protected_file(self):
        (self.root / 'AGENTS.md').write_text('## 이 프로젝트\n- 수정 금지 파일: README.md, protected.txt\n')
        self.run_git('add', 'AGENTS.md')
        self.run_git('commit', '-qm', 'docs: 보호 목록을 기록함')
        (self.root / 'protected.txt').write_text('변경된 파일\n')

        result = self.check_script()
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn('수정 금지 파일 변경: protected.txt', result.stdout)
        self.assertEqual((self.root / 'protected.txt').read_text(), '변경된 파일\n')

    def test_uncommitted_change_and_no_unit_commit_warn(self):
        (self.root / 'app.py').write_text('print("changed")\n')
        result = self.check_script()
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn('커밋 안 된 변경', result.stdout)
        self.assertIn('검증된 단위 커밋 없음', result.stdout)

    def test_english_commit_summary_warns(self):
        (self.root / 'app.py').write_text('print("changed")\n')
        self.run_git('add', 'app.py')
        self.run_git('commit', '-qm', 'feat: add feature')
        result = self.check_script()
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn('커밋 메시지 형식 또는 한국어 요약', result.stdout)

    def test_valid_committed_change_has_no_new_warning(self):
        (self.root / 'app.py').write_text('print("changed")\n')
        self.run_git('add', 'app.py')
        self.run_git('commit', '-qm', 'fix: 출력 값을 고침')
        result = self.check_script()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn('결과: 추가 경고 없음', result.stdout)

    @unittest.skipUnless(REHEARSAL_ARCHIVE and Path(REHEARSAL_ARCHIVE).is_file(), '실제 제출물 경로가 필요합니다')
    def test_real_wafer_submission_counts_commits_and_document_coverage(self):
        with tempfile.TemporaryDirectory() as tmp:
            with tarfile.open(REHEARSAL_ARCHIVE, 'r:gz') as archive:
                archive.extractall(tmp, filter='data')
            result = subprocess.run([sys.executable, str(SCRIPT)], cwd=tmp,
                                    text=True, capture_output=True)
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn('변경: 수정 2 · 신규 4 · 삭제 0', result.stdout)
        self.assertIn('결정 문서 대조: 코드 2개', result.stdout)
        self.assertIn('.pyc', result.stdout)


if __name__ == '__main__':
    unittest.main()
