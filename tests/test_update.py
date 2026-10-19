import json
import tempfile
import unittest
from pathlib import Path

from forgeflow import __version__
from forgeflow.scaffold import TemplateScaffolder
from forgeflow.update import apply, inspect
from forgeflow.bundle_catalog import V045_UPDATE_SECTION, V045_VERSION_LINE, bundle_for


class UpdateTests(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp())
        self.addCleanup(lambda: __import__("shutil").rmtree(self.root, ignore_errors=True))
        TemplateScaffolder.init_project_governance(self.root, "fixture")

    def test_preview_is_read_only_and_current(self):
        before = (self.root / ".forgeflow.json").read_bytes()
        result = inspect(self.root)
        self.assertEqual("up_to_date", result["status"])
        self.assertEqual(before, (self.root / ".forgeflow.json").read_bytes())

    def test_apply_upgrades_clean_old_marker(self):
        config = self.root / ".forgeflow.json"
        data = json.loads(config.read_text())
        data["forgeflow_version"] = "0.4.4"
        config.write_text(json.dumps(data), encoding="utf-8")
        for relative, content in bundle_for("0.4.4").items():
            (self.root / relative).write_text(content, encoding="utf-8")
        self.assertEqual("upgrade_available", inspect(self.root)["status"])
        self.assertIn(".forgeflow.json", inspect(self.root)["paths"])
        self.assertEqual("up_to_date", apply(self.root)["status"])
        self.assertEqual(__version__, json.loads(config.read_text())["forgeflow_version"])

    def test_apply_upgrades_exact_unversioned_legacy_bundle(self):
        config = self.root / ".forgeflow.json"
        data = json.loads(config.read_text())
        data.pop("forgeflow_version")
        config.write_text(json.dumps(data), encoding="utf-8")
        for relative, content in bundle_for("0.4.4").items():
            (self.root / relative).write_text(content, encoding="utf-8")

        self.assertEqual("upgrade_available", inspect(self.root)["status"])
        self.assertEqual("0.4.4", inspect(self.root)["installed_version"])
        self.assertEqual("up_to_date", apply(self.root)["status"])
        self.assertEqual(__version__, json.loads(config.read_text())["forgeflow_version"])

    def test_unversioned_edited_bundle_is_unsupported_and_never_applied(self):
        config = self.root / ".forgeflow.json"
        data = json.loads(config.read_text())
        data.pop("forgeflow_version")
        config.write_text(json.dumps(data), encoding="utf-8")

        self.assertEqual("unsupported", inspect(self.root)["status"])
        self.assertEqual("unsupported", apply(self.root)["status"])

    def test_local_bundle_edit_does_not_block_upgrade(self):
        config = self.root / ".forgeflow.json"
        data = json.loads(config.read_text())
        data["forgeflow_version"] = "0.8.1"
        config.write_text(json.dumps(data), encoding="utf-8")
        guide = self.root / TemplateScaffolder.GOVERNANCE_PATH
        guide.write_text("local edit", encoding="utf-8")
        self.assertEqual("upgrade_available", inspect(self.root)["status"])
        self.assertEqual("up_to_date", apply(self.root)["status"])
        self.assertNotEqual("local edit", guide.read_text(encoding="utf-8"))

    def test_duplicate_configuration_key_is_unsupported(self):
        (self.root / ".forgeflow.json").write_text('{"forgeflow_version":"0.4.4","forgeflow_version":"0.4.5"}', encoding="utf-8")
        self.assertEqual("unsupported", inspect(self.root)["status"])

    def test_unknown_older_marker_is_unsupported(self):
        config = self.root / ".forgeflow.json"
        data = json.loads(config.read_text())
        data["forgeflow_version"] = "0.0.1"
        config.write_text(json.dumps(data), encoding="utf-8")
        self.assertEqual("unsupported", inspect(self.root)["status"])

    def test_journal_preview_does_not_mutate(self):
        journal = self.root / TemplateScaffolder.JOURNAL_PATH
        journal.write_text('{"invalid": true}', encoding="utf-8")
        before = journal.read_bytes()
        self.assertEqual("recovery_required", inspect(self.root)["status"])
        self.assertEqual(before, journal.read_bytes())

    def test_malformed_journal_apply_is_fail_closed(self):
        journal = self.root / TemplateScaffolder.JOURNAL_PATH
        journal.write_text('{"invalid": true}', encoding="utf-8")
        result = apply(self.root)
        self.assertEqual("recovery_required", result["status"])
        self.assertTrue(journal.exists())

    def test_symlink_root_is_unsupported(self):
        alias = self.root.parent / (self.root.name + "-alias")
        alias.symlink_to(self.root, target_is_directory=True)
        self.addCleanup(alias.unlink)
        self.assertEqual("unsupported", inspect(alias)["status"])

    def test_legacy_projection_removes_marker_and_update_contract(self):
        old, current = bundle_for("0.4.4"), bundle_for("0.4.5")
        for path in current:
            if path == TemplateScaffolder.GOVERNANCE_PATH:
                self.assertEqual(old[path], current[path].replace(V045_VERSION_LINE, ""))
            elif path == Path("docs/forgeflow/spec/FLOW_SPEC.md"):
                self.assertEqual(old[path], current[path].replace(V045_UPDATE_SECTION, ""))
            else:
                self.assertEqual(old[path], current[path])

    def test_clean_v046_marker_upgrades_and_markerless_v046_is_unsupported(self):
        config = self.root / ".forgeflow.json"
        data = json.loads(config.read_text())
        data["forgeflow_version"] = "0.4.6"
        config.write_text(json.dumps(data), encoding="utf-8")
        for relative, content in bundle_for("0.4.6").items():
            (self.root / relative).write_text(content, encoding="utf-8")
        self.assertEqual("upgrade_available", inspect(self.root)["status"])
        self.assertEqual("up_to_date", apply(self.root)["status"])
        data.pop("forgeflow_version")
        config.write_text(json.dumps(data), encoding="utf-8")
        for relative, content in bundle_for("0.4.6").items():
            (self.root / relative).write_text(content, encoding="utf-8")
        self.assertEqual("unsupported", inspect(self.root)["status"])


if __name__ == "__main__":
    unittest.main()
