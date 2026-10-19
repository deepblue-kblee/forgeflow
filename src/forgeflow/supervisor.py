"""A deliberately small local supervisor with no implicit process side effects."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .adapter import (
    AdapterError,
    Capabilities,
    HostAdapter,
    WorkerRequest,
    WorkerResult,
    operation_allowed,
)
from .lifecycle import (
    ActivationAttestation,
    AutonomousPolicy,
    CASConflict,
    LifecycleController,
    OperationClass,
    Status,
    TransitionError,
    ValidationError,
    digest,
    validate_relative_path,
    safe_event,
)


class SupervisorError(RuntimeError):
    """Raised when supervisor preflight or correlation fails."""


@dataclass(frozen=True)
class DispatchReceipt:
    invocation_id: str
    worker_id: str
    attempt_id: str
    fencing_epoch: int
    operation_generation: int


@dataclass(frozen=True)
class SupervisorOutcome:
    accepted: bool
    status: str
    reason: str = ""
    result: WorkerResult | None = None


class LocalSupervisor:
    """Coordinates a controller and injected adapter without spawning commands.

    The class has no subprocess, shell, Git, network, or filesystem behavior of
    its own.  Any effect is explicit in the supplied adapter implementation.
    """

    def __init__(self, controller: LifecycleController, adapter: HostAdapter):
        self.controller = controller
        self.adapter = adapter

    def capabilities(self) -> Capabilities:
        capabilities = self.adapter.probe_capabilities()
        if not isinstance(capabilities, Capabilities):
            raise SupervisorError("adapter returned malformed capabilities")
        return capabilities

    def preflight(self, request: WorkerRequest) -> None:
        if not isinstance(request, WorkerRequest):
            raise ValidationError("supervisor accepts only WorkerRequest")
        if request.operation_class in {OperationClass.EXTERNAL_WRITE.value, OperationClass.DESTRUCTIVE.value}:
            raise SupervisorError("operation class requires separate user authority")
        if not operation_allowed(request.operation_class, self.capabilities()):
            raise SupervisorError("operation is not supported by adapter capabilities")
        for path in request.planned_paths:
            normalized = validate_relative_path(path, self.controller.store.repository_root)
            if normalized == ".git" or normalized.startswith(".git/") or normalized == ".forgeflow" or normalized.startswith(".forgeflow/"):
                raise SupervisorError("planned path is outside the lifecycle write boundary")
        if not self.controller.can_dispatch(request.operation_class):
            raise SupervisorError("lifecycle status or operation guard forbids dispatch")
        state = self.controller.state
        if state["control"].get("in_flight") is not None:
            raise SupervisorError("a worker is already in flight")
        if state["progress"]["continuation_policy"] == "autonomous":
            raw = state["host"].get("attestation")
            if not isinstance(raw, dict):
                raise SupervisorError("autonomous dispatch requires activation attestation")
            try:
                attestation = ActivationAttestation.from_mapping(raw)
                policy = AutonomousPolicy.autonomous(state["progress"]["target_checkpoint"])
                attestation.validate(self.controller.store.release_id, digest(policy.as_dict()), require_verified=True)
                if attestation.host_session_id != state["host"].get("host_session_id"):
                    raise SupervisorError("autonomous dispatch host session binding mismatch")
                if attestation.adapter_id != getattr(self.adapter, "adapter_id", ""):
                    raise SupervisorError("autonomous dispatch adapter binding mismatch")
                if attestation.adapter_version != getattr(self.adapter, "adapter_version", ""):
                    raise SupervisorError("autonomous dispatch adapter version binding mismatch")
                if not self.adapter.verify_activation_attestation(attestation):
                    raise SupervisorError("autonomous dispatch attestation verification failed")
            except (SupervisorError, ValidationError, RuntimeError) as exc:
                if isinstance(exc, SupervisorError):
                    raise
                raise SupervisorError("autonomous dispatch attestation is invalid") from exc

    def dispatch(self, request: WorkerRequest) -> DispatchReceipt:
        self.preflight(request)
        state = self.controller.state
        try:
            invocation_id = self.adapter.dispatch_worker(request)
        except Exception as exc:
            self.controller.record_attempt(stage_loop_fingerprint="dispatch", attempt_class="dispatch_failure",
                                           failure="adapter dispatch failed")
            raise SupervisorError("adapter dispatch failed") from exc
        if not isinstance(invocation_id, str) or not invocation_id:
            raise SupervisorError("adapter returned invalid invocation id")
        updated = self.controller.begin_work(
            worker_id=request.worker_id or "worker",
            invocation_id=invocation_id,
            attempt_id=request.attempt_id or "attempt",
            operation_generation=state["control"]["operation_generation"],
        )
        inflight = updated["control"]["in_flight"]
        return DispatchReceipt(invocation_id, inflight["worker_id"], inflight["attempt_id"],
                               inflight["fencing_epoch"], inflight["operation_generation"])

    def wait(self, receipt: DispatchReceipt, *, timeout_seconds: float = 180.0) -> SupervisorOutcome:
        if timeout_seconds < 0:
            raise ValidationError("timeout cannot be negative")
        state = self.controller.state
        inflight = state["control"].get("in_flight")
        if inflight is None or inflight.get("invocation_id") != receipt.invocation_id:
            raise SupervisorError("worker receipt is not current")
        result = self.adapter.wait_worker(receipt.invocation_id, timeout_seconds)
        if result is None:
            self.controller.record_attempt(stage_loop_fingerprint="wait", attempt_class="wait_timeout",
                                           failure="worker wait timed out", next_action="retry or suspend")
            return SupervisorOutcome(False, self.controller.state["progress"]["status"], "wait_timeout")
        return self.record_result(result)

    def record_result(self, result: WorkerResult) -> SupervisorOutcome:
        state = self.controller.state
        inflight = state["control"].get("in_flight")
        if inflight is None:
            raise SupervisorError("no in-flight worker")
        if result.worker_id != inflight.get("worker_id") or result.invocation_id != inflight.get("invocation_id") or result.attempt_id != inflight.get("attempt_id"):
            self.controller.record_attempt(stage_loop_fingerprint="worker", attempt_class="correlation_failure",
                                           duplicate=True, failure="worker identity mismatch")
            raise SupervisorError("worker result correlation failed")
        if result.operation_generation != inflight.get("operation_generation"):
            self.controller.record_attempt(stage_loop_fingerprint="worker", attempt_class="stale_event",
                                           duplicate=True, failure="worker generation mismatch")
            return SupervisorOutcome(False, self.controller.state["progress"]["status"], "stale_event")
        try:
            updated = self.controller.complete_work(event_seq=result.event_seq, fencing_epoch=result.fencing_epoch,
                                                    success=result.success)
        except CASConflict:
            self.controller.record_attempt(stage_loop_fingerprint="worker", attempt_class="stale_event",
                                           duplicate=True, failure="worker fencing or sequence mismatch")
            return SupervisorOutcome(False, self.controller.state["progress"]["status"], "stale_event")
        if not result.success:
            self.controller.record_attempt(stage_loop_fingerprint="worker", attempt_class="worker_failure",
                                           failure=result.summary or "worker failure", token_usage=result.token_usage)
        return SupervisorOutcome(True, updated["progress"]["status"], "completed", result)

    def cancel(self, receipt: DispatchReceipt) -> bool:
        state = self.controller.state
        inflight = state["control"].get("in_flight")
        if inflight is None or inflight.get("invocation_id") != receipt.invocation_id:
            raise SupervisorError("worker receipt is not current")
        cancelled = bool(self.adapter.cancel_write_work(receipt.invocation_id))
        if cancelled:
            self.controller.transition(Status.PAUSED, reason="worker cancellation requested")
        else:
            self.controller.transition(Status.SUSPENDED, reason="worker cancellation unavailable")
        return cancelled

    def suspend_for_capability_loss(self, reason: str = "capability loss") -> dict[str, Any]:
        if self.controller.status in {Status.ACTIVE, Status.WAITING_INTERNAL}:
            return self.controller.transition(Status.SUSPENDED, reason=reason)
        return self.controller.state
