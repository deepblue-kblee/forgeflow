#!/usr/bin/env python3
"""
Unit tests for ForgeFlow First-Class Issue CLI & Tracker Module.
"""

import ast
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import MagicMock, patch

from forgeflow.cli import parse_forgeflow_args
from forgeflow.issue import (
    IssueTracker,
    detect_repo_from_git,
    format_issue_detail,
    format_issue_summary,
    handle_issue_command,
    normalize_issue_args,
)


class TestIssueCLIParsing(unittest.TestCase):
    """Test CLI argument parsing and normalization for 'forgeflow issue'."""

    def test_default_create_shortcut(self):
        """Test 'forgeflow issue --title ... --body ...' shortcut mapping to create."""
        args = ["issue", "--title", "버그 수정 요청", "--body", "상세 설명"]
        parsed = parse_forgeflow_args(args)
        self.assertEqual(parsed.command, "issue")
        self.assertEqual(parsed.issue_command, "create")
        self.assertEqual(parsed.title, "버그 수정 요청")
        self.assertEqual(parsed.body, "상세 설명")
        self.assertIsNone(parsed.body_file)

    def test_create_with_body_file(self):
        """Test 'forgeflow issue create --title ... -F <path>' parsing."""
        args = ["issue", "create", "--title", "기획서", "-F", "docs/spec.md", "--label", "enhancement"]
        parsed = parse_forgeflow_args(args)
        self.assertEqual(parsed.issue_command, "create")
        self.assertEqual(parsed.title, "기획서")
        self.assertEqual(parsed.body_file, Path("docs/spec.md"))
        self.assertEqual(parsed.labels, ["enhancement"])

    def test_subcommands_parsing(self):
        """Test list, view, edit, close, delete subcommands."""
        parsed_list = parse_forgeflow_args(["issue", "list", "--state", "closed", "--refresh"])
        self.assertEqual(parsed_list.issue_command, "list")
        self.assertEqual(parsed_list.state, "closed")
        self.assertTrue(parsed_list.refresh)

        parsed_view = parse_forgeflow_args(["issue", "view", "42"])
        self.assertEqual(parsed_view.issue_command, "view")
        self.assertEqual(parsed_view.number, 42)

        parsed_close = parse_forgeflow_args(["issue", "close", "42", "--comment", "해결 완료"])
        self.assertEqual(parsed_close.issue_command, "close")
        self.assertEqual(parsed_close.number, 42)
        self.assertEqual(parsed_close.comment, "해결 완료")

        parsed_delete = parse_forgeflow_args(["issue", "delete", "42", "--yes"])
        self.assertEqual(parsed_delete.issue_command, "delete")
        self.assertEqual(parsed_delete.number, 42)
        self.assertTrue(parsed_delete.yes)

    def test_normalize_issue_args_helper(self):
        """Directly test normalize_issue_args helper."""
        self.assertEqual(normalize_issue_args([]), ["--help"])
        self.assertEqual(normalize_issue_args(["-h"]), ["-h"])
        self.assertEqual(
            normalize_issue_args(["--title", "T", "--body", "B"]),
            ["create", "--title", "T", "--body", "B"],
        )
        self.assertEqual(
            normalize_issue_args(["create", "--title", "T", "--body", "B"]),
            ["create", "--title", "T", "--body", "B"],
        )
        self.assertEqual(
            normalize_issue_args(["list", "--state", "open"]),
            ["list", "--state", "open"],
        )


class TestIssueTrackerCore(unittest.TestCase):
    """Test IssueTracker business logic and local caching."""

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.cache_dir = Path(self.temp_dir.name)
        self.tracker = IssueTracker(repo="test-owner/test-repo", cache_dir=self.cache_dir)

    def tearDown(self):
        self.temp_dir.cleanup()

    @patch("forgeflow.issue.run_gh_command")
    def test_create_issue_and_cache(self, mock_gh):
        mock_gh.side_effect = [
            # 1st call: gh issue create
            MagicMock(returncode=0, stdout="https://github.com/test-owner/test-repo/issues/10\n", stderr=""),
            # 2nd call: gh issue view 10 (called by view() inside create())
            MagicMock(
                returncode=0,
                stdout=json.dumps({
                    "number": 10,
                    "title": "테스트 이슈",
                    "body": "본문",
                    "state": "OPEN",
                    "labels": [{"name": "bug"}],
                    "url": "https://github.com/test-owner/test-repo/issues/10",
                    "createdAt": "2026-10-06T00:00:00Z",
                    "updatedAt": "2026-10-06T00:00:00Z",
                    "comments": [],
                }),
                stderr="",
            ),
        ]

        issue = self.tracker.create(title="테스트 이슈", body="본문", labels=["bug"])
        self.assertEqual(issue["number"], 10)
        self.assertEqual(issue["state"], "OPEN")
        self.assertEqual(issue["labels"], ["bug"])

        # Check local cache created
        cache_file = self.cache_dir / "10.json"
        self.assertTrue(cache_file.exists())
        with open(cache_file, "r", encoding="utf-8") as f:
            cached = json.load(f)
        self.assertEqual(cached["number"], 10)

    @patch("forgeflow.issue.run_gh_command")
    def test_view_read_through_cache(self, mock_gh):
        cache_file = self.cache_dir / "15.json"
        with open(cache_file, "w", encoding="utf-8") as f:
            json.dump({"number": 15, "title": "캐시된 이슈", "state": "OPEN"}, f)

        # Should read from cache without invoking gh
        issue = self.tracker.view(15, refresh=False)
        self.assertEqual(issue["title"], "캐시된 이슈")
        mock_gh.assert_not_called()

        # With refresh=True, it should call gh
        mock_gh.return_value = MagicMock(
            returncode=0,
            stdout=json.dumps({"number": 15, "title": "새로고침된 이슈", "state": "OPEN", "labels": []}),
            stderr="",
        )
        refreshed = self.tracker.view(15, refresh=True)
        self.assertEqual(refreshed["title"], "새로고침된 이슈")
        self.assertEqual(mock_gh.call_count, 1)

    @patch("forgeflow.issue.run_gh_command")
    def test_close_and_cache(self, mock_gh):
        mock_gh.return_value = MagicMock(returncode=0, stdout="", stderr="")
        cache_file = self.cache_dir / "20.json"
        with open(cache_file, "w", encoding="utf-8") as f:
            json.dump({"number": 20, "title": "종료할 이슈", "state": "OPEN"}, f)

        res = self.tracker.close(20, comment="완료")
        self.assertEqual(res["state"], "CLOSED")
        with open(cache_file, "r", encoding="utf-8") as f:
            cached = json.load(f)
        self.assertEqual(cached["state"], "CLOSED")


class TestIssueCommandExecution(unittest.TestCase):
    """Test handle_issue_command stdout formatting and URL guidance."""

    @patch("forgeflow.issue.IssueTracker.create")
    def test_handle_create_stdout_contains_url_guidance(self, mock_create):
        mock_create.return_value = {
            "number": 99,
            "title": "URL 테스트 이슈",
            "state": "OPEN",
            "labels": ["enhancement"],
            "url": "https://github.com/deepblue-kblee/forgeflow/issues/99",
        }

        parsed = parse_forgeflow_args(["issue", "--title", "URL 테스트 이슈", "--body", "본문"])
        with patch("sys.stdout") as mock_stdout:
            from io import StringIO
            buf = StringIO()
            mock_stdout.write = buf.write
            handle_issue_command(parsed)

        output = buf.getvalue()
        self.assertIn("등록된 issue는 GitHub 사이트에서 확인할 수 있습니다: https://github.com/deepblue-kblee/forgeflow/issues/99", output)
        self.assertIn("#99 (OPEN) [enhancement]: URL 테스트 이슈", output)


class TestZeroDependency(unittest.TestCase):
    """Ensure src/forgeflow/issue.py uses only Python standard library."""

    def test_issue_module_uses_stdlib_only(self):
        issue_file = Path(__file__).resolve().parent.parent / "src" / "forgeflow" / "issue.py"
        self.assertTrue(issue_file.exists())

        tree = ast.parse(issue_file.read_text(encoding="utf-8"), filename=str(issue_file))
        imported_modules = set()

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imported_modules.add(alias.name.split(".")[0])
            elif isinstance(node, ast.ImportFrom):
                if node.module and not node.module.startswith("."):
                    imported_modules.add(node.module.split(".")[0])

        stdlib_allowlist = {
            "__future__",
            "argparse",
            "json",
            "os",
            "pathlib",
            "re",
            "subprocess",
            "sys",
            "typing",
        }

        for mod in imported_modules:
            self.assertIn(
                mod,
                stdlib_allowlist,
                f"Unauthorized external dependency '{mod}' found in issue.py",
            )


if __name__ == "__main__":
    unittest.main()
