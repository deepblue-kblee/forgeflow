"""Codex-first host adapter with an explicit local fallback boundary.

The native transport is injected by the host.  ForgeFlow never assumes that a
Codex heartbeat or automation exists; an unavailable native capability is a
typed result and the supplied fallback adapter is used only for operations it
explicitly supports.
"""

from __future__ import annotations

from typing import Callable, Protocol

from .adapter import AdapterError, Capabilities, HostAdapter, WorkerRequest, WorkerResult
from .lifecycle import ActivationAttestation


class CapabilityUnavailable(AdapterError):
    """Native Codex transport is unavailable for this invocation."""

    code = "capability_unavailable"


class CodexNativeTransport(Protocol):
    """Minimal injected interface for a real Codex native transport."""

    def probe_capabilities(self) -> Capabilities: ...

    def dispatch_worker(self, request: WorkerRequest) -> str: ...

    def wait_worker(self, invocation_id: str, timeout_seconds: float) -> WorkerResult | None: ...

    def cancel_write_work(self, invocation_id: str) -> bool: ...

    def record_usage(self, invocation_id: str) -> int | None: ...

    def verify_activation_attestation(self, attestation: ActivationAttestation) -> bool: ...


class CodexAdapter:
    """Use native same-thread continuation first, then an explicit fallback."""

    adapter_id = "codex"
    adapter_version = "1"

    def __init__(self, native: CodexNativeTransport | None = None,
                 fallback: HostAdapter | None = None,
                 attestation_verifier: Callable[[ActivationAttestation], bool] | None = None):
        self.native = native
        self.fallback = fallback
        self.attestation_verifier = attestation_verifier

    def _native_call(self, name: str, *args):
        if self.native is None or not hasattr(self.native, name):
            raise CapabilityUnavailable(f"native Codex capability unavailable: {name}")
        try:
            return getattr(self.native, name)(*args)
        except CapabilityUnavailable:
            raise
        except Exception as exc:
            raise CapabilityUnavailable(f"native Codex capability failed: {name}") from exc

    def probe_capabilities(self) -> Capabilities:
        try:
            value = self._native_call("probe_capabilities")
            if isinstance(value, Capabilities):
                return value
        except CapabilityUnavailable:
            pass
        if self.fallback is not None:
            return self.fallback.probe_capabilities()
        return Capabilities()

    def dispatch_worker(self, request: WorkerRequest) -> str:
        try:
            return self._native_call("dispatch_worker", request)
        except CapabilityUnavailable:
            if self.fallback is None:
                raise
            return self.fallback.dispatch_worker(request)

    def wait_worker(self, invocation_id: str, timeout_seconds: float) -> WorkerResult | None:
        try:
            return self._native_call("wait_worker", invocation_id, timeout_seconds)
        except CapabilityUnavailable:
            if self.fallback is None:
                return None
            return self.fallback.wait_worker(invocation_id, timeout_seconds)

    def cancel_write_work(self, invocation_id: str) -> bool:
        try:
            return bool(self._native_call("cancel_write_work", invocation_id))
        except CapabilityUnavailable:
            return bool(self.fallback and self.fallback.cancel_write_work(invocation_id))

    def record_usage(self, invocation_id: str) -> int | None:
        try:
            return self._native_call("record_usage", invocation_id)
        except CapabilityUnavailable:
            return self.fallback.record_usage(invocation_id) if self.fallback else None

    def verify_activation_attestation(self, attestation: ActivationAttestation) -> bool:
        if self.attestation_verifier is not None:
            return bool(self.attestation_verifier(attestation))
        try:
            return bool(self._native_call("verify_activation_attestation", attestation))
        except CapabilityUnavailable:
            return False

