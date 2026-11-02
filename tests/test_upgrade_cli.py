import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from forgeflow._version import __version__
from forgeflow.cli import parse_version_tuple, handle_upgrade, parse_forgeflow_args


def _response(payload: bytes) -> MagicMock:
    response = MagicMock()
    response.read.return_value = payload
    response.__enter__.return_value = response
    return response


def _target(root: Path) -> dict:
    return {
        "prefix": str(root / "prefix"),
        "bin_dir": str(root / "bin"),
        "skills_dir": str(root / "skills"),
    }


class TestUpgradeCLI(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        resolver = patch("forgeflow.distribution.resolve_revision", return_value="a" * 40)
        resolver.start()
        self.addCleanup(resolver.stop)

    def tearDown(self):
        self.temp.cleanup()

    def test_with_revision_pins_fetch_and_clone_source(self):
        from forgeflow.cli import _with_revision
        from forgeflow.distribution import derive_clone_url
        base, ref = _with_revision("https://raw.githubusercontent.com/o/r/main", "deadbeef")
        self.assertEqual(ref, "deadbeef")
        self.assertEqual(base, "https://raw.githubusercontent.com/o/r/deadbeef")
        self.assertEqual(derive_clone_url(base), "https://github.com/o/r")

    def test_custom_prefix_is_derived_from_installed_package_path(self):
        from forgeflow.distribution import resolve_installation_target
        prefix = self.root / "custom-prefix"
        package = prefix / "packages" / "0.1.26-abcdef" / "lib" / "forgeflow" / "distribution.py"
        package.parent.mkdir(parents=True)
        (prefix / "current").mkdir()
        (prefix / "current" / "package.json").write_text(json.dumps({
            "version": __version__,
            "bin_dir": str(self.root / "custom-bin"),
            "skills_dir": str(self.root / "custom-skills"),
        }), encoding="utf-8")
        with patch("forgeflow.distribution.__file__", str(package)), \
             patch.dict("os.environ", {}, clear=True):
            target = resolve_installation_target()
        self.assertEqual(target["prefix"], str(prefix.resolve()))
        self.assertEqual(target["bin_dir"], str((self.root / "custom-bin").absolute()))
        self.assertEqual(target["skills_dir"], str((self.root / "custom-skills").absolute()))

    def test_parse_version_tuple(self):
        self.assertEqual(parse_version_tuple("0.1.2"), (0, 1, 2))
        self.assertEqual(parse_version_tuple("v0.1.3"), (0, 1, 3))
        self.assertEqual(parse_version_tuple("1.0"), (1, 0))
        self.assertTrue(parse_version_tuple("0.1.3") > parse_version_tuple("0.1.2"))
        self.assertTrue(parse_version_tuple("0.2.0") > parse_version_tuple("0.1.9"))

    @patch("urllib.request.urlopen")
    def test_upgrade_check_up_to_date(self, mock_urlopen):
        mock_urlopen.side_effect = [
            _response(f'__version__ = "{__version__}"'.encode("utf-8")),
            _response(b"#!/usr/bin/env bash\n# forgeflow installer\nexit 0\n"),
        ]
        args = parse_forgeflow_args(["upgrade", "--check", "--json"])
        with patch("forgeflow.distribution.resolve_installation_target", return_value=_target(self.root)), \
             patch("forgeflow.distribution.read_package_metadata", return_value={}):
            with patch("builtins.print") as mock_print:
                code = handle_upgrade(args)
                self.assertEqual(code, 0)
                output = json.loads(mock_print.call_args[0][0])
                self.assertEqual(output["status"], "success")
                self.assertTrue(output["upgrade_available"])
                self.assertEqual(output["identity_comparison"], "not-installed")
                self.assertFalse(output["installed"])

    @patch("urllib.request.urlopen")
    def test_upgrade_check_upgrade_available(self, mock_urlopen):
        mock_urlopen.side_effect = [
            _response(b'__version__ = "99.9.9"'),
            _response(b"#!/usr/bin/env bash\n# forgeflow installer\nexit 0\n"),
        ]
        args = parse_forgeflow_args(["upgrade", "--check", "--json"])
        with patch("forgeflow.distribution.resolve_installation_target", return_value=_target(self.root)), \
             patch("forgeflow.distribution.read_package_metadata", return_value={}):
            with patch("builtins.print") as mock_print:
                code = handle_upgrade(args)
                self.assertEqual(code, 0)
                output = json.loads(mock_print.call_args[0][0])
                self.assertTrue(output["upgrade_available"])
                self.assertEqual(output["remote_version"], "99.9.9")
                self.assertIn("source_identity", output)
                self.assertIn("source_revision", output)

    @patch("urllib.request.urlopen")
    def test_upgrade_already_up_to_date_skips_install(self, mock_urlopen):
        mock_urlopen.side_effect = [
            _response(f'__version__ = "{__version__}"'.encode("utf-8")),
            _response(b"#!/usr/bin/env bash\n# forgeflow installer\nexit 0\n"),
        ]
        args = parse_forgeflow_args(["upgrade", "--json"])
        with patch("forgeflow.distribution.resolve_installation_target", return_value=_target(self.root)), \
             patch("forgeflow.distribution.read_package_metadata", return_value={"version": __version__}), \
             patch("subprocess.run") as mock_subproc, patch("builtins.print") as mock_print:
            code = handle_upgrade(args)
            self.assertEqual(code, 0)
            mock_subproc.assert_not_called()
            output = json.loads(mock_print.call_args[0][0])
            self.assertFalse(output["upgraded"])

    @patch("urllib.request.urlopen")
    def test_upgrade_noop_installer_is_not_reported_as_success(self, mock_urlopen):
        mock_urlopen.side_effect = [
            _response(b'__version__ = "99.0.0"'),
            _response(b"#!/usr/bin/env bash\n# forgeflow installer\nexit 0\n"),
        ]
        args = parse_forgeflow_args(["upgrade", "--force", "--json"])
        with patch("forgeflow.distribution.resolve_installation_target", return_value=_target(self.root)), \
             patch("forgeflow.distribution.read_package_metadata", return_value={}), \
             patch("subprocess.run", return_value=MagicMock(returncode=0, stderr="")), \
             patch("builtins.print") as mock_print:
            code = handle_upgrade(args)
            self.assertEqual(code, 1)
            output = json.loads(mock_print.call_args[0][0])
            self.assertEqual(output["status"], "error")
            self.assertFalse(output["upgraded"])
            self.assertTrue(output["errors"])

    @patch("urllib.request.urlopen")
    def test_upgrade_wrong_installed_version_is_not_success(self, mock_urlopen):
        mock_urlopen.side_effect = [
            _response(b'__version__ = "99.0.0"'),
            _response(b"#!/usr/bin/env bash\n# forgeflow installer\nexit 0\n"),
        ]
        args = parse_forgeflow_args(["upgrade", "--force", "--json"])
        with patch("forgeflow.distribution.resolve_installation_target", return_value=_target(self.root)), \
             patch("forgeflow.distribution.read_package_metadata", return_value={}), \
             patch("subprocess.run", return_value=MagicMock(returncode=0, stderr="")), \
             patch("forgeflow.distribution.verify_installed_distribution", return_value={
                 "ok": False,
                 "errors": ["Installed package version '1.0.0' does not match expected '99.0.0'."],
                 "observed": {},
                 "target": _target(self.root),
             }), \
             patch("builtins.print") as mock_print:
            code = handle_upgrade(args)
            self.assertEqual(code, 1)
            output = json.loads(mock_print.call_args[0][0])
            self.assertFalse(output["upgraded"])

    @patch("urllib.request.urlopen")
    def test_same_version_different_build_is_detected(self, mock_urlopen):
        mock_urlopen.side_effect = [
            _response(f'__version__ = "{__version__}"'.encode("utf-8")),
            _response(b"#!/usr/bin/env bash\n# forgeflow installer\nexit 0\n"),
        ]
        args = parse_forgeflow_args(["upgrade", "--check", "--json"])
        with patch("forgeflow.distribution.resolve_installation_target", return_value=_target(self.root)), \
             patch("forgeflow.distribution.read_package_metadata", return_value={
                 "version": __version__, "source_identity": "different-build",
             }):
            with patch("builtins.print") as mock_print:
                code = handle_upgrade(args)
                self.assertEqual(code, 0)
                output = json.loads(mock_print.call_args[0][0])
                self.assertTrue(output["upgrade_available"])
                self.assertEqual(output["reason"], "same-version-different-build")

    @patch("urllib.request.urlopen")
    def test_upgrade_without_installation_is_not_success(self, mock_urlopen):
        mock_urlopen.side_effect = [
            _response(b'__version__ = "99.0.0"'),
            _response(b"#!/usr/bin/env bash\n# forgeflow installer\nexit 0\n"),
        ]
        args = parse_forgeflow_args(["upgrade", "--json"])
        with patch("forgeflow.distribution.resolve_installation_target", return_value=_target(self.root)), \
             patch("forgeflow.distribution.read_package_metadata", return_value={}), \
             patch("subprocess.run") as mock_subproc, \
             patch("builtins.print") as mock_print:
            code = handle_upgrade(args)
            self.assertEqual(code, 1)
            mock_subproc.assert_not_called()
            output = json.loads(mock_print.call_args[0][0])
            self.assertEqual(output["status"], "error")
            self.assertFalse(output["upgraded"])
            self.assertFalse(output["installed"])

    @patch("urllib.request.urlopen")
    def test_upgrade_installer_failure_returns_nonzero(self, mock_urlopen):
        mock_urlopen.side_effect = [
            _response(b'__version__ = "99.0.0"'),
            _response(b"#!/usr/bin/env bash\n# forgeflow installer\nexit 0\n"),
        ]
        args = parse_forgeflow_args(["upgrade", "--force", "--json"])
        with patch("forgeflow.distribution.resolve_installation_target", return_value=_target(self.root)), \
             patch("forgeflow.distribution.read_package_metadata", return_value={}), \
             patch("subprocess.run", return_value=MagicMock(returncode=3, stderr="boom")), \
             patch("builtins.print") as mock_print:
            code = handle_upgrade(args)
            self.assertEqual(code, 3)
            output = json.loads(mock_print.call_args[0][0])
            self.assertEqual(output["status"], "error")
            self.assertFalse(output["upgraded"])

    @patch("urllib.request.urlopen")
    def test_upgrade_network_error(self, mock_urlopen):
        mock_urlopen.side_effect = Exception("Connection timed out")
        args = parse_forgeflow_args(["upgrade", "--json"])
        with patch("builtins.print") as mock_print:
            code = handle_upgrade(args)
            self.assertEqual(code, 1)
            output = json.loads(mock_print.call_args[0][0])
            self.assertEqual(output["status"], "error")

    @patch("builtins.input")
    @patch("urllib.request.urlopen")
    def test_upgrade_interactive_prompt_yes(self, mock_urlopen, mock_input):
        mock_input.return_value = "y"
        mock_urlopen.side_effect = [
            _response(b'__version__ = "99.0.0"'),
            _response(b"#!/usr/bin/env bash\n# forgeflow installer\nexit 0\n"),
        ]
        args = parse_forgeflow_args(["upgrade"])
        with patch("forgeflow.distribution.resolve_installation_target", return_value=_target(self.root)), \
             patch("forgeflow.distribution.read_package_metadata", return_value={"version": "0.1.0"}), \
             patch("subprocess.run", return_value=MagicMock(returncode=0, stderr="")), \
             patch("forgeflow.distribution.verify_installed_distribution", return_value={
                 "ok": True, "errors": [], "observed": {}, "target": _target(self.root),
             }), \
             patch("builtins.print"):
            code = handle_upgrade(args)
            self.assertEqual(code, 0)
            mock_input.assert_called_once()
            self.assertIn("upgrade to v99.0.0", mock_input.call_args[0][0])

    @patch("builtins.input")
    @patch("urllib.request.urlopen")
    def test_upgrade_interactive_prompt_no_cancels(self, mock_urlopen, mock_input):
        mock_input.return_value = "n"
        mock_urlopen.side_effect = [
            _response(b'__version__ = "99.0.0"'),
            _response(b"#!/usr/bin/env bash\n# forgeflow installer\nexit 0\n"),
        ]
        args = parse_forgeflow_args(["upgrade"])
        with patch("forgeflow.distribution.resolve_installation_target", return_value=_target(self.root)), \
             patch("forgeflow.distribution.read_package_metadata", return_value={"version": __version__}), \
             patch("subprocess.run") as mock_subproc, patch("builtins.print") as mock_print:
            code = handle_upgrade(args)
            self.assertEqual(code, 0)
            mock_input.assert_called_once()
            mock_subproc.assert_not_called()
            mock_print.assert_any_call("Upgrade cancelled.")

    @patch("builtins.input")
    @patch("urllib.request.urlopen")
    def test_upgrade_force_skips_prompt(self, mock_urlopen, mock_input):
        mock_urlopen.side_effect = [
            _response(b'__version__ = "99.0.0"'),
            _response(b"#!/usr/bin/env bash\n# forgeflow installer\nexit 0\n"),
        ]
        args = parse_forgeflow_args(["upgrade", "--force"])
        with patch("forgeflow.distribution.resolve_installation_target", return_value=_target(self.root)), \
             patch("forgeflow.distribution.read_package_metadata", return_value={"version": "0.1.0"}), \
             patch("subprocess.run", return_value=MagicMock(returncode=0, stderr="")), \
             patch("forgeflow.distribution.verify_installed_distribution", return_value={
                 "ok": True, "errors": [], "observed": {}, "target": _target(self.root),
             }), \
             patch("builtins.print"):
            code = handle_upgrade(args)
            self.assertEqual(code, 0)
            mock_input.assert_not_called()

    @patch("urllib.request.urlopen")
    def test_upgrade_fetches_same_revision_without_cache_busting(self, mock_urlopen):
        mock_urlopen.side_effect = [
            _response(f'__version__ = "{__version__}"'.encode("utf-8")),
            _response(b"#!/usr/bin/env bash\n# forgeflow installer\nexit 0\n"),
        ]
        args = parse_forgeflow_args(["upgrade", "--check", "--json"])
        with patch("forgeflow.distribution.resolve_installation_target", return_value=_target(self.root)), \
             patch("forgeflow.distribution.read_package_metadata", return_value={}), \
             patch("builtins.print"):
            code = handle_upgrade(args)
            self.assertEqual(code, 0)
        urls = [call[0][0].full_url for call in mock_urlopen.call_args_list]
        self.assertEqual(len(urls), 2)
        self.assertTrue(urls[0].endswith("/src/forgeflow/_version.py"))
        self.assertTrue(urls[1].endswith("/install.sh"))
        self.assertNotIn("t=", urls[0])
        request = mock_urlopen.call_args_list[0][0][0]
        self.assertEqual(request.headers.get("Cache-control"), "no-cache, no-store, must-revalidate")
        self.assertEqual(request.headers.get("Pragma"), "no-cache")

    @patch("urllib.request.urlopen")
    def test_upgrade_remote_older_warning_json_and_stdout(self, mock_urlopen):
        mock_urlopen.side_effect = [
            _response(b'__version__ = "0.1.7"'),
            _response(b"#!/usr/bin/env bash\n# forgeflow installer\nexit 0\n"),
        ]
        args_json = parse_forgeflow_args(["upgrade", "--check", "--json"])
        with patch("forgeflow.distribution.resolve_installation_target", return_value=_target(self.root)), \
             patch("forgeflow.distribution.read_package_metadata", return_value={"version": "99.0.0"}):
            with patch("builtins.print") as mock_print:
                code = handle_upgrade(args_json)
                self.assertEqual(code, 0)
                output = json.loads(mock_print.call_args[0][0])
                self.assertIn("warning", output)
                self.assertIn("older than", output["warning"])

        mock_urlopen.side_effect = [
            _response(b'__version__ = "0.1.7"'),
            _response(b"#!/usr/bin/env bash\n# forgeflow installer\nexit 0\n"),
        ]
        args_stdout = parse_forgeflow_args(["upgrade", "--check"])
        with patch("forgeflow.distribution.resolve_installation_target", return_value=_target(self.root)), \
             patch("forgeflow.distribution.read_package_metadata", return_value={"version": "99.0.0"}):
            with patch("builtins.print") as mock_print:
                code = handle_upgrade(args_stdout)
                self.assertEqual(code, 0)
                printed_texts = " ".join(call[0][0] for call in mock_print.call_args_list if call[0])
                self.assertIn("⚠️  Warning:", printed_texts)
                self.assertIn("older than installed version", printed_texts)

    @patch("urllib.request.urlopen")
    def test_upgrade_includes_release_highlights(self, mock_urlopen):
        mock_urlopen.side_effect = [
            _response(b'__version__ = "99.0.0"'),
            _response(b"#!/usr/bin/env bash\n# forgeflow installer\nexit 0\n"),
        ]
        prefix = Path(_target(self.root)["prefix"])
        changelog = prefix / "current" / "lib" / "forgeflow" / "CHANGELOG.md"
        changelog.parent.mkdir(parents=True)
        changelog.write_text("## [99.0.0] - 2026-11-02\n\n### Added\n- Real installed build.\n", encoding="utf-8")
        args_json = parse_forgeflow_args(["upgrade", "--force", "--json"])
        with patch("forgeflow.distribution.resolve_installation_target", return_value=_target(self.root)), \
             patch("forgeflow.distribution.read_package_metadata", return_value={"version": "0.1.0"}), \
             patch("subprocess.run", return_value=MagicMock(returncode=0, stderr="")), \
             patch("forgeflow.distribution.verify_installed_distribution", return_value={
                 "ok": True, "errors": [], "observed": {}, "target": _target(self.root),
             }), \
             patch("builtins.print") as mock_print:
            code = handle_upgrade(args_json)
            self.assertEqual(code, 0)
            output = json.loads(mock_print.call_args[0][0])
            self.assertTrue(output["upgraded"])
            self.assertIn("release_highlights", output)


if __name__ == "__main__":
    unittest.main()
