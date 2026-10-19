import tempfile
import unittest
from datetime import datetime, timedelta, timezone

from forgeflow.adapter import Capabilities, HMACAttestationVerifier, WorkerRequest, WorkerResult, make_attestation
from forgeflow.lifecycle import AutonomousPolicy, LifecycleController, OperationClass, Status
from forgeflow.supervisor import LocalSupervisor, SupervisorError


class FakeAdapter:
    adapter_id = "fake"
    adapter_version = "1"

    def __init__(self):
        self.dispatched = []
        self.result = None

    def probe_capabilities(self):
        return Capabilities(can_wait=True, can_cancel_write=True,
                            supported_operations=frozenset({"read_only", "repository_write", "local_commit"}))

    def dispatch_worker(self, request):
        self.dispatched.append(request)
        return "inv-1"

    def wait_worker(self, invocation_id, timeout_seconds):
        return self.result

    def cancel_write_work(self, invocation_id):
        return True

    def record_usage(self, invocation_id):
        return None

    def verify_activation_attestation(self, attestation):
        return True


class SupervisorTests(unittest.TestCase):
    def test_dispatch_and_correlated_result(self):
        with tempfile.TemporaryDirectory() as root:
            controller = LifecycleController.start(root, "v0.5.0-supervisor")
            adapter = FakeAdapter()
            supervisor = LocalSupervisor(controller, adapter)
            request = WorkerRequest(OperationClass.REPOSITORY_WRITE, ("src/example.py",), worker_id="worker-1",
                                    invocation_id="requested", attempt_id="attempt-1")
            receipt = supervisor.dispatch(request)
            self.assertEqual(controller.status, Status.WAITING_INTERNAL)
            adapter.result = WorkerResult("worker-1", receipt.invocation_id, "attempt-1", 1,
                                          receipt.fencing_epoch, receipt.operation_generation, True, "done")
            outcome = supervisor.wait(receipt)
            self.assertTrue(outcome.accepted)
            self.assertEqual(controller.status, Status.ACTIVE)

    def test_external_and_destructive_operations_are_rejected(self):
        with tempfile.TemporaryDirectory() as root:
            controller = LifecycleController.start(root, "v0.5.0-supervisor-guard")
            supervisor = LocalSupervisor(controller, FakeAdapter())
            for operation in ("external_write", "destructive"):
                request = WorkerRequest(operation, ())
                with self.assertRaises(SupervisorError):
                    supervisor.preflight(request)

    def test_stale_worker_result_does_not_change_state(self):
        with tempfile.TemporaryDirectory() as root:
            controller = LifecycleController.start(root, "v0.5.0-supervisor-stale")
            adapter = FakeAdapter()
            supervisor = LocalSupervisor(controller, adapter)
            receipt = supervisor.dispatch(WorkerRequest("repository_write", (), worker_id="worker", attempt_id="attempt"))
            stale = WorkerResult("worker", receipt.invocation_id, "attempt", 0, receipt.fencing_epoch,
                                 receipt.operation_generation, True, "stale")
            outcome = supervisor.record_result(stale)
            self.assertFalse(outcome.accepted)
            self.assertEqual(controller.status, Status.WAITING_INTERNAL)

    def test_second_dispatch_is_rejected_while_worker_is_in_flight(self):
        with tempfile.TemporaryDirectory() as root:
            controller = LifecycleController.start(root, "v0.5.0-supervisor-duplicate")
            adapter = FakeAdapter()
            supervisor = LocalSupervisor(controller, adapter)
            supervisor.dispatch(WorkerRequest("repository_write", (), worker_id="first", attempt_id="attempt-1"))
            with self.assertRaises(SupervisorError):
                supervisor.dispatch(WorkerRequest("repository_write", (), worker_id="second", attempt_id="attempt-2"))
            self.assertEqual(len(adapter.dispatched), 1)

    def test_autonomous_dispatch_revalidates_attestation(self):
        with tempfile.TemporaryDirectory() as root:
            controller = LifecycleController.start(root, "v0.5.0-attestation-guard")
            controller._update(lambda state: (
                state["progress"].update(continuation_policy="autonomous"),
                state["host"].update(attestation={}),
            ))
            supervisor = LocalSupervisor(controller, FakeAdapter())
            with self.assertRaises(SupervisorError):
                supervisor.preflight(WorkerRequest("read_only"))

    def test_autonomous_dispatch_rejects_adapter_identity_mismatch(self):
        with tempfile.TemporaryDirectory() as root:
            controller = LifecycleController.start(root, "v0.5.0-attestation-identity")
            policy = AutonomousPolicy.autonomous("full")
            verifier = HMACAttestationVerifier({"key": b"secret"}, trust_anchor_id="anchor")
            issued = datetime.now(timezone.utc)
            unsigned = make_attestation(
                lifecycle_id="v0.5.0-attestation-identity", host_session_id="session",
                adapter_id="codex", adapter_version="1", user_intent="autonomous",
                policy=policy, issued_at=issued.isoformat().replace("+00:00", "Z"),
                expires_at=(issued + timedelta(minutes=5)).isoformat().replace("+00:00", "Z"),
            )
            controller.activate(policy, verifier.sign(unsigned, key_id="key"), verifier)
            with self.assertRaises(SupervisorError):
                LocalSupervisor(controller, FakeAdapter()).preflight(WorkerRequest("read_only"))

    def test_sensitive_repository_paths_are_denied(self):
        with tempfile.TemporaryDirectory() as root:
            controller = LifecycleController.start(root, "v0.5.0-path-guard")
            supervisor = LocalSupervisor(controller, FakeAdapter())
            with self.assertRaises(SupervisorError):
                supervisor.preflight(WorkerRequest("read_only", (".git/config",)))


if __name__ == "__main__":
    unittest.main()
