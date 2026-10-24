import json
import unittest
from unittest.mock import patch, MagicMock
from forgeflow.cli import parse_version_tuple, handle_upgrade, parse_forgeflow_args


class TestUpgradeCLI(unittest.TestCase):
    def test_parse_version_tuple(self):
        self.assertEqual(parse_version_tuple("0.1.2"), (0, 1, 2))
        self.assertEqual(parse_version_tuple("v0.1.3"), (0, 1, 3))
        self.assertEqual(parse_version_tuple("1.0"), (1, 0))
        self.assertTrue(parse_version_tuple("0.1.3") > parse_version_tuple("0.1.2"))
        self.assertTrue(parse_version_tuple("0.2.0") > parse_version_tuple("0.1.9"))

    @patch("urllib.request.urlopen")
    def test_upgrade_check_up_to_date(self, mock_urlopen):
        # Mock remote version same as current
        from forgeflow._version import __version__
        mock_resp = MagicMock()
        mock_resp.read.return_value = f'__version__ = "{__version__}"'.encode("utf-8")
        mock_resp.__enter__.return_value = mock_resp
        mock_urlopen.return_value = mock_resp

        args = parse_forgeflow_args(["upgrade", "--check", "--json"])
        with patch("builtins.print") as mock_print:
            code = handle_upgrade(args)
            self.assertEqual(code, 0)
            mock_print.assert_called_once()
            output = json.loads(mock_print.call_args[0][0])
            self.assertEqual(output["status"], "success")
            self.assertFalse(output["upgrade_available"])

    @patch("urllib.request.urlopen")
    def test_upgrade_check_upgrade_available(self, mock_urlopen):
        # Mock remote version higher than current
        mock_resp = MagicMock()
        mock_resp.read.return_value = b'__version__ = "99.9.9"'
        mock_resp.__enter__.return_value = mock_resp
        mock_urlopen.return_value = mock_resp

        args = parse_forgeflow_args(["upgrade", "--check", "--json"])
        with patch("builtins.print") as mock_print:
            code = handle_upgrade(args)
            self.assertEqual(code, 0)
            mock_print.assert_called_once()
            output = json.loads(mock_print.call_args[0][0])
            self.assertEqual(output["status"], "success")
            self.assertTrue(output["upgrade_available"])
            self.assertEqual(output["remote_version"], "99.9.9")

    @patch("urllib.request.urlopen")
    def test_upgrade_already_up_to_date_skips_install(self, mock_urlopen):
        from forgeflow._version import __version__
        mock_resp = MagicMock()
        mock_resp.read.return_value = f'__version__ = "{__version__}"'.encode("utf-8")
        mock_resp.__enter__.return_value = mock_resp
        mock_urlopen.return_value = mock_resp

        args = parse_forgeflow_args(["upgrade", "--json"])
        with patch("subprocess.run") as mock_subproc, patch("builtins.print") as mock_print:
            code = handle_upgrade(args)
            self.assertEqual(code, 0)
            mock_subproc.assert_not_called()
            output = json.loads(mock_print.call_args[0][0])
            self.assertFalse(output["upgraded"])

    @patch("subprocess.run")
    @patch("urllib.request.urlopen")
    def test_upgrade_executes_installer_when_upgrade_available(self, mock_urlopen, mock_subproc):
        # Version check returns 99.0.0, installer download returns echo script
        v_resp = MagicMock()
        v_resp.read.return_value = b'__version__ = "99.0.0"'
        v_resp.__enter__.return_value = v_resp

        inst_resp = MagicMock()
        inst_resp.read.return_value = b'#!/usr/bin/env bash\necho "installed"'
        inst_resp.__enter__.return_value = inst_resp

        mock_urlopen.side_effect = [v_resp, inst_resp]

        mock_subproc_result = MagicMock()
        mock_subproc_result.returncode = 0
        mock_subproc.return_value = mock_subproc_result

        args = parse_forgeflow_args(["upgrade", "--json"])
        with patch("builtins.print") as mock_print:
            code = handle_upgrade(args)
            self.assertEqual(code, 0)
            mock_subproc.assert_called_once()
            output = json.loads(mock_print.call_args[0][0])
            self.assertTrue(output["upgraded"])
            self.assertEqual(output["current_version"], "99.0.0")

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
    @patch("subprocess.run")
    @patch("urllib.request.urlopen")
    def test_upgrade_interactive_prompt_yes(self, mock_urlopen, mock_subproc, mock_input):
        mock_input.return_value = "y"
        v_resp = MagicMock()
        v_resp.read.return_value = b'__version__ = "99.0.0"'
        v_resp.__enter__.return_value = v_resp

        inst_resp = MagicMock()
        inst_resp.read.return_value = b'#!/usr/bin/env bash\necho "installed"'
        inst_resp.__enter__.return_value = inst_resp

        mock_urlopen.side_effect = [v_resp, inst_resp]
        mock_subproc.return_value = MagicMock(returncode=0)

        args = parse_forgeflow_args(["upgrade"])
        with patch("builtins.print"):
            code = handle_upgrade(args)
            self.assertEqual(code, 0)
            mock_input.assert_called_once()
            self.assertIn("upgrade to v99.0.0", mock_input.call_args[0][0])
            mock_subproc.assert_called_once()

    @patch("builtins.input")
    @patch("subprocess.run")
    @patch("urllib.request.urlopen")
    def test_upgrade_interactive_prompt_no_cancels(self, mock_urlopen, mock_subproc, mock_input):
        mock_input.return_value = "n"
        v_resp = MagicMock()
        v_resp.read.return_value = b'__version__ = "99.0.0"'
        v_resp.__enter__.return_value = v_resp

        mock_urlopen.side_effect = [v_resp]

        args = parse_forgeflow_args(["upgrade"])
        with patch("builtins.print") as mock_print:
            code = handle_upgrade(args)
            self.assertEqual(code, 0)
            mock_input.assert_called_once()
            mock_subproc.assert_not_called()
            mock_print.assert_any_call("Upgrade cancelled.")

    @patch("builtins.input")
    @patch("subprocess.run")
    @patch("urllib.request.urlopen")
    def test_upgrade_force_skips_prompt(self, mock_urlopen, mock_subproc, mock_input):
        v_resp = MagicMock()
        v_resp.read.return_value = b'__version__ = "99.0.0"'
        v_resp.__enter__.return_value = v_resp

        inst_resp = MagicMock()
        inst_resp.read.return_value = b'#!/usr/bin/env bash\necho "installed"'
        inst_resp.__enter__.return_value = inst_resp

        mock_urlopen.side_effect = [v_resp, inst_resp]
        mock_subproc.return_value = MagicMock(returncode=0)

        args = parse_forgeflow_args(["upgrade", "--force"])
        with patch("builtins.print"):
            code = handle_upgrade(args)
            self.assertEqual(code, 0)
            mock_input.assert_not_called()
            mock_subproc.assert_called_once()

    @patch("urllib.request.urlopen")
    def test_upgrade_cache_busting_and_headers(self, mock_urlopen):
        from forgeflow._version import __version__
        mock_resp = MagicMock()
        mock_resp.read.return_value = f'__version__ = "{__version__}"'.encode("utf-8")
        mock_resp.__enter__.return_value = mock_resp
        mock_urlopen.return_value = mock_resp

        args = parse_forgeflow_args(["upgrade", "--check", "--json"])
        with patch("builtins.print"):
            code = handle_upgrade(args)
            self.assertEqual(code, 0)

        mock_urlopen.assert_called_once()
        req = mock_urlopen.call_args[0][0]
        self.assertIn("t=", req.full_url)
        self.assertEqual(req.headers.get("Cache-control"), "no-cache, no-store, must-revalidate")
        self.assertEqual(req.headers.get("Pragma"), "no-cache")

    @patch("urllib.request.urlopen")
    def test_upgrade_remote_older_warning_json_and_stdout(self, mock_urlopen):
        # When remote version is older than current version (e.g. CDN cache delay)
        v_resp = MagicMock()
        v_resp.read.return_value = b'__version__ = "0.1.7"'
        v_resp.__enter__.return_value = v_resp
        mock_urlopen.return_value = v_resp

        # Check JSON output
        args_json = parse_forgeflow_args(["upgrade", "--check", "--json"])
        with patch("builtins.print") as mock_print:
            code = handle_upgrade(args_json)
            self.assertEqual(code, 0)
            output = json.loads(mock_print.call_args[0][0])
            self.assertIn("warning", output)
            self.assertIn("older than", output["warning"])

        # Check stdout terminal output
        args_stdout = parse_forgeflow_args(["upgrade", "--check"])
        with patch("builtins.print") as mock_print:
            code = handle_upgrade(args_stdout)
            self.assertEqual(code, 0)
            printed_texts = " ".join(call[0][0] for call in mock_print.call_args_list if call[0])
            self.assertIn("⚠️  Warning:", printed_texts)
            self.assertIn("older than local version", printed_texts)

    @patch("pathlib.Path.home")
    @patch("subprocess.run")
    @patch("urllib.request.urlopen")
    def test_upgrade_verified_installed_version(self, mock_urlopen, mock_subproc, mock_home):
        import tempfile
        from pathlib import Path

        v_resp = MagicMock()
        v_resp.read.return_value = b'__version__ = "0.1.7"'  # Stale CDN returned 0.1.7
        v_resp.__enter__.return_value = v_resp

        inst_resp = MagicMock()
        inst_resp.read.return_value = b'#!/usr/bin/env bash\necho "installed"'
        inst_resp.__enter__.return_value = inst_resp

        mock_urlopen.side_effect = [v_resp, inst_resp]
        mock_subproc.return_value = MagicMock(returncode=0)

        with tempfile.TemporaryDirectory() as tmp_home:
            mock_home.return_value = Path(tmp_home)
            version_file = Path(tmp_home) / ".local" / "forgeflow" / "current" / "lib" / "forgeflow" / "_version.py"
            version_file.parent.mkdir(parents=True, exist_ok=True)
            # Actually installed version by install.sh was 0.1.10
            version_file.write_text('__version__ = "0.1.10"\n', encoding="utf-8")

            args = parse_forgeflow_args(["upgrade", "--force"])
            with patch("builtins.print") as mock_print:
                code = handle_upgrade(args)
                self.assertEqual(code, 0)
                mock_print.assert_any_call("🎉 Successfully upgraded ForgeFlow to v0.1.10!")

    @patch("subprocess.run")
    @patch("urllib.request.urlopen")
    def test_upgrade_includes_release_highlights(self, mock_urlopen, mock_subproc):
        v_resp = MagicMock()
        v_resp.read.return_value = b'__version__ = "0.1.13"'
        v_resp.__enter__.return_value = v_resp

        inst_resp = MagicMock()
        inst_resp.read.return_value = b'#!/usr/bin/env bash\necho "installed"'
        inst_resp.__enter__.return_value = inst_resp

        mock_urlopen.side_effect = [v_resp, inst_resp]
        mock_subproc.return_value = MagicMock(returncode=0)

        # JSON mode
        args_json = parse_forgeflow_args(["upgrade", "--force", "--json"])
        with patch("builtins.print") as mock_print:
            code = handle_upgrade(args_json)
            self.assertEqual(code, 0)
            output = json.loads(mock_print.call_args[0][0])
            self.assertTrue(output["upgraded"])
            self.assertIn("release_highlights", output)

        # Re-mock urlopen
        v_resp2 = MagicMock()
        v_resp2.read.return_value = b'__version__ = "0.1.13"'
        v_resp2.__enter__.return_value = v_resp2
        inst_resp2 = MagicMock()
        inst_resp2.read.return_value = b'#!/usr/bin/env bash\necho "installed"'
        inst_resp2.__enter__.return_value = inst_resp2
        mock_urlopen.side_effect = [v_resp2, inst_resp2]

        # Stdout mode
        args_stdout = parse_forgeflow_args(["upgrade", "--force"])
        with patch("builtins.print") as mock_print:
            code = handle_upgrade(args_stdout)
            self.assertEqual(code, 0)
            printed = " ".join(call[0][0] for call in mock_print.call_args_list if call[0])
            self.assertIn("Release Highlights", printed)
            self.assertIn("forgeflow doc show changelog", printed)


if __name__ == "__main__":
    unittest.main()
