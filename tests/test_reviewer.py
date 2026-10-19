#!/usr/bin/env python3
import json
import tempfile
import unittest
from pathlib import Path

from forgeflow.renderer import ReportRenderer
from forgeflow.review_scanner import ReviewScanner
from forgeflow.reviewer import ReviewEngine, ReviewResult
from forgeflow.smell_detector import CodeSmell, SmellDetector


class TestSmellDetector(unittest.TestCase):
    def test_clean_code_has_no_critical_smells(self):
        clean_code = "def calculate_total(price: float, tax_rate: float) -> float:\n    return price * (1.0 + tax_rate)\n"
        smells = SmellDetector.analyze_code(clean_code)
        critical = [s for s in smells if s.severity == "CRITICAL"]
        self.assertEqual(len(critical), 0)

    def test_bare_except_detection(self):
        bad_code = "def unsafe_operation():\n    try:\n        do_something()\n    except:\n        pass\n"
        smells = SmellDetector.analyze_code(bad_code)
        critical = [s for s in smells if s.severity == "CRITICAL" and s.smell_type == "Bare Except"]
        self.assertEqual(len(critical), 1)

    def test_base_exception_detection(self):
        bad_code = "def catch_all():\n    try:\n        pass\n    except BaseException:\n        pass\n"
        smells = SmellDetector.analyze_code(bad_code)
        critical = [s for s in smells if s.severity == "CRITICAL" and s.smell_type == "Bare Except"]
        self.assertEqual(len(critical), 1)

    def test_too_many_parameters_detection(self):
        code = "def many_args(a: int, b: int, c: int, d: int, e: int, f: int) -> int:\n    return a + b + c + d + e + f\n"
        smells = SmellDetector.analyze_code(code)
        warnings = [s for s in smells if s.smell_type == "Too Many Parameters"]
        self.assertEqual(len(warnings), 1)

    def test_deep_nesting_detection(self):
        code = "def nested(x: int) -> int:\n    if x > 0:\n        if x > 1:\n            if x > 2:\n                if x > 3:\n                    return x\n    return 0\n"
        smells = SmellDetector.analyze_code(code)
        nesting = [s for s in smells if s.smell_type == "Deep Nesting"]
        self.assertEqual(len(nesting), 1)

    def test_long_function_detection(self):
        lines = ["def long_func() -> None:"]
        for i in range(60):
            lines.append(f"    x_{i} = {i}")
        code = "\n".join(lines)
        smells = SmellDetector.analyze_code(code)
        long_funcs = [s for s in smells if s.smell_type == "Long Function"]
        self.assertEqual(len(long_funcs), 1)

    def test_missing_type_annotations(self):
        code = "def untyped_func(foo, bar):\n    return foo + bar\n"
        smells = SmellDetector.analyze_code(code)
        types = [s for s in smells if s.smell_type == "Missing Type Annotations"]
        self.assertEqual(len(types), 1)

    def test_top_level_side_effect_detection(self):
        bad_code = "import logging\nimport sqlite3\nlogging.basicConfig(level=logging.INFO)\nconn = sqlite3.connect('test.db')\n"
        smells = SmellDetector.analyze_code(bad_code)
        side_effects = [s for s in smells if s.smell_type == "Top-level Side-Effect"]
        self.assertEqual(len(side_effects), 2)
        self.assertEqual(side_effects[0].severity, "CRITICAL")

    def test_unmanaged_resource_detection(self):
        bad_code = "def read_file(path: str) -> str:\n    f = open(path)\n    return f.read()\n"
        smells = SmellDetector.analyze_code(bad_code)
        unmanaged = [s for s in smells if s.smell_type == "Unmanaged Resource"]
        self.assertEqual(len(unmanaged), 1)

    def test_main_block_and_with_context_allowed(self):
        good_code = "def read_file_safe(path: str) -> str:\n    with open(path) as f:\n        return f.read()\n\nif __name__ == '__main__':\n    import sqlite3\n    conn = sqlite3.connect('main.db')\n"
        smells = SmellDetector.analyze_code(good_code)
        critical_or_unmanaged = [s for s in smells if s.smell_type in ("Top-level Side-Effect", "Unmanaged Resource")]
        self.assertEqual(len(critical_or_unmanaged), 0)


class TestReviewScanner(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)
        (self.root / "src").mkdir()
        (self.root / "src" / "sample.py").write_text("print('hello')\n")
        (self.root / "PRD.md").write_text("# PRD\nREQ-F01: Sample\n")

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_get_all_source_files(self):
        files = ReviewScanner.get_all_source_files(self.root)
        self.assertEqual(len(files), 1)
        self.assertEqual(files[0].name, "sample.py")

    def test_find_spec_source(self):
        spec = ReviewScanner.find_spec_source(self.root)
        self.assertIsNotNone(spec)
        self.assertEqual(spec.name, "PRD.md")


class TestReviewEngine(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)
        (self.root / "src").mkdir()
        (self.root / "src" / "good.py").write_text("def add(a: int, b: int) -> int:\n    return a + b\n")
        (self.root / "src" / "bad.py").write_text("def bad():\n    try:\n        pass\n    except:\n        pass\n")
        (self.root / "PRD.md").write_text("# PRD\nREQ-F01: Review\n")

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_run_review_detects_bad_code(self):
        engine = ReviewEngine(repo_root=self.root)
        res = engine.run_review(all_files=True)
        self.assertFalse(res.passed)
        self.assertTrue(any(s.severity == "CRITICAL" for s in res.smells))

    def test_run_review_good_code_only(self):
        engine = ReviewEngine(repo_root=self.root)
        good_file = self.root / "src" / "good.py"
        res = engine.run_review(targets=[good_file], strict=False)
        self.assertTrue(res.passed)
        self.assertIsNotNone(res.report_path)

    def test_render_terminal_and_json(self):
        engine = ReviewEngine(repo_root=self.root)
        res = engine.run_review(all_files=True)
        terminal_out = ReportRenderer.render_terminal_review(res)
        json_out = ReportRenderer.render_json_review(res)
        self.assertIn("Code Review & Architecture Audit Report", terminal_out)
        parsed = json.loads(json_out)
        self.assertEqual(parsed["summary"]["total_files"], 2)

    def test_render_terminal_includes_refactoring_guidance(self):
        engine = ReviewEngine(repo_root=self.root)
        nested_file = self.root / "src" / "nested.py"
        nested_file.write_text("def nested(x):\n    if x > 0:\n        if x > 1:\n            if x > 2:\n                if x > 3:\n                    return x\n    return 0\n")
        res = engine.run_review(targets=[nested_file], strict=False)
        terminal_out = ReportRenderer.render_terminal_review(res)
        self.assertIn("Deep Module & Clean Code 리팩토링 권장 사항", terminal_out)
    def test_run_review_clean_tree_bailout(self):
        engine = ReviewEngine(repo_root=self.root)
        from unittest.mock import patch
        with patch.object(ReviewScanner, "get_diff_files", return_value=[]):
            res = engine.run_review(all_files=False)
            self.assertTrue(res.passed)
            self.assertEqual(res.smells, [])
            self.assertEqual(res.files_scanned, [])

    def test_security_vulnerability_causes_review_failure(self):
        engine = ReviewEngine(repo_root=self.root)
        sec_file = self.root / "src" / "vuln.py"
        sec_file.write_text("import subprocess\nsubprocess.run('echo hi', shell=True)\n", encoding="utf-8")
        res = engine.run_review(targets=[sec_file], strict=False)
        self.assertFalse(res.passed)
        self.assertTrue(any(s.smell_type == "Security Vulnerability" for s in res.smells))

    def test_fail_on_warning_causes_review_failure(self):
        engine = ReviewEngine(repo_root=self.root)
        warn_file = self.root / "src" / "warn.py"
        warn_file.write_text("def silent():\n    try:\n        pass\n    except ValueError:\n        pass\n", encoding="utf-8")
        # normal review without strict or fail_on_warning should pass
        res_normal = engine.run_review(targets=[warn_file], strict=False, fail_on_warning=False)
        self.assertTrue(res_normal.passed)

        # with fail_on_warning
        res_fail = engine.run_review(targets=[warn_file], fail_on_warning=True)
        self.assertFalse(res_fail.passed)


if __name__ == "__main__":
    unittest.main()