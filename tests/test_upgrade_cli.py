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


if __name__ == "__main__":
    unittest.main()
