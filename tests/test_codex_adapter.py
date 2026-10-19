import unittest

from forgeflow.adapter import Capabilities, NullAdapter, WorkerRequest
from forgeflow.codex_adapter import CapabilityUnavailable, CodexAdapter


class UnavailableNative:
    def probe_capabilities(self):
        raise CapabilityUnavailable("native unavailable")

    def dispatch_worker(self, request):
        raise CapabilityUnavailable("native unavailable")


class CodexAdapterTests(unittest.TestCase):
    def test_native_unavailable_falls_back_without_claiming_native_success(self):
        adapter = CodexAdapter(UnavailableNative(), NullAdapter())
        self.assertEqual(adapter.probe_capabilities(), Capabilities())
        with self.assertRaises(Exception):
            adapter.dispatch_worker(WorkerRequest("read_only"))

    def test_missing_native_attestation_verifier_fails_closed(self):
        adapter = CodexAdapter()
        self.assertFalse(adapter.verify_activation_attestation(None))


if __name__ == "__main__":
    unittest.main()
