#!/usr/bin/env python3
"""
Unit tests for multi-axis quality metrics and AST security pattern rules in SmellDetector.
"""

import unittest

from forgeflow.smell_detector import SmellDetector


class TestSmellDetectorMultiAxisRules(unittest.TestCase):
    def test_io_in_loop_detection(self):
        bad_code = """
def process_items(items):
    for item in items:
        with open(f"{item}.txt", "w") as f:
            f.write("data")
"""
        smells = SmellDetector.analyze_code(bad_code)
        loop_io = [s for s in smells if s.smell_type == "I/O in Loop"]
        self.assertGreaterEqual(len(loop_io), 1)
        self.assertEqual(loop_io[0].severity, "WARNING")
        self.assertIn("루프 내부", loop_io[0].message)

    def test_io_outside_loop_allowed(self):
        good_code = """
def process_items(items):
    with open("items.txt", "w") as f:
        f.write("data")
    for item in items:
        pass
"""
        smells = SmellDetector.analyze_code(good_code)
        loop_io = [s for s in smells if s.smell_type == "I/O in Loop"]
        self.assertEqual(len(loop_io), 0)

    def test_excessive_imports_detection(self):
        # 21 unique imported module names
        imports = [f"import mod_{i}" for i in range(22)]
        code = "\n".join(imports) + "\ndef foo(): pass\n"
        smells = SmellDetector.analyze_code(code)
        excessive = [s for s in smells if s.smell_type == "Excessive Imports"]
        self.assertGreaterEqual(len(excessive), 1)
        self.assertEqual(excessive[0].severity, "WARNING")

    def test_unused_import_detection(self):
        code = """
import os
import sys
from math import sqrt, sin

def compute(x: float) -> float:
    return sqrt(x)
"""
        smells = SmellDetector.analyze_code(code)
        unused = [s for s in smells if s.smell_type == "Unused Import"]
        unused_names = [s.message for s in unused]
        # os, sys, sin are unused; sqrt is used
        self.assertTrue(any("os" in msg for msg in unused_names))
        self.assertTrue(any("sys" in msg for msg in unused_names))
        self.assertTrue(any("sin" in msg for msg in unused_names))
        self.assertFalse(any("sqrt" in msg for msg in unused_names))

    def test_unused_import_allowed_with_all_export(self):
        code = """
from submodule import PublicAPI, Helper

__all__ = ["PublicAPI"]

def internal():
    pass
"""
        smells = SmellDetector.analyze_code(code)
        unused = [s for s in smells if s.smell_type == "Unused Import"]
        unused_names = [s.message for s in unused]
        self.assertFalse(any("PublicAPI" in msg for msg in unused_names))
        self.assertTrue(any("Helper" in msg for msg in unused_names))

    def test_silent_exception_detection(self):
        code = """
def test_silent():
    try:
        do_something()
    except ValueError:
        pass
"""
        smells = SmellDetector.analyze_code(code)
        silent = [s for s in smells if s.smell_type == "Silent Exception"]
        self.assertEqual(len(silent), 1)
        self.assertEqual(silent[0].severity, "WARNING")

    def test_silent_exception_with_ellipsis(self):
        code = """
def test_ellipsis():
    try:
        do_something()
    except KeyError:
        ...
"""
        smells = SmellDetector.analyze_code(code)
        silent = [s for s in smells if s.smell_type == "Silent Exception"]
        self.assertEqual(len(silent), 1)

    def test_handled_exception_not_reported_as_silent(self):
        code = """
import logging

def test_handled():
    try:
        do_something()
    except KeyError as exc:
        logging.warning("Error: %s", exc)
"""
        smells = SmellDetector.analyze_code(code)
        silent = [s for s in smells if s.smell_type == "Silent Exception"]
        self.assertEqual(len(silent), 0)

    def test_security_vulnerability_subprocess_shell_true(self):
        code = """
import subprocess

def run_cmd(user_input: str):
    subprocess.run(f"echo {user_input}", shell=True)
"""
        smells = SmellDetector.analyze_code(code)
        sec = [s for s in smells if s.smell_type == "Security Vulnerability"]
        self.assertEqual(len(sec), 1)
        self.assertEqual(sec[0].severity, "CRITICAL")
        self.assertIn("shell=True", sec[0].message)

    def test_security_vulnerability_eval_and_exec(self):
        code = """
def dynamic_exec(code_str: str):
    eval(code_str)
    exec(code_str)
"""
        smells = SmellDetector.analyze_code(code)
        sec = [s for s in smells if s.smell_type == "Security Vulnerability"]
        self.assertEqual(len(sec), 2)
        for s in sec:
            self.assertEqual(s.severity, "CRITICAL")

    def test_security_vulnerability_tempfile_mktemp(self):
        code = """
import tempfile

def create_temp():
    return tempfile.mktemp()
"""
        smells = SmellDetector.analyze_code(code)
        sec = [s for s in smells if s.smell_type == "Security Vulnerability"]
        self.assertEqual(len(sec), 1)
        self.assertEqual(sec[0].severity, "CRITICAL")
        self.assertIn("mktemp", sec[0].message)

    def test_builtin_shadowing_parameter(self):
        code = """
def get_item(id: int, type: str) -> None:
    pass
"""
        smells = SmellDetector.analyze_code(code)
        shadowing = [s for s in smells if s.smell_type == "Builtin Shadowing"]
        self.assertEqual(len(shadowing), 2)
        params = [s.message for s in shadowing]
        self.assertTrue(any("id" in p for p in params))
        self.assertTrue(any("type" in p for p in params))

    def test_builtin_shadowing_local_variable(self):
        code = """
def calculate():
    sum = 100
    format = "json"
    return sum
"""
        smells = SmellDetector.analyze_code(code)
        shadowing = [s for s in smells if s.smell_type == "Builtin Shadowing"]
        self.assertEqual(len(shadowing), 2)


if __name__ == "__main__":
    unittest.main()
