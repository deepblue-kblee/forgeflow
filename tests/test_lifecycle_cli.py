import os
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from forgeflow.cli import parse_forgeflow_args, _run_lifecycle_command
from forgeflow.lifecycle import LifecycleError


class LifecycleCliArgsTests(unittest.TestCase):
    def test_package_review_positional_and_flag_args(self):
        # Positional syntax: forgeflow lifecycle package-review <release-id> <qa-sha>
        args1 = parse_forgeflow_args(["lifecycle", "package-review", "v0.1.0-test", "1111111111111111111111111111111111111111"])
        self.assertEqual(args1.release_id, "v0.1.0-test")
        self.assertEqual(args1.qa_sha_pos, "1111111111111111111111111111111111111111")
        self.assertIsNone(args1.qa_sha)

        # Flag syntax: forgeflow lifecycle package-review <release-id> --qa-sha <qa-sha>
        args2 = parse_forgeflow_args(["lifecycle", "package-review", "v0.1.0-test", "--qa-sha", "1111111111111111111111111111111111111111"])
        self.assertEqual(args2.release_id, "v0.1.0-test")
        self.assertEqual(args2.qa_sha, "1111111111111111111111111111111111111111")
        self.assertIsNone(args2.qa_sha_pos)

    def test_seal_positional_and_flag_args(self):
        # Positional syntax: forgeflow lifecycle seal <release-id> <candidate-sha>
        args1 = parse_forgeflow_args(["lifecycle", "seal", "v0.1.0-test", "2222222222222222222222222222222222222222"])
        self.assertEqual(args1.release_id, "v0.1.0-test")
        self.assertEqual(args1.candidate_sha_pos, "2222222222222222222222222222222222222222")
        self.assertIsNone(args1.release_candidate_sha)

        # Flag syntax: forgeflow lifecycle seal <release-id> --release-candidate-sha <candidate-sha>
        args2 = parse_forgeflow_args(["lifecycle", "seal", "v0.1.0-test", "--release-candidate-sha", "2222222222222222222222222222222222222222"])
        self.assertEqual(args2.release_id, "v0.1.0-test")
        self.assertEqual(args2.release_candidate_sha, "2222222222222222222222222222222222222222")
        self.assertIsNone(args2.candidate_sha_pos)

    @patch("forgeflow.cli.HarnessEngine")
    @patch("sys.exit")
    def test_run_lifecycle_command_invocations(self, mock_exit, mock_harness_engine_cls):
        mock_engine = MagicMock()
        mock_engine.lifecycle_package_review.return_value = {"ok": True}
        mock_engine.lifecycle_seal.return_value = {"ok": True}
        mock_harness_engine_cls.return_value = mock_engine

        # Test positional package-review
        parsed1 = parse_forgeflow_args(["lifecycle", "package-review", "v0.1.0-test", "1111111111111111111111111111111111111111"])
        _run_lifecycle_command(parsed1)
        mock_engine.lifecycle_package_review.assert_called_with("v0.1.0-test", "1111111111111111111111111111111111111111")

        # Test flag package-review
        parsed2 = parse_forgeflow_args(["lifecycle", "package-review", "v0.1.0-test", "--qa-sha", "3333333333333333333333333333333333333333"])
        _run_lifecycle_command(parsed2)
        mock_engine.lifecycle_package_review.assert_called_with("v0.1.0-test", "3333333333333333333333333333333333333333")

        # Test positional seal
        parsed3 = parse_forgeflow_args(["lifecycle", "seal", "v0.1.0-test", "2222222222222222222222222222222222222222"])
        _run_lifecycle_command(parsed3)
        mock_engine.lifecycle_seal.assert_called_with("v0.1.0-test", "2222222222222222222222222222222222222222")

        # Test flag seal
        parsed4 = parse_forgeflow_args(["lifecycle", "seal", "v0.1.0-test", "--release-candidate-sha", "4444444444444444444444444444444444444444"])
        _run_lifecycle_command(parsed4)
        mock_engine.lifecycle_seal.assert_called_with("v0.1.0-test", "4444444444444444444444444444444444444444")

    def test_missing_args_raise_lifecycle_error(self):
        parsed = parse_forgeflow_args(["lifecycle", "package-review", "v0.1.0-test"])
        with self.assertRaises(SystemExit) as ctx:
            _run_lifecycle_command(parsed)
        self.assertEqual(ctx.exception.code, 2)


if __name__ == "__main__":
    unittest.main()
