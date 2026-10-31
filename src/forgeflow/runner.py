"""
Generalized Target Test Runner with Multi-tiered Virtualenv Discovery
"""

import json
import math
import os
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, Optional


class RuntimeTestRunner:
    """Discovers python executable and runs unit/regression test suites."""

    DEFAULT_TEST_TIMEOUT: float = 60.0

    @staticmethod
    def resolve_test_timeout(repo_root: Path) -> float:
        modern_cfg = repo_root / ".forgeflow" / "config.json"
        legacy_cfg = repo_root / ".forgeflow.json"
        config_path = modern_cfg if modern_cfg.exists() else legacy_cfg
        if not config_path.exists() or not config_path.is_file():
            return RuntimeTestRunner.DEFAULT_TEST_TIMEOUT

        config_name = ".forgeflow/config.json" if config_path == modern_cfg else ".forgeflow.json"

        try:
            data = json.loads(config_path.read_text(encoding="utf-8"))
        except Exception as e:
            raise ValueError(f"Failed to parse {config_name}: {e}") from e

        if not isinstance(data, dict):
            return RuntimeTestRunner.DEFAULT_TEST_TIMEOUT

        governance = data.get("governance")
        if not isinstance(governance, dict) or "test_timeout_seconds" not in governance:
            return RuntimeTestRunner.DEFAULT_TEST_TIMEOUT

        raw_val = governance["test_timeout_seconds"]

        if isinstance(raw_val, bool):
            raise ValueError(
                f"Invalid test_timeout_seconds in {config_name}: expected positive number, got bool ({raw_val})"
            )

        if not isinstance(raw_val, (int, float)):
            raise ValueError(
                f"Invalid test_timeout_seconds in {config_name}: expected positive number, got {type(raw_val).__name__} ({raw_val!r})"
            )

        if not math.isfinite(raw_val):
            raise ValueError(
                f"Invalid test_timeout_seconds in {config_name}: expected finite number, got {raw_val}"
            )

        if raw_val <= 0:
            raise ValueError(
                f"Invalid test_timeout_seconds in {config_name}: expected positive number > 0, got {raw_val}"
            )

        return float(raw_val)

    @staticmethod
    def resolve_python_interpreter(repo_root: Path, explicit_python: Optional[str] = None) -> str:
        # 1. Explicit CLI argument
        if explicit_python and Path(explicit_python).exists():
            return explicit_python

        # 2. Environment variable FORGEFLOW_PYTHON
        env_py = os.environ.get("FORGEFLOW_PYTHON")
        if env_py and Path(env_py).exists():
            return env_py

        # 3. Target project virtualenvs (.venv, venv)
        venv_candidates = [
            repo_root / ".venv" / "bin" / "python",
            repo_root / "venv" / "bin" / "python",
            repo_root / ".venv" / "bin" / "python3",
            repo_root / "venv" / "bin" / "python3",
        ]
        for c in venv_candidates:
            if c.exists() and os.access(c, os.X_OK):
                return str(c)

        # 4. Caller shell VIRTUAL_ENV
        shell_venv = os.environ.get("VIRTUAL_ENV")
        if shell_venv:
            candidate = Path(shell_venv) / "bin" / "python"
            if candidate.exists() and os.access(candidate, os.X_OK):
                return str(candidate)

        # 5. Fallback to current sys.executable
        return sys.executable

    @staticmethod
    def run_tests(
        repo_root: Path,
        explicit_python: Optional[str] = None,
        test_dir: Optional[str] = None,
        timeout: Optional[float] = None,
    ) -> Dict[str, Any]:
        effective_timeout = (
            timeout if timeout is not None else RuntimeTestRunner.resolve_test_timeout(repo_root)
        )
        python_bin = RuntimeTestRunner.resolve_python_interpreter(repo_root, explicit_python)
        target_tests_dir = repo_root / (test_dir or "tests")

        if not target_tests_dir.exists():
            return {
                "executed": False,
                "passed": True,
                "output": "No tests directory found in target project.",
                "total": 0,
                "failures": 0,
                "errors": 0,
            }

        cmd = [python_bin, "-m", "unittest", "discover", "-s", str(target_tests_dir)]
        try:
            env = os.environ.copy()
            source_root = repo_root / "src"
            if source_root.is_dir():
                existing = env.get("PYTHONPATH", "")
                env["PYTHONPATH"] = str(source_root) if not existing else str(source_root) + os.pathsep + existing
            res = subprocess.run(
                cmd,
                cwd=str(repo_root),
                capture_output=True,
                text=True,
                env=env,
                timeout=effective_timeout,
                check=False,
            )
            raw_output = res.stderr + "\n" + res.stdout
            passed = res.returncode == 0

            return {
                "executed": True,
                "passed": passed,
                "returncode": res.returncode,
                "output": raw_output.strip(),
                "python_used": python_bin,
            }
        except subprocess.TimeoutExpired:
            return {
                "executed": True,
                "passed": False,
                "returncode": -1,
                "output": f"Tests timed out after {effective_timeout} seconds.",
                "python_used": python_bin,
            }
        except Exception as e:
            return {
                "executed": True,
                "passed": False,
                "returncode": -1,
                "output": f"Failed to execute tests: {e}",
                "python_used": python_bin,
            }
