"""Small development workflow with explicit Git authority and resumable finalization.

The strict release lifecycle is intentionally separate. This module records one
task agreement and the execution facts needed to finish it; it never allocates a
branch or a worktree and never interprets readiness as permission to merge.
"""
from __future__ import annotations

from contextlib import contextmanager
import copy
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import time
import unicodedata


class WorkflowError(RuntimeError):
    """A precise pending step; the last verified outcome remains in state."""


def validate_relative_path(path: str, root: str | os.PathLike[str] | None = None) -> str:
    raw = unicodedata.normalize("NFC", str(path))
    if not raw or raw != str(path) or "\x00" in raw or any(ord(char) < 32 for char in raw):
        raise WorkflowError("unsafe path")
    candidate = Path(raw)
    if candidate.is_absolute() or any(part == ".." for part in candidate.parts):
        raise WorkflowError("path must be relative and contained")
    if any(part in {"", "."} for part in candidate.parts):
        raise WorkflowError("path contains an empty or dot component")
    normalized = candidate.as_posix()
    if root is not None:
        root_path = Path(root).resolve()
        current = root_path
        for part in candidate.parts:
            current = current / part
            if current.is_symlink():
                raise WorkflowError("symlink path is not allowed")
        full = (root_path / normalized).resolve(strict=False)
        try:
            full.relative_to(root_path)
        except ValueError as exc:
            raise WorkflowError("path escapes repository root") from exc
    return normalized


def _digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=True).encode()).hexdigest()


def _git(root, *args, check=True):
    try:
        result = subprocess.run(["git", "--literal-pathspecs", "-C", str(root), *args], capture_output=True,
                                text=True, errors="surrogateescape", timeout=60)
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise WorkflowError(f"git {args[0]} could not finish: {type(exc).__name__}") from exc
    if check and result.returncode:
        raise WorkflowError(f"git {args[0]} failed: {result.stderr.strip()}")
    return (result.stdout if "-z" in args else result.stdout.strip()) if check else result


def _config(root):
    for path in (root / ".forgeflow/config.json", root / ".forgeflow.json"):
        if path.exists():
            value = json.loads(path.read_text())
            if not isinstance(value, dict):
                raise WorkflowError("project configuration must be an object")
            return value
    return {}


def _check_commands(value):
    if not isinstance(value, list):
        raise WorkflowError("checks must be a list of argv lists")
    commands = []
    for argv in value:
        if (not isinstance(argv, list) or not argv
                or any(not isinstance(arg, str) or not arg or "\x00" in arg for arg in argv)):
            raise WorkflowError("each check must be a nonempty argv list (no shell string)")
        if argv not in commands:
            commands.append(argv)
    return commands


def _workflow_config(root):
    value = _config(root).get("workflow", {})
    if not isinstance(value, dict):
        raise WorkflowError("workflow configuration must be an object")
    return value


def _assert_owner(root, agreement):
    owner = _workflow_config(root).get("owner", "standalone")
    if owner not in {"standalone", "host"}:
        raise WorkflowError("project workflow.owner must be standalone or host")
    if owner == "host" and agreement.get("owner") != "host":
        raise WorkflowError("project declares host ownership; standalone repository operations are not permitted")


def required_checks(root, agreement):
    """Task commands can add to, but cannot remove, project requirements."""
    configured = _workflow_config(root)
    return _check_commands(_check_commands(configured.get("checks", []))
                           + _check_commands(agreement.get("checks", [])))


def _inside_scope(path, scope):
    return any(path == item or path.startswith(item + "/") for item in scope)


def _dirty(root):
    paths = set()
    for args in (("diff", "--no-renames", "--name-only", "-z"),
                 ("diff", "--cached", "--no-renames", "--name-only", "-z"),
                 ("ls-files", "--others", "--exclude-standard", "-z")):
        output = _git(root, *args)
        paths.update(path for path in output.split("\x00") if path)
    return paths


def _verification_paths(root, agreement):
    configured = _workflow_config(root)
    project = configured.get("verification_paths")
    task = agreement.get("verification_paths")
    if project is None and task is None:
        return None  # Conservative tracked dependency coverage.
    selected = []
    for value in (project if project is not None else [], task if task is not None else agreement["scope"]):
        if not isinstance(value, list) or any(not isinstance(path, str) for path in value):
            raise WorkflowError("verification_paths must be a list of relative dependency paths")
        selected.extend(validate_relative_path(path, root) for path in value)
    if not selected or any(path in {"", "."} for path in selected):
        raise WorkflowError("verification_paths must name nonempty explicit paths")
    return sorted(set(selected))


def _content(root, scope, verification_paths=None):
    # Existing tracked dependencies are inputs, including files outside scope.
    # Untracked files are inputs only within task-owned paths. State/snapshots
    # are bookkeeping, never an implementation input or a staged task file.
    paths = set(_git(root, "ls-files", "-z").split("\x00"))
    paths.update(path for path in _dirty(root)
                 if _inside_scope(path, scope)
                 or (verification_paths is not None and _inside_scope(path, verification_paths)))
    result = []
    for name in sorted(paths):
        if not name or name.startswith((".forgeflow/workflows/", ".forgeflow/runtime/")):
            continue
        if verification_paths is not None and not _inside_scope(name, verification_paths):
            continue
        if name in {".forgeflow/run.py", ".forgeflow/runtime.json"}:
            continue
        path = root / name
        if path.is_symlink():
            value = ["symlink", os.readlink(path)]
        elif path.is_file():
            value = ["file", hashlib.sha256(path.read_bytes()).hexdigest(), path.stat().st_mode & 0o111]
        else:
            continue  # A committed deletion has the same inputs as its verified absence.
        result.append([name, value])
    return _digest(result)


def _undelivered_dependencies(root, agreement):
    """Find verified inputs that would be omitted from a task-only commit.

    The default conservatively treats tracked files as dependencies. Explicit
    verification_paths let the plan declare genuinely unrelated dirty work.
    These paths are reported, never staged, reset or stashed by this workflow.
    """
    inputs = _verification_paths(root, agreement)
    tracked = set(_git(root, "ls-files", "-z").split("\x00"))
    pending = []
    for path in sorted(_dirty(root)):
        if _inside_scope(path, agreement["scope"]):
            continue
        if path.startswith((".forgeflow/workflows/", ".forgeflow/runtime/")) or path in {".forgeflow/run.py", ".forgeflow/runtime.json"}:
            continue
        if (inputs is None and path in tracked) or (inputs is not None and _inside_scope(path, inputs)):
            pending.append(path)
    return pending


def _assert_scope_diff(root, agreement, source_sha, target_sha):
    changed = _git(root, "diff", "--no-renames", "--name-only", "-z", target_sha, source_sha).split("\x00")
    if any(path and not _inside_scope(path, agreement["scope"]) for path in changed):
        raise WorkflowError("source includes committed changes outside the agreed task scope")
    return [path for path in changed if path]


def _ref(root, name):
    if not isinstance(name, str) or not name or name.startswith("-"):
        raise WorkflowError("branch name is required")
    if _git(root, "check-ref-format", "--branch", name, check=False).returncode:
        raise WorkflowError("invalid branch name")
    return name


def _head(root, branch=None):
    return _git(root, "rev-parse", "--verify", ("refs/heads/" + branch if branch else "HEAD") + "^{commit}")


def _ancestor(root, older, newer):
    return _git(root, "merge-base", "--is-ancestor", older, newer, check=False).returncode == 0


def _identity(root):
    return {"root": str(root), "git_dir": _git(root, "rev-parse", "--absolute-git-dir"),
            "common_dir": str((root / _git(root, "rev-parse", "--git-common-dir")).resolve())}


def _environment(root, agreement):
    configured = _workflow_config(root)
    names = configured.get("environment", [])
    if not isinstance(names, list) or any(not isinstance(name, str) for name in names):
        raise WorkflowError("workflow.environment must be a list of variable names")
    # Values are hashed, never retained or printed (they may contain secrets).
    defaults = ["PATH", "PYTHONPATH", "PYTHONHOME", "VIRTUAL_ENV", "CONDA_PREFIX", "NODE_PATH", "NODE_OPTIONS"]
    return _digest({"python": sys.version, "executable": sys.executable,
                    "environment": {name: os.environ.get(name) for name in [*defaults, *names]},
                    "timeout": _config(root).get("governance", {}).get("test_timeout_seconds", 300),
                    "checks": required_checks(root, agreement)})


def _failure_excerpt(stdout, stderr):
    """Keep a bounded failure clue and redact known secret environment values."""
    def decoded(value):
        return value.decode(errors="replace") if isinstance(value, bytes) else (value or "")
    text = (decoded(stdout) + "\n" + decoded(stderr))[-4000:]
    for key, value in os.environ.items():
        if value and re.search(r"TOKEN|SECRET|PASSWORD|CREDENTIAL|API_KEY|PRIVATE_KEY", key, re.I):
            text = text.replace(value, "[redacted]")
    return text.strip()


def _validate_agreement(root, value):
    if not isinstance(value, dict):
        raise WorkflowError("agreement must be a JSON object")
    agreement = copy.deepcopy(value)
    for field in ("scope", "acceptance"):
        if not isinstance(agreement.get(field), list) or not agreement[field]:
            raise WorkflowError(f"{field} must be a nonempty list")
        if any(not isinstance(item, str) or not item.strip() for item in agreement[field]):
            raise WorkflowError(f"{field} entries must be nonempty text")
    if not isinstance(agreement.get("plan"), str) or not agreement["plan"].strip():
        raise WorkflowError("a plan is required before implementation")
    agreement["scope"] = sorted({validate_relative_path(path, root) for path in agreement["scope"]})
    for path in agreement["scope"]:
        if path in {".", ""}:
            raise WorkflowError("scope must name explicit task paths, not the repository root")
        if path == ".git" or path.startswith(".git/") or path == ".forgeflow" or path.startswith(".forgeflow/workflows") or path.startswith(".forgeflow/runtime"):
            raise WorkflowError("workflow metadata and Git internals cannot be task scope")
    if agreement.get("owner") not in {"standalone", "host"}:
        raise WorkflowError("owner must be standalone or host")
    _assert_owner(root, agreement)
    agreement.setdefault("integration", "none")
    if agreement["integration"] not in {"none", "local", "pr"}:
        raise WorkflowError("integration must be none, local or pr")
    if agreement["integration"] == "pr" and agreement["owner"] != "host":
        raise WorkflowError("PR integration requires owner=host so the owning tool can execute and report its result")
    _ref(root, agreement.get("source"))
    if agreement["integration"] != "none":
        _ref(root, agreement.get("target"))
        if agreement["target"] == agreement["source"]:
            raise WorkflowError("integration source and target must differ")
        _head(root, agreement["target"])
    permissions = agreement.setdefault("permissions", [])
    allowed = {"commit", "push", "merge", "delete-branch", "host-cleanup"}
    if not isinstance(permissions, list) or any(item not in allowed for item in permissions):
        raise WorkflowError("unsupported delegated permission")
    for field in ("task_owned_branch", "include_existing_changes"):
        if field in agreement and not isinstance(agreement[field], bool):
            raise WorkflowError(f"{field} must be a boolean")
        agreement.setdefault(field, False)
    agreement.setdefault("checks", [])
    required_checks(root, agreement)
    _verification_paths(root, agreement)
    if "push" in permissions:
        remote = agreement.setdefault("remote", "origin")
        if not isinstance(remote, str) or not re.fullmatch(r"[A-Za-z0-9_.-]+", remote) or remote.startswith("-"):
            raise WorkflowError("invalid remote name")
        agreement["remote_identity"] = _digest(_git(root, "remote", "get-url", remote))
    for field in ("verification_note", "commit_message"):
        if field in agreement and (not isinstance(agreement[field], str) or not agreement[field].strip()):
            raise WorkflowError(f"{field} must be nonempty text")
    return agreement


def _now():
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


class Workflow:
    """Single-file task state; process lock covers commands and Git effects."""

    def __init__(self, root, task_id):
        self.root = Path(root).resolve()
        if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,127}", task_id):
            raise WorkflowError("unsafe workflow ID")
        self.task_id = task_id
        self.directory = self.root / ".forgeflow/workflows"
        validate_relative_path(".forgeflow/workflows", self.root)
        self.path = self.directory / (task_id + ".json")
        validate_relative_path(str(self.path.relative_to(self.root)), self.root)

    @contextmanager
    def locked(self):
        self.directory.mkdir(parents=True, exist_ok=True)
        lock_path = self.directory / ".repository.lock"
        # flock releases on process exit, unlike stale lock directories.
        import fcntl
        fd = os.open(lock_path, os.O_CREAT | os.O_RDWR | getattr(os, "O_NOFOLLOW", 0), 0o600)
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            yield
        except BlockingIOError as exc:
            raise WorkflowError("workflow is busy; another process owns its lock") from exc
        finally:
            os.close(fd)

    def load(self):
        state = json.loads(self.path.read_text())
        if state.get("schema") != 1 or state.get("id") != self.task_id:
            raise WorkflowError("malformed workflow state")
        if state.get("repository") != _identity(self.root):
            raise WorkflowError("workflow belongs to a different repository or checkout")
        return state

    def save(self, state):
        state["revision"] = state.get("revision", 0) + 1
        fd, name = tempfile.mkstemp(prefix=".workflow-", dir=self.directory)
        try:
            with os.fdopen(fd, "w") as stream:
                json.dump(state, stream, indent=2, ensure_ascii=True)
                stream.write("\n")
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(name, self.path)
        finally:
            if os.path.exists(name):
                os.unlink(name)

    def start(self, agreement, hitl=None):
        from .runtime import assert_runtime, pin_runtime, safe_project_path
        from .scaffold import TemplateScaffolder
        with self.locked():
            if self.path.exists():
                raise WorkflowError("workflow already exists; resume its recorded agreement")
            agreement = _validate_agreement(self.root, agreement)
            if _git(self.root, "branch", "--show-current") != agreement["source"]:
                raise WorkflowError("source must be the current branch")
            existing = sorted(path for path in _dirty(self.root) if _inside_scope(path, agreement["scope"]))
            if existing and not agreement["include_existing_changes"]:
                raise WorkflowError("scope contains pre-existing changes; explicitly include them or narrow scope")
            active = TemplateScaffolder._active_work(self.root, _config(self.root))
            if active:
                baseline_path = safe_project_path(self.root, ".forgeflow/runtime.json")
                if not baseline_path.is_file():
                    raise WorkflowError("active work has no executable baseline; preserve its rules and review migration before starting a new workflow")
                assert_runtime(self.root, json.loads(baseline_path.read_text()))
            state = {"schema": 1, "id": self.task_id, "repository": _identity(self.root),
                     "agreement": agreement, "baseline": pin_runtime(self.root),
                     "initial_head": _head(self.root), "initial_changes": existing,
                     "status": "planned", "verification": None, "integration": None,
                     "cleanup": None, "pending": None, "operations": [], "adoptions": [],
                     "hitl": hitl, "checkpoints": {}}
            state["finalization_complete"] = False
            self.save(state)
            return state

    def _assert_runtime(self, state):
        from .runtime import assert_runtime
        assert_runtime(self.root, state["baseline"])

    def _fingerprint(self, state):
        paths = _verification_paths(self.root, state["agreement"])
        return {"content": _content(self.root, state["agreement"]["scope"], paths),
                "verification_paths": paths,
                "environment": _environment(self.root, state["agreement"]),
                "baseline": state["baseline"]["identity"]}

    def _fresh(self, state):
        verification = state.get("verification")
        return bool(verification and verification.get("passed")
                    and verification.get("inputs") == self._fingerprint(state))

    def check(self, summary=None):
        with self.locked():
            state = self.load()
            self._assert_runtime(state)
            _validate_agreement(self.root, state["agreement"])
            if not state.get("integration") and _git(self.root, "branch", "--show-current") != state["agreement"]["source"]:
                raise WorkflowError("current branch differs from the recorded source")
            if state.get("hitl") == "design":
                checkpoint = state.setdefault("checkpoints", {}).setdefault("design", {})
                if checkpoint.get("status") != "approved":
                    checkpoint.update({
                        "status": "awaiting-user",
                        "summary": summary or self._default_design_summary(state),
                        "requested_at": _now(),
                    })
                    state["status"] = "awaiting-user"
                    state["pending"] = {
                        "operation": "checkpoint:design",
                        "reason": "Review the design before implementation, then continue, revise, or stop.",
                    }
                    self.save(state)
                    return state
            return self._report(state)

    def _default_design_summary(self, state):
        agreement = state["agreement"]
        return {
            "scope": agreement.get("scope"),
            "acceptance": agreement.get("acceptance"),
            "plan": agreement.get("plan"),
            "checks": agreement.get("checks"),
            "source": agreement.get("source"),
            "target": agreement.get("target"),
        }

    def _require_design_approval(self, state):
        if state.get("hitl") != "design":
            return
        checkpoint = state.get("checkpoints", {}).get("design", {})
        if checkpoint.get("status") != "approved":
            raise WorkflowError("design checkpoint is awaiting user approval; run workflow continue, revise, or stop")

    def continue_workflow(self, note=None):
        with self.locked():
            state = self.load()
            checkpoint = state.get("checkpoints", {}).get("design", {})
            if state.get("pending", {}).get("operation") != "checkpoint:design":
                raise WorkflowError("no design checkpoint is awaiting a decision")
            checkpoint.update({"status": "approved", "decision": "continue",
                               "note": note, "decided_at": _now()})
            state["status"] = "planned"
            state["pending"] = None
            self.save(state)
            return state

    def revise(self, note=None):
        with self.locked():
            state = self.load()
            checkpoint = state.get("checkpoints", {}).get("design", {})
            if state.get("pending", {}).get("operation") != "checkpoint:design":
                raise WorkflowError("no design checkpoint is awaiting a decision")
            checkpoint.update({"status": "changes-requested", "decision": "revise",
                               "note": note, "decided_at": _now()})
            state["status"] = "planned"
            state["pending"] = None
            self.save(state)
            return state

    def stop(self, note=None):
        with self.locked():
            state = self.load()
            checkpoint = state.get("checkpoints", {}).get("design", {})
            if state.get("pending", {}).get("operation") != "checkpoint:design":
                raise WorkflowError("no design checkpoint is awaiting a decision")
            checkpoint.update({"status": "stopped", "decision": "stop",
                               "note": note, "decided_at": _now()})
            state["status"] = "stopped"
            state["pending"] = None
            self.save(state)
            return state

    def _report(self, state):
        result = copy.deepcopy(state)
        if not state.get("integration") and state.get("verification") and not self._fresh(state):
            result["status"] = "verification-stale"
            result["finalization_complete"] = False
        result["ready"] = self._fresh(state) if not state.get("integration") else True
        return result

    def status(self):
        with self.locked():
            state = self.load()
            try:
                self._assert_runtime(state)
            except (ValueError, OSError, RuntimeError) as exc:
                result = copy.deepcopy(state)
                result.update(status="baseline-drift", ready=False,
                              pending={"operation": "resume-baseline", "reason": str(exc)})
                return result
            return self._report(state)

    def verify(self):
        with self.locked():
            state = self.load()
            self._assert_runtime(state)
            self._require_design_approval(state)
            if state.get("integration"):
                raise WorkflowError("already integrated; resume cleanup instead of reopening verification")
            agreement = state["agreement"]
            if _git(self.root, "branch", "--show-current") != agreement["source"]:
                raise WorkflowError("verify must run in the source checkout")
            checks = required_checks(self.root, agreement)
            if not checks and not agreement.get("verification_note"):
                raise WorkflowError("declare checks or an explicit verification_note for a change requiring no executable checks")
            # Invalidate before execution, so a failed/terminated run cannot
            # leave a previous PASS eligible for finalization.
            state["verification"] = {"passed": False, "results": [], "inputs": None}
            state["status"] = "verifying"
            state["finalization_complete"] = False
            state["pending"] = None
            self.save(state)
            before = self._fingerprint(state)
            timeout = _config(self.root).get("governance", {}).get("test_timeout_seconds", 300)
            if not isinstance(timeout, (int, float)) or isinstance(timeout, bool) or timeout <= 0:
                raise WorkflowError("test_timeout_seconds must be positive")
            for argv in checks:
                started = time.monotonic()
                try:
                    completed = subprocess.run(argv, cwd=self.root, capture_output=True,
                                               timeout=timeout, text=True, errors="replace")
                    result = {"argv": argv, "returncode": completed.returncode,
                              "duration_seconds": round(time.monotonic() - started, 3)}
                    if completed.returncode:
                        result["diagnostic_excerpt"] = _failure_excerpt(completed.stdout, completed.stderr)
                except (OSError, subprocess.TimeoutExpired) as exc:
                    result = {"argv": argv, "returncode": None, "error": type(exc).__name__}
                    if isinstance(exc, subprocess.TimeoutExpired):
                        result["diagnostic_excerpt"] = _failure_excerpt(exc.stdout, exc.stderr)
                    else:
                        result["diagnostic_excerpt"] = str(exc)[:4000]
                state["verification"]["results"].append(result)
                if result["returncode"] != 0:
                    state["status"] = "verification-failed"
                    self.save(state)
                    return state
            after = self._fingerprint(state)
            state["verification"].update(passed=before == after, inputs=after)
            state["status"] = "ready" if before == after else "verification-stale"
            if before != after:
                state["pending"] = {"operation": "verify", "reason": "verification commands changed implementation inputs; review outputs then verify again"}
            self.save(state)
            return state

    def adopt(self, reason, impact):
        from .runtime import pin_runtime
        if not reason.strip() or not impact.strip():
            raise WorkflowError("rule adoption requires reason and reviewed impact")
        with self.locked():
            state = self.load()
            if state.get("integration"):
                raise WorkflowError("integrated tasks retain their baseline; only cleanup remains")
            for other in self.directory.glob("*.json"):
                if other != self.path:
                    validate_relative_path(str(other.relative_to(self.root)), self.root)
                    sibling = json.loads(other.read_text())
                    if sibling.get("finalization_complete") is not True and sibling.get("status") not in {"cleaned", "completed", "cancelled"}:
                        raise WorkflowError("another active workflow shares the project rules; finish or explicitly migrate it before adopting a new project baseline")
            previous = state["baseline"]
            baseline = pin_runtime(self.root)
            state["adoptions"].append({"from": previous["identity"], "to": baseline["identity"],
                                       "reason": reason, "impact": impact})
            state["baseline"] = baseline
            state["finalization_complete"] = False
            if previous["identity"] != baseline["identity"]:
                state["verification"] = None
                state["status"] = "planned"
            self.save(state)
            return state

    def _pending(self, state, operation, reason):
        state["finalization_complete"] = False
        state["pending"] = {"operation": operation, "reason": reason}
        self.save(state)
        return state

    def _commit(self, state):
        agreement = state["agreement"]
        dirty = sorted(path for path in _dirty(self.root) if _inside_scope(path, agreement["scope"]))
        if not dirty:
            return None
        if "commit" not in agreement["permissions"]:
            return self._pending(state, "commit", "task changes need an explicitly authorized commit")
        # --only commits named task paths and preserves unrelated staged work.
        _git(self.root, "add", "--", *dirty)
        _git(self.root, "commit", "--only", "-m", agreement.get("commit_message", f"Complete {self.task_id}"), "--", *dirty)
        state["operations"].append({"operation": "commit", "commit": _head(self.root)})
        self.save(state)
        return None

    def _push(self, state):
        agreement = state["agreement"]
        if "push" not in agreement["permissions"]:
            return
        remote = agreement["remote"]
        if _digest(_git(self.root, "remote", "get-url", remote)) != agreement["remote_identity"]:
            raise WorkflowError("remote identity changed; do not push to a new destination")
        source_sha = _head(self.root, agreement["source"])
        pushed = next((event for event in reversed(state["operations"]) if event["operation"] == "push"), None)
        if pushed and pushed["commit"] == source_sha:
            return
        _git(self.root, "push", remote, f"{source_sha}:refs/heads/{agreement['source']}")
        observed = _git(self.root, "ls-remote", "--heads", remote, "refs/heads/" + agreement["source"])
        if not observed or observed.split()[0] != source_sha:
            raise WorkflowError("push completed but remote branch identity could not be confirmed")
        state["operations"].append({"operation": "push", "commit": source_sha, "remote": remote})
        self.save(state)
        if _head(self.root, agreement["source"]) != source_sha:
            raise WorkflowError("source branch changed during push; accepted commit was pushed, verify the new source before integration")

    def _recover_integration(self, state):
        intent = state.get("merge_intent")
        if not intent or state.get("integration"):
            return
        agreement = state["agreement"]
        target_sha = _head(self.root, agreement["target"])
        if _ancestor(self.root, intent["source_commit"], target_sha):
            if _git(self.root, "diff", "--quiet", intent["source_commit"], target_sha, "--", check=False).returncode:
                raise WorkflowError("observed target contains additional unverified changes; reconcile verification before recovering integration")
            state["integration"] = {**intent, "target_commit": target_sha, "recovered": True}
            state["status"] = "integrated"
            state["pending"] = None
            self.save(state)

    def _merge(self, state):
        agreement = state["agreement"]
        if "merge" not in agreement["permissions"]:
            return self._pending(state, "merge", "readiness does not authorize integration")
        if agreement["integration"] == "pr":
            return self._pending(state, "merge", "PR integration is delegated to the selected host; provide an observed integration receipt")
        source_sha = _head(self.root, agreement["source"])
        target_sha = _head(self.root, agreement["target"])
        # Fast-forward-only integration guarantees the tested source is the
        # exact integrated tree; target divergence needs an explicit reconcile.
        if not _ancestor(self.root, target_sha, source_sha):
            return self._pending(state, "reconcile", "target diverged; reconcile on source and run affected verification")
        changed = _assert_scope_diff(self.root, agreement, source_sha, target_sha)
        dirty = _dirty(self.root)
        if any(path in dirty for path in changed if path):
            raise WorkflowError("dirty changes overlap the integration result; preserve them and resolve ownership first")
        state["merge_intent"] = {"source_commit": source_sha, "target_before": target_sha,
                                 "source": agreement["source"], "target": agreement["target"]}
        self.save(state)
        try:
            _git(self.root, "switch", agreement["target"])
            if _head(self.root, agreement["source"]) != source_sha:
                raise WorkflowError("source branch moved immediately before merge; verify the new source")
            _git(self.root, "merge", "--ff-only", "--", source_sha)
        except WorkflowError as exc:
            self._recover_integration(state)
            if state.get("integration"):
                return None
            if _git(self.root, "branch", "--show-current") == agreement["target"]:
                try:
                    _git(self.root, "switch", agreement["source"])
                except WorkflowError:
                    return self._pending(state, "resume-source", f"{exc}; restore source checkout {agreement['source']} with its owner before resuming")
            operation = "verify" if _head(self.root, agreement["source"]) != source_sha else "merge"
            return self._pending(state, operation, str(exc))
        self._recover_integration(state)
        if not state.get("integration"):
            raise WorkflowError("merge result did not contain the accepted source")
        return None

    def _cleanup(self, state):
        agreement = state["agreement"]
        target_sha = _head(self.root, agreement["target"])
        if not _ancestor(self.root, state["integration"]["source_commit"], target_sha):
            return self._pending(state, "verify-integration", "target no longer contains the accepted source; preserve the task branch and restore integration before cleanup")
        if "delete-branch" not in agreement["permissions"]:
            state["cleanup"] = {"status": "not-requested"}
            state["pending"] = None
            state["finalization_complete"] = True
            self.save(state)
            return state
        if not agreement["task_owned_branch"]:
            return self._pending(state, "delete-branch", "branch ownership is not delegated")
        source = agreement["source"]
        exists = _git(self.root, "show-ref", "--verify", "--quiet", "refs/heads/" + source, check=False).returncode == 0
        if exists:
            if _head(self.root, source) != state["integration"]["source_commit"]:
                return self._pending(state, "delete-branch", "source branch changed after integration")
            _git(self.root, "branch", "-d", "--", source)
        state["cleanup"] = {"status": "cleaned", "branch": source}
        state["status"] = "cleaned"
        state["pending"] = None
        state["finalization_complete"] = True
        self.save(state)
        return state

    def _host(self, state, receipt):
        agreement = state["agreement"]
        permissions = agreement["permissions"]
        if state.get("integration") and not _ancestor(self.root, state["integration"]["source_commit"], _head(self.root, agreement["target"])):
            return self._pending(state, "verify-integration", "target no longer contains the accepted source; preserve task-owned artifacts before cleanup")
        if receipt is not None:
            if not isinstance(receipt, dict) or not receipt.get("tool") or not receipt.get("evidence"):
                raise WorkflowError("host receipt needs owning tool and concrete execution evidence")
            if receipt.get("repository") != str(self.root) or receipt.get("source") != agreement["source"]:
                raise WorkflowError("host receipt repository/source identity mismatch")
            operation = receipt.get("operation")
            if operation not in permissions:
                raise WorkflowError("host receipt operation was not delegated")
            if operation == "merge":
                if agreement["integration"] == "none" or receipt.get("target") != agreement.get("target"):
                    raise WorkflowError("host receipt target was not delegated")
                source_sha = receipt.get("source_commit")
                if not state.get("host_source_commit") or source_sha != state["host_source_commit"]:
                    raise WorkflowError("host integration source differs from verified source")
                intent = state.get("host_merge_intent")
                if not intent or intent.get("source_commit") != source_sha:
                    raise WorkflowError("host integration has no matching reviewed source/target intent")
                _assert_scope_diff(self.root, agreement, source_sha, intent["target_before"])
                target_sha = _head(self.root, agreement["target"])
                if not _ancestor(self.root, source_sha, target_sha):
                    raise WorkflowError("target does not contain accepted source; merge receipt is unverified")
                if _git(self.root, "diff", "--quiet", source_sha, target_sha, "--", check=False).returncode:
                    raise WorkflowError("host integrated tree differs from verified source; verify the reconciled source first")
                state["integration"] = {"source_commit": source_sha, "target_commit": target_sha,
                                         "source": agreement["source"], "target": agreement["target"], "receipt": receipt}
                state["status"] = "integrated"
            elif operation == "delete-branch":
                if not state.get("integration") or not agreement["task_owned_branch"]:
                    raise WorkflowError("cleanup requires integration and task-owned branch")
                if _git(self.root, "show-ref", "--verify", "--quiet", "refs/heads/" + agreement["source"], check=False).returncode == 0:
                    raise WorkflowError("host branch cleanup is not observed")
                state["cleanup"] = {"status": "cleaned", "receipt": receipt}
                state["status"] = "cleaned"
            else:
                raise WorkflowError("this host receipt cannot be independently observed; keep the operation pending")
            self.save(state)
        if state.get("integration"):
            if (state.get("cleanup") or {}).get("status") == "cleaned":
                state["pending"] = None
                state["finalization_complete"] = True
                self.save(state)
                return state
            if "host-cleanup" in permissions:
                return self._pending(state, "host-cleanup", "archive the host-owned checkout with its owning tool; record its outcome outside the removed checkout")
            if "delete-branch" in permissions:
                return self._pending(state, "delete-branch", "use the owning host tool and provide an observed cleanup receipt")
            state["cleanup"] = {"status": "not-requested"}
            state["pending"] = None
            state["finalization_complete"] = True
            self.save(state)
            return state
        related = [path for path in _dirty(self.root) if _inside_scope(path, agreement["scope"])]
        if related:
            reason = ("use the owning host to commit the accepted task paths, then finalize again"
                      if "commit" in permissions else "committing task changes has not been delegated")
            return self._pending(state, "commit", reason)
        if "push" in permissions:
            remote = agreement["remote"]
            if _digest(_git(self.root, "remote", "get-url", remote)) != agreement["remote_identity"]:
                raise WorkflowError("remote identity changed; do not publish to another destination")
            source_sha = _head(self.root, agreement["source"])
            observed = _git(self.root, "ls-remote", "--heads", remote, "refs/heads/" + agreement["source"])
            if not observed or observed.split()[0] != source_sha:
                return self._pending(state, "push", "publish the accepted source using the owning host, then finalize again")
        if agreement["integration"] == "none":
            if "host-cleanup" in permissions:
                return self._pending(state, "host-cleanup", "archive with the owning host and record the final outcome outside this checkout")
            state.update(status="ready", pending=None, finalization_complete=True)
            self.save(state)
            return state
        if "merge" not in permissions:
            return self._pending(state, "merge", "readiness does not authorize integration")
        source_sha = _head(self.root, agreement["source"])
        target_sha = _head(self.root, agreement["target"])
        _assert_scope_diff(self.root, agreement, source_sha, target_sha)
        state["host_source_commit"] = source_sha
        state["host_merge_intent"] = {"source_commit": source_sha, "target_before": target_sha}
        return self._pending(state, "merge", "integrate with the owning host and provide the observed source/target receipt")

    def finalize(self, receipt=None):
        with self.locked():
            state = self.load()
            self._assert_runtime(state)
            self._require_design_approval(state)
            _assert_owner(self.root, state["agreement"])
            self._recover_integration(state)
            if state.get("integration"):
                return self._host(state, receipt) if state["agreement"]["owner"] == "host" else self._cleanup(state)
            if not self._fresh(state):
                return self._pending(state, "verify", "required verification is missing, failed or stale")
            agreement = state["agreement"]
            dependencies = _undelivered_dependencies(self.root, agreement)
            if dependencies:
                return self._pending(state, "verify-committed-inputs", "verified dependencies outside task scope are not committed in the accepted source: " + ", ".join(dependencies) + ". Preserve them; declare genuinely unrelated inputs or verify an independently prepared committed result")
            if agreement["owner"] == "host":
                return self._host(state, receipt)
            if _git(self.root, "branch", "--show-current") != agreement["source"]:
                raise WorkflowError("finalization must start on the recorded source branch")
            pending = self._commit(state)
            if pending:
                return pending
            if not self._fresh(state):
                return self._pending(state, "verify", "commit hooks changed verification inputs; verify the committed result before publishing")
            self._push(state)
            if not self._fresh(state):
                return self._pending(state, "verify", "implementation inputs changed during publication")
            if agreement["integration"] == "none":
                state["pending"] = None
                state["status"] = "ready"
                state["finalization_complete"] = True
                self.save(state)
                return state
            pending = self._merge(state)
            if pending:
                return pending
            return self._cleanup(state)


def add_parser(subparsers):
    parser = subparsers.add_parser("workflow", help="Plan, verify and finalize a lean development task")
    commands = parser.add_subparsers(dest="workflow_command", required=True)
    for name in ("start", "status", "check", "verify", "finalize", "adopt", "continue", "revise", "stop"):
        command = commands.add_parser(name)
        command.add_argument("task_id")
        command.add_argument("--repo-root", default=None)
        command.add_argument("--json", action="store_true")
        if name == "start":
            command.add_argument("--agreement", required=True, help="JSON plan, scope, checks, owner and delegated permissions")
            command.add_argument("--hitl", choices=["design"], default=None,
                                 help="Pause at the design checkpoint for user review")
        if name == "check":
            command.add_argument("--summary", default=None, help="Design review summary shown to the user")
        if name in {"continue", "revise", "stop"}:
            command.add_argument("--note", default=None)
        if name == "finalize":
            command.add_argument("--receipt", help="Host execution receipt JSON file")
        if name == "adopt":
            command.add_argument("--reason", required=True)
            command.add_argument("--impact", required=True, help="Reviewed effect of explicitly changing rules")
    return parser


def handle_command(parsed):
    try:
        root = Path(parsed.repo_root).resolve() if parsed.repo_root else Path(_git(Path.cwd(), "rev-parse", "--show-toplevel")).resolve()
        workflow = Workflow(root, parsed.task_id)
        command = parsed.workflow_command
        if command == "start":
            state = workflow.start(json.loads(Path(parsed.agreement).read_text()), hitl=parsed.hitl)
        elif command == "adopt":
            state = workflow.adopt(parsed.reason, parsed.impact)
        elif command == "finalize":
            receipt = json.loads(Path(parsed.receipt).read_text()) if parsed.receipt else None
            state = workflow.finalize(receipt)
        elif command == "check":
            state = workflow.check(summary=parsed.summary)
        elif command == "continue":
            state = workflow.continue_workflow(parsed.note)
        elif command == "revise":
            state = workflow.revise(parsed.note)
        elif command == "stop":
            state = workflow.stop(parsed.note)
        else:
            state = getattr(workflow, command)()
        if parsed.json:
            print(json.dumps(state, indent=2, ensure_ascii=True))
        else:
            print(f"{state['id']}: {state['status']}")
            if state.get("checkpoints", {}).get("design"):
                design = state["checkpoints"]["design"]
                print(f"Design checkpoint: {design.get('status')}")
            if state.get("pending"):
                print(f"Next: {state['pending']['operation']} — {state['pending']['reason']}")
        if state.get("status") == "awaiting-user":
            return 3
        if state.get("status") == "stopped":
            return 0
        return 1 if state.get("status") in {"verification-failed", "verification-stale"} or state.get("pending") else 0
    except (WorkflowError, ValueError, OSError) as exc:
        if parsed.json:
            print(json.dumps({"status": "blocked", "reason": str(exc)}))
        else:
            print(f"Workflow blocked: {exc}", file=sys.stderr)
        return 1
