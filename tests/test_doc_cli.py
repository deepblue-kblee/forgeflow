"""
Unit tests for forgeflow doc / spec CLI command
"""

import io
import json
import shutil
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

from forgeflow.cli import main, handle_doc, parse_forgeflow_args, resolve_spec_directory, OFFICIAL_SPECS


class TestDocCli(unittest.TestCase):
    def setUp(self):
        self.temp_dir = Path(tempfile.mkdtemp())

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_resolve_spec_directory(self):
        spec_dir = resolve_spec_directory()
        self.assertIsNotNone(spec_dir)
        self.assertTrue((spec_dir / "FLOW_SPEC.md").is_file())

    def test_doc_list_text_output(self):
        stdout = io.StringIO()
        stderr = io.StringIO()
        args = parse_forgeflow_args(["doc", "--list"])
        with redirect_stdout(stdout), redirect_stderr(stderr):
            code = handle_doc(args)
        self.assertEqual(code, 0)
        output = stdout.getvalue()
        self.assertIn("FLOW_SPEC", output)
        self.assertIn("GATES_AND_LOOPS", output)
        self.assertIn("SPECKIT_HOOKS_AND_NORMS", output)
        self.assertIn("DISTRIBUTION_SPEC", output)
        self.assertIn("PHILOSOPHY_AND_COMPASS", output)
        self.assertIn("REFACTORING_GUIDE", output)
        self.assertIn("CHANGELOG", output)

    def test_doc_list_json_output(self):
        stdout = io.StringIO()
        args = parse_forgeflow_args(["doc", "--list", "--json"])
        with redirect_stdout(stdout):
            code = handle_doc(args)
        self.assertEqual(code, 0)
        data = json.loads(stdout.getvalue())
        self.assertEqual(data["status"], "success")
        self.assertEqual(data["count"], 7)
        ids = [s["id"] for s in data["specifications"]]
        self.assertIn("FLOW_SPEC", ids)
        self.assertIn("SPECKIT_HOOKS_AND_NORMS", ids)

    def test_doc_show_single_spec(self):
        stdout = io.StringIO()
        args = parse_forgeflow_args(["doc", "FLOW_SPEC"])
        with redirect_stdout(stdout):
            code = handle_doc(args)
        self.assertEqual(code, 0)
        output = stdout.getvalue()
        self.assertIn("FLOW_SPEC", output)
        self.assertIn("ForgeFlow-SpecKit 하이브리드 워크플로우", output)

    def test_doc_show_case_insensitive_and_extension(self):
        stdout = io.StringIO()
        args = parse_forgeflow_args(["doc", "gates_and_loops.md"])
        with redirect_stdout(stdout):
            code = handle_doc(args)
        self.assertEqual(code, 0)
        output = stdout.getvalue()
        self.assertIn("GATES_AND_LOOPS", output)

    def test_doc_show_json(self):
        stdout = io.StringIO()
        args = parse_forgeflow_args(["doc", "SPECKIT_HOOKS_AND_NORMS", "--json"])
        with redirect_stdout(stdout):
            code = handle_doc(args)
        self.assertEqual(code, 0)
        data = json.loads(stdout.getvalue())
        self.assertEqual(data["status"], "success")
        self.assertEqual(data["id"], "SPECKIT_HOOKS_AND_NORMS")
        self.assertIn("GitHub Spec Kit 주입 규범", data["content"])

    def test_doc_show_subcommand_syntax(self):
        stdout = io.StringIO()
        args = parse_forgeflow_args(["doc", "show", "DISTRIBUTION_SPEC"])
        with redirect_stdout(stdout):
            code = handle_doc(args)
        self.assertEqual(code, 0)
        output = stdout.getvalue()
        self.assertIn("DISTRIBUTION_SPEC", output)

    def test_doc_not_found(self):
        stdout = io.StringIO()
        stderr = io.StringIO()
        args = parse_forgeflow_args(["doc", "NON_EXISTENT_SPEC"])
        with redirect_stdout(stdout), redirect_stderr(stderr):
            code = handle_doc(args)
        self.assertEqual(code, 1)
        self.assertIn("not found", stderr.getvalue())

    def test_doc_not_found_json(self):
        stdout = io.StringIO()
        args = parse_forgeflow_args(["doc", "NON_EXISTENT_SPEC", "--json"])
        with redirect_stdout(stdout):
            code = handle_doc(args)
        self.assertEqual(code, 1)
        data = json.loads(stdout.getvalue())
        self.assertEqual(data["status"], "error")
        self.assertIn("available", data)

    def test_spec_alias_command(self):
        stdout = io.StringIO()
        args = parse_forgeflow_args(["spec", "list"])
        with redirect_stdout(stdout):
            code = handle_doc(args)
        self.assertEqual(code, 0)
        self.assertIn("FLOW_SPEC", stdout.getvalue())

    def test_custom_path_resolution(self):
        custom_spec_dir = self.temp_dir / "custom" / "spec"
        custom_spec_dir.mkdir(parents=True)
        (custom_spec_dir / "FLOW_SPEC.md").write_text("# Custom Flow Spec\n", encoding="utf-8")

        stdout = io.StringIO()
        args = parse_forgeflow_args(["doc", "FLOW_SPEC", "--path", str(custom_spec_dir)])
        with redirect_stdout(stdout):
            code = handle_doc(args)
        self.assertEqual(code, 0)
        self.assertIn("Custom Flow Spec", stdout.getvalue())
