
import unittest
import sys
from pathlib import Path

# Add scripts to path
scripts_path = Path(__file__).resolve().parent.parent.parent / "scripts"
sys.path.append(str(scripts_path))

try:
    from commit_check import parse_issue_from_branch
except ImportError:
    # If failed, try adjusting path or direct import? 
    # The structure is .agent/skills/github-repo-bootstrap/scripts/commit_check.py
    # Test is .agent/skills/github-repo-bootstrap/tests/unit/test_commit_check.py
    # Parent^3 is .agent/skills/github-repo-bootstrap
    pass

from commit_check import parse_issue_from_branch

class TestCommitCheck(unittest.TestCase):
    def test_parse_valid_branch(self):
        pattern = r'^(feat|fix|chore|docs|refactor)\/(?P<id>\d+)(-.+)?$'
        self.assertEqual(parse_issue_from_branch("feat/123-new-login", pattern), "123")
        self.assertEqual(parse_issue_from_branch("fix/456", pattern), "456")
        self.assertEqual(parse_issue_from_branch("chore/789-setup", pattern), "789")
        self.assertEqual(parse_issue_from_branch("docs/55-readme", pattern), "55")

    def test_parse_invalid_branch(self):
        pattern = r'^(feat|fix|chore|docs|refactor)\/(?P<id>\d+)(-.+)?$'
        self.assertIsNone(parse_issue_from_branch("main", pattern))
        self.assertIsNone(parse_issue_from_branch("dev", pattern))
        # "feature" is not in the default regex group
        self.assertIsNone(parse_issue_from_branch("feature/123-foo", pattern))

if __name__ == "__main__":
    unittest.main()
