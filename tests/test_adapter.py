import os
import tempfile
import time
import unittest

from forgeflow.adapter import (
    AdapterError,
    Capabilities,
    CapabilityCache,
    HMACAttestationVerifier,
    WorkerRequest,
    make_attestation,
    operation_allowed,
)
from forgeflow.lifecycle import AutonomousPolicy, OperationClass, ValidationError


class AdapterTests(unittest.TestCase):
    def test_structured_request_and_operation_allowlist(self):
        request = WorkerRequest(OperationClass.REPOSITORY_WRITE, ("src/example.py",), "baseline", "w", "i", "a")
        self.assertEqual(request.as_dict()["operation_class"], "repository_write")
        self.assertTrue(operation_allowed(OperationClass.READ_ONLY, Capabilities(
            supported_operations=frozenset({"read_only"}))))
        self.assertFalse(operation_allowed("external_write"))
        with self.assertRaises(ValidationError):
            WorkerRequest("repository_write", payload={"command": "rm -rf"})

    def test_attestation_requires_pinned_proof(self):
        policy = AutonomousPolicy.autonomous("full")
        verifier = HMACAttestationVerifier({"key-1": b"test-key"}, trust_anchor_id="anchor-1")
        unsigned = make_attestation(
            lifecycle_id="v0.5.0-adapter", host_session_id="session", adapter_id="codex",
            adapter_version="1", user_intent="explicit autonomous", policy=policy,
            issued_at="2026-10-05T00:00:00Z", expires_at="2099-10-05T00:00:00Z")
        signed = verifier.sign(unsigned, key_id="key-1")
        self.assertTrue(verifier(signed))
        self.assertFalse(verifier(type(signed)(**{**signed.as_dict(), "signature": "bad"})))
        self.assertFalse(verifier(type(signed)(**{**signed.as_dict(), "signature": signed.signature + "!!!!"})))

    def test_capability_cache_binding_integrity_and_expiry(self):
        with tempfile.TemporaryDirectory() as root:
            cache = CapabilityCache(os.path.join(root, "capabilities.json"), host_id="host", adapter_id="a",
                                    adapter_version="1", project_binding="project")
            capabilities = Capabilities(can_wait=True, supported_operations=frozenset({"read_only"}))
            cache.write(capabilities, issued_at=time.time(), expires_at=time.time() + 60)
            self.assertEqual(cache.load().can_wait, True)
            with open(cache.path, "r+", encoding="utf-8") as handle:
                content = handle.read().replace("project", "other")
                handle.seek(0)
                handle.write(content)
                handle.truncate()
            with self.assertRaises(AdapterError):
                cache.load()

    def test_capability_cache_write_rejects_symlink_target(self):
        with tempfile.TemporaryDirectory() as root:
            target = os.path.join(root, "target.json")
            path = os.path.join(root, "capabilities.json")
            with open(target, "w", encoding="utf-8") as handle:
                handle.write("original")
            os.symlink(target, path)
            cache = CapabilityCache(path, host_id="host", adapter_id="a", adapter_version="1", project_binding="project")
            with self.assertRaises(AdapterError):
                cache.write(Capabilities())
            with open(target, encoding="utf-8") as handle:
                self.assertEqual(handle.read(), "original")

    def test_capability_cache_write_rejects_nested_parent_symlink(self):
        with tempfile.TemporaryDirectory() as root:
            outside = os.path.join(root, "outside")
            os.mkdir(outside)
            link = os.path.join(root, "nested-link")
            os.symlink(outside, link)
            path = os.path.join(link, "cache", "capabilities.json")
            cache = CapabilityCache(path, host_id="host", adapter_id="a", adapter_version="1", project_binding="project")
            with self.assertRaises(AdapterError):
                cache.write(Capabilities())

    def test_capability_cache_write_rejects_user_local_ancestor_symlink(self):
        with tempfile.TemporaryDirectory(dir=os.getcwd()) as root:
            outside = os.path.join(root, "outside")
            os.mkdir(outside)
            link = os.path.join(root, "user-link")
            os.symlink(outside, link)
            path = os.path.join(link, "cache", "capabilities.json")
            cache = CapabilityCache(path, host_id="host", adapter_id="a", adapter_version="1", project_binding="project")
            with self.assertRaises(AdapterError):
                cache.write(Capabilities())


if __name__ == "__main__":
    unittest.main()
