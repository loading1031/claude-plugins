"""Issue mode keeps specs with their implementation; file mode keeps plan branches."""
import importlib.util
import json
from pathlib import Path
import subprocess
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / 'check_git_command.py'
spec = importlib.util.spec_from_file_location('git_policy', SCRIPT)
policy = importlib.util.module_from_spec(spec)
spec.loader.exec_module(policy)


class IssueBacklogTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.git('init', '-q')
        self.git('config', 'user.email', 'test@example.com')
        self.git('config', 'user.name', 'Test')
        (self.root / 'README.md').write_text('test\n')
        self.git('add', 'README.md')
        self.git('commit', '-qm', 'chore: initial')
        self.git('switch', '-qc', 'codex/feat/17-worldbible')

    def tearDown(self):
        self.temp.cleanup()

    def git(self, *args):
        return subprocess.run(['git', *args], cwd=self.root, check=True, capture_output=True, text=True)

    def configure(self, extra='', filename='CLAUDE.md'):
        (self.root / filename).write_text('## 기획 설정\n- 기획 폴더: docs/specs\n- 기본 브랜치: dev\n' + extra)

    def check_commit(self):
        path = self.root / 'docs/specs/worldbible.md'
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text('WorldBible requirements\n')
        self.git('add', 'docs/specs/worldbible.md')
        payload = {'cwd': str(self.root), 'tool_input': {'command': 'git commit -m "docs: 세계관 결정\n\nRefs: #17"'}}
        return subprocess.run(['python3', str(SCRIPT)], input=json.dumps(payload), text=True, capture_output=True)

    def test_existing_tracking_configuration_resumes_without_file_backlog(self):
        self.configure('- 작업지시서: issue\n- 작업 추적: loading1031/2nd-if\n')
        self.assertTrue(policy.settings(self.root)['issue_mode'])
        self.assertEqual(self.check_commit().returncode, 0)
        self.assertFalse((self.root / 'docs/specs/backlog.md').exists())

    def test_explicit_issue_mode_from_agents(self):
        self.configure('- 백로그: issue\n- 작업 추적: owner/repo\n', 'AGENTS.md')
        self.assertTrue(policy.settings(self.root)['issue_mode'])
        self.assertEqual(self.check_commit().returncode, 0)

    def test_explicit_file_mode_preserves_branch_rule(self):
        self.configure('- 백로그: file\n- 작업지시서: issue\n- 작업 추적: owner/repo\n')
        self.assertFalse(policy.settings(self.root)['issue_mode'])
        result = self.check_commit()
        self.assertEqual(result.returncode, 2)
        self.assertIn('code-branch-docs', result.stderr)

    def test_legacy_issue_instructions_keep_file_index(self):
        self.configure('- 작업지시서: issue\n')
        self.assertFalse(policy.settings(self.root)['issue_mode'])
        self.assertEqual(self.check_commit().returncode, 2)

    def test_file_mode_accepts_codex_plan_branch(self):
        self.configure('- 백로그: file\n')
        self.git('switch', '-qc', 'codex/plan/17-worldbible')
        self.assertEqual(self.check_commit().returncode, 0)

    def test_issue_mode_still_rejects_bulk_staging(self):
        self.configure('- 백로그: issue\n- 작업 추적: owner/repo\n')
        result = subprocess.run(['python3', str(SCRIPT)], input=json.dumps({'cwd': str(self.root), 'tool_input': {'command': 'git add .'}}), text=True, capture_output=True)
        self.assertEqual(result.returncode, 2)
        self.assertIn('git-add-all', result.stderr)

    def test_conflicting_settings_are_reported(self):
        self.configure('- 백로그: issue\n', 'AGENTS.md')
        self.configure('- 백로그: file\n')
        result = self.check_commit()
        self.assertEqual(result.returncode, 2)
        self.assertIn('settings-conflict', result.stderr)


if __name__ == '__main__':
    unittest.main()
