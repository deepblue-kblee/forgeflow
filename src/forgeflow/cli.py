#!/usr/bin/env python3
"""
ForgeFlow & Harness Unified CLI Entrypoints
"""

import argparse
import json
import sys
from pathlib import Path

from . import __version__
from .harness import HarnessEngine, LifecycleError
from .lifecycle import (
    LifecycleError as CoreLifecycleError,
    TransitionError,
    ValidationError as LifecycleValidationError,
    CASConflict,
)
from .renderer import ReportRenderer
from .reviewer import ReviewEngine
from .scaffold import TemplateScaffolder
from .scanner import HierarchicalRootScanner, ReleaseScanner
from .validator import TierRules
from .validator import SelfGovernanceValidator
from .update import apply as apply_update, inspect as inspect_update


def parse_harness_args(args=None):
    if args is None:
        raw_args = list(sys.argv[1:])
    else:
        raw_args = list(args)

    cleaned_args = []
    has_action = None
    for a in raw_args:
        if a in ("check", "review") and has_action is None and not a.startswith("-"):
            has_action = a
            continue
        cleaned_args.append(a)

    action = has_action or "check"

    parser = argparse.ArgumentParser(
        prog="harness",
        description="ForgeFlow Harness Gate & Quality Audit CLI",
    )
    parser.add_argument(
        "target",
        nargs="*",
        default=None,
        help="Target release path, files, or ID to check/review",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Audit/Review all releases or source files",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Enforce 100%% pass on tests and zero smells",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output machine-readable JSON report",
    )
    parser.add_argument(
        "--base",
        type=str,
        default=None,
        help="Base git ref for diff in review mode",
    )
    parser.add_argument(
        "--spec",
        type=str,
        default=None,
        help="Explicit spec file path",
    )
    parser.add_argument(
        "--report",
        type=str,
        default=None,
        help="Custom markdown report output path",
    )
    parser.add_argument(
        "--fail-on-warning",
        action="store_true",
        help="Fail review if any warning smells are found",
    )
    parser.add_argument(
        "--no-cache",
        action="store_true",
        help="Disable incremental AST checkpoint cache in review",
    )
    parser.add_argument(
        "--python",
        type=str,
        default=None,
        help="Explicit python interpreter for running tests",
    )
    parser.add_argument(
        "--repo-root",
        type=str,
        default=None,
        help="Explicit target repository root directory",
    )
    parser.add_argument("--self-governance", action="store_true", help="Audit ForgeFlow repository-local spec coverage")
    parser.add_argument("--lifecycle", type=str, help="Read-only evidence audit for one release ID")
    parser.add_argument("--release-id", type=str, help="Release ID required by --self-governance")
    parsed = parser.parse_args(cleaned_args)
    setattr(parsed, "_action", action)
    return parsed


def harness_main(args=None):
    if args is None and len(sys.argv) > 1 and sys.argv[1] == "version":
        print(f"ForgeFlow Harness Gate CLI v{__version__}")
        sys.exit(0)
    elif args and len(args) > 0 and args[0] == "version":
        print(f"ForgeFlow Harness Gate CLI v{__version__}")
        sys.exit(0)

    parsed = parse_harness_args(args)
    root_path = Path(parsed.repo_root).resolve() if parsed.repo_root else HierarchicalRootScanner.find_root()

    if getattr(parsed, "_action", "check") == "review":
        rev_engine = ReviewEngine(repo_root=root_path)
        targets = [Path(t) for t in parsed.target] if parsed.target else None
        res = rev_engine.run_review(
            targets=targets,
            all_files=parsed.all,
            base_ref=parsed.base,
            explicit_spec=parsed.spec,
            strict=parsed.strict,
            fail_on_warning=getattr(parsed, "fail_on_warning", False),
            no_cache=getattr(parsed, "no_cache", False),
            report_dest=Path(parsed.report) if parsed.report else None,
        )
        if parsed.json:
            print(ReportRenderer.render_json_review(res))
        else:
            print(ReportRenderer.render_terminal_review(res))
        sys.exit(0 if res.passed else 1)

    # Action: check
    if parsed.lifecycle:
        engine = HarnessEngine(repo_root=root_path)
        result = engine.check_lifecycle_evidence(
            parsed.lifecycle,
            strict=parsed.strict,
            explicit_python=parsed.python,
        )
        rendered = json.dumps(result, ensure_ascii=False, sort_keys=True) if parsed.json else json.dumps(result, ensure_ascii=False, indent=2)
        print(rendered)
        sys.exit(0 if result["ok"] else 1)
    if parsed.self_governance:
        passed, messages = SelfGovernanceValidator.validate(root_path, parsed.release_id, parsed.base)
        for message in messages:
            print(("🟢 " if passed else "🔴 ") + message)
        sys.exit(0 if passed else 1)
    engine = HarnessEngine(repo_root=root_path)
    results = []
    target_arg = parsed.target[0] if parsed.target else None

    if parsed.all:
        results = engine.check_all_releases(strict=parsed.strict, explicit_python=parsed.python)
    elif target_arg:
        target_path = Path(target_arg)
        if not target_path.is_absolute():
            rel_candidate = root_path / "docs" / "releases" / target_arg
            if rel_candidate.exists():
                target_path = rel_candidate
            else:
                target_path = (root_path / target_arg).resolve()

        if not target_path.exists():
            print(f"❌ Error: Release path '{target_path}' does not exist.", file=sys.stderr)
            sys.exit(2)

        r = engine.check_release(target_path, strict=parsed.strict, explicit_python=parsed.python)
        results = [r]
    else:
        latest = engine.check_latest_release(strict=parsed.strict, explicit_python=parsed.python)
        if not latest:
            print("⚠️ No release directories found under tasks/ or docs/releases/.", file=sys.stderr)
            sys.exit(1)
        results = [latest]

    if parsed.json:
        print(ReportRenderer.render_json_report(results))
    else:
        print(ReportRenderer.render_terminal_report(results))

    all_passed = all(r.passed for r in results) if results else True
    sys.exit(0 if all_passed else 1)


def parse_forgeflow_args(args=None):
    if args is None:
        raw_args = list(sys.argv[1:])
    else:
        raw_args = list(args)

    if raw_args and raw_args[0] == "issue":
        from .issue import normalize_issue_args
        raw_args = ["issue"] + normalize_issue_args(raw_args[1:])

    parser = argparse.ArgumentParser(
        prog="forgeflow",
        description="ForgeFlow: Autonomous Agent Governance & Review CLI",
    )
    parser.add_argument(
        "-v", "--version", action="version", version=f"ForgeFlow v{__version__} (Autonomous Agent Governance Framework)"
    )
    subparsers = parser.add_subparsers(dest="command", help="ForgeFlow Commands")

    # Command: init
    init_parser = subparsers.add_parser("init", help="Initialize project governance or release scaffold")
    init_parser.add_argument("target", nargs="?", default=None, help="Target release ID or project name (optional)")
    init_parser.add_argument("--project", type=str, default=None, help="New project directory / slug to initialize")
    init_parser.add_argument(
        "--tier", type=int, default=2, choices=[1, 2, 3], help="Risk Tier for release scaffolding (1=Minor, 2=Standard, 3=Critical)"
    )
    init_parser.add_argument("--speckit", "--hybrid", action="store_true", dest="speckit", help="Initialize lightweight GitHub Spec Kit & ForgeFlow hybrid environment")
    init_parser.add_argument("--template", type=str, default=None, help="Custom template directory path")
    init_parser.add_argument("--force", action="store_true", help="Force reinstall the complete governance bundle or overwrite release files")
    init_parser.add_argument("--continuation-policy", choices=["interactive", "autonomous"], default="interactive", help="Selectable human-in-the-loop or autonomous continuation capability")
    init_parser.add_argument("--migrate-continuation-policy", action="store_true", help="Add the continuation policy without replacing unrelated configuration")
    init_parser.add_argument("--refresh-governance", action="store_true", help="Refresh central governance guide and retain a backup")
    init_parser.add_argument(
        "--migrate-governance-binding",
        action="store_true",
        help="Replace the exact legacy ForgeFlow root-guide binding with the central-guide binding",
    )
    init_parser.add_argument("--json", action="store_true", help="Output machine-readable JSON")
    init_parser.add_argument("--path", type=str, default=None, help="Target directory (legacy alias / explicit path)")

    # Command: release
    rel_parser = subparsers.add_parser("release", help="Manage release specifications")
    rel_sub = rel_parser.add_subparsers(dest="release_command")
    rel_create = rel_sub.add_parser("create", help="Create a new release boilerplate")
    rel_create.add_argument("release_id", help="Release identifier (e.g. v0.1.0-feature)")
    rel_create.add_argument(
        "--tier", type=int, default=2, choices=[1, 2, 3], help="Risk Tier (1=Minor, 2=Standard, 3=Critical)"
    )

    # Command: check
    check_parser = subparsers.add_parser("check", help="Run ForgeFlow governance gate audit", description="Run ForgeFlow governance gate audit")
    check_parser.add_argument("target", nargs="*", default=None)
    check_parser.add_argument("--stage", type=int, default=None, help="Check specific gate stage (e.g. 2 for Gate 1 pre-implementation check)")
    check_parser.add_argument("--quiet", action="store_true", help="Suppress non-error output")
    check_parser.add_argument("--all", action="store_true")
    check_parser.add_argument("--strict", action="store_true")
    check_parser.add_argument("--json", action="store_true")
    check_parser.add_argument("--repo-root", type=str, default=None)
    check_parser.add_argument("--lifecycle", type=str, default=None)
    check_parser.add_argument("--self-governance", action="store_true", help="Audit ForgeFlow repository-local spec coverage")
    check_parser.add_argument("--release-id", type=str, default=None, help="Release ID required by --self-governance")
    check_parser.add_argument("--base", type=str, default=None, help="Base git ref for diff")
    check_parser.add_argument("--python", type=str, default=None, help="Explicit python interpreter for running tests")

    # Command: lifecycle
    lifecycle_parser = subparsers.add_parser("lifecycle", help="Manage durable lifecycle state")
    lifecycle_sub = lifecycle_parser.add_subparsers(dest="lifecycle_command", required=True)

    def add_lifecycle_common(parser):
        parser.add_argument("release_id", help="Release identifier")
        parser.add_argument("--repo-root", type=str, default=None, help="Explicit target repository root")
        parser.add_argument("--json", action="store_true", help="Output machine-readable JSON")

    start_parser = lifecycle_sub.add_parser("start", help="Create a lifecycle state")
    add_lifecycle_common(start_parser)
    start_parser.add_argument("--policy", "--continuation-policy", dest="policy", choices=["interactive", "autonomous"], default="interactive")
    start_parser.add_argument("--target", choices=["design-only", "qa-signoff", "full", "current-stage"], default="full")
    start_parser.add_argument("--attestation", "--activation-attestation", dest="attestation", default=None, help="Activation attestation JSON object")

    status_parser = lifecycle_sub.add_parser("status", help="Read lifecycle state")
    add_lifecycle_common(status_parser)

    advance_parser = lifecycle_sub.add_parser("advance", help="Advance lifecycle state")
    add_lifecycle_common(advance_parser)
    advance_parser.add_argument("--stage", default=None)
    advance_parser.add_argument("--status", choices=["ACTIVE", "WAITING_INTERNAL"], default=None)
    advance_parser.add_argument("--action", default=None)
    advance_parser.add_argument("--checkpoint", choices=["C0", "D1", "C1", "C2", "C3", "C4"], default=None)
    advance_parser.add_argument("--worker", default=None)
    advance_parser.add_argument("--invocation-id", default=None)
    advance_parser.add_argument("--attempt-id", default=None)
    advance_parser.add_argument("--candidate-sha", default=None)

    attempt_parser = lifecycle_sub.add_parser("record-attempt", help="Record a worker attempt")
    add_lifecycle_common(attempt_parser)
    attempt_parser.add_argument("--attempt-id", required=True)
    attempt_parser.add_argument("--result", choices=["progress", "no-progress", "passed", "success", "pass", "failed", "failure", "fail", "duplicate", "timeout"], required=True)
    attempt_parser.add_argument("--stage-loop-fingerprint", default=None)
    attempt_parser.add_argument("--worker", default=None)

    resume_parser = lifecycle_sub.add_parser("resume", help="Resume a paused lifecycle")
    add_lifecycle_common(resume_parser)
    resume_parser.add_argument("--policy", "--continuation-policy", dest="policy", choices=["interactive", "autonomous"], required=True)
    resume_parser.add_argument("--target", choices=["design-only", "full", "current-stage"], default=None)
    resume_parser.add_argument("--attestation", "--activation-attestation", dest="attestation", default=None)

    complete_parser = lifecycle_sub.add_parser("complete", help="Complete lifecycle after all guards pass")
    add_lifecycle_common(complete_parser)
    complete_parser.add_argument("--python", type=str, default=None, help="Explicit python interpreter for strict tests")

    package_review_parser = lifecycle_sub.add_parser("package-review", help="Enter PACKAGE_REVIEW_PENDING after approved QA Sign-off")
    add_lifecycle_common(package_review_parser)
    package_review_parser.add_argument("qa_sha_pos", nargs="?", default=None, help="QA commit SHA (positional)")
    package_review_parser.add_argument("--qa-sha", default=None, help="QA commit SHA (flag)")

    seal_parser = lifecycle_sub.add_parser("seal", help="Seal a Gate 3-approved release candidate")
    add_lifecycle_common(seal_parser)
    seal_parser.add_argument("candidate_sha_pos", nargs="?", default=None, help="Release candidate commit SHA (positional)")
    seal_parser.add_argument("--release-candidate-sha", default=None, help="Release candidate commit SHA (flag)")

    close_parser = lifecycle_sub.add_parser("close", help="Close a completed release and clean up task branch on main")
    add_lifecycle_common(close_parser)

    remediate_parser = lifecycle_sub.add_parser("remediate", help="Record or resolve remediations in the loop record")
    add_lifecycle_common(remediate_parser)
    remediate_parser.add_argument("--verdict", choices=["REJECT", "FAIL", "PASS", "APPROVED"], default="REJECT")
    remediate_parser.add_argument("--finding", default=None, help="Remediation finding or description")
    remediate_parser.add_argument("--fingerprint", default=None, help="Optional failure fingerprint")
    remediate_parser.add_argument("--resolve", action="store_true", help="Mark remediations as resolved")
    remediate_parser.add_argument("--remediation-id", default=None, help="Specific remediation ID to resolve")
    remediate_parser.add_argument("--candidate-sha", default=None, help="Candidate SHA for resolution")

    # Command: review
    rev_parser = subparsers.add_parser("review", help="Run AST code smell detection and 2-axis review")
    rev_parser.add_argument("target", nargs="*", default=None, help="Target files or directories")
    rev_parser.add_argument("--all", action="store_true", help="Review all source files")
    rev_parser.add_argument("--base", type=str, default=None, help="Base git ref for diff")
    rev_parser.add_argument("--spec", type=str, default=None, help="Explicit spec file path")
    rev_parser.add_argument("--strict", action="store_true", help="Fail on warning smells")
    rev_parser.add_argument("--fail-on-warning", action="store_true", help="Fail if any warning smells are found")
    rev_parser.add_argument("--no-cache", action="store_true", help="Disable incremental AST checkpoint cache")
    rev_parser.add_argument("--json", action="store_true", help="Output JSON report")
    rev_parser.add_argument("--report", type=str, default=None, help="Custom markdown report output path")
    rev_parser.add_argument("--repo-root", type=str, default=None, help="Explicit repository root")

    # Command: version
    subparsers.add_parser("version", help="Show ForgeFlow version")

    update_parser = subparsers.add_parser("update", help="Preview a local governance bundle update")
    update_parser.add_argument("--path", default=None, help="Target project directory")
    update_parser.add_argument("--apply", action="store_true", help="Reserved: explicit update apply")
    update_parser.add_argument("--json", action="store_true", help="Output JSON result")
    # Command: migrate
    migrate_parser = subparsers.add_parser("migrate", help="Migrate legacy release structures to tasks architecture")
    migrate_parser.add_argument("--tasks", action="store_true", help="Migrate legacy docs/releases/ to root tasks/completed/")
    migrate_parser.add_argument("--target", default="tasks", help="Target tasks directory name (default: tasks, fallback: ff-tasks)")
    migrate_parser.add_argument("--repo-root", default=None, help="Explicit repository root")

    # Command: task
    task_parser = subparsers.add_parser("task", help="Manage task packages (tasks/ architecture)")
    task_sub = task_parser.add_subparsers(dest="task_command")
    task_create = task_sub.add_parser("create", help="Create a new task package")
    task_create.add_argument("task_id", help="Task ID (e.g. task-001 or v1.0.0)")
    task_create.add_argument("--tier", type=int, choices=[1, 2, 3], default=2, help="Governance tier (default: 2)")
    task_create.add_argument("--stage", choices=["backlog", "in-progress"], default="in-progress", help="Target stage folder (default: in-progress)")

    # Command: status
    subparsers.add_parser("status", help="Show current project governance status")

    # Command: doctor
    doctor_parser = subparsers.add_parser("doctor", aliases=["diagnose"], help="Run ForgeFlow diagnostic health check")
    doctor_parser.add_argument("--json", action="store_true", help="Output machine-readable JSON report")
    doctor_parser.add_argument("--report-issue", action="store_true", help="Generate structured GitHub Issue draft from diagnostics")
    doctor_parser.add_argument("--clear", action="store_true", help="Clear local diagnostic event logs")

    # Command: issue
    issue_common = argparse.ArgumentParser(add_help=False)
    issue_common.add_argument("--repo", default=None, help="Target GitHub repository (default: detected from git)")
    issue_common.add_argument("--json", action="store_true", help="Output machine-readable JSON")

    issue_parser = subparsers.add_parser(
        "issue",
        parents=[issue_common],
        help="Manage GitHub issues with local caching",
    )
    issue_sub = issue_parser.add_subparsers(dest="issue_command", help="Issue subcommands")

    # issue create
    create_p = issue_sub.add_parser("create", parents=[issue_common], help="Create a new GitHub issue")
    create_p.add_argument("--title", required=True, help="Issue title")
    body_grp = create_p.add_mutually_exclusive_group(required=True)
    body_grp.add_argument("--body", help="Issue body/description")
    body_grp.add_argument("--body-file", "-F", type=Path, help="File path containing issue body")
    create_p.add_argument("--label", action="append", dest="labels", help="Label to apply (can be repeated)")

    # issue list
    list_p = issue_sub.add_parser("list", parents=[issue_common], help="List issues (cached by default)")
    list_p.add_argument("--state", choices=["open", "closed", "all"], default="open", help="Issue state")
    list_p.add_argument("--refresh", action="store_true", help="Force refresh from GitHub")

    # issue view
    view_p = issue_sub.add_parser("view", parents=[issue_common], help="View issue details")
    view_p.add_argument("number", type=int, help="Issue number")
    view_p.add_argument("--refresh", action="store_true", help="Force refresh from GitHub")

    # issue edit
    edit_p = issue_sub.add_parser("edit", parents=[issue_common], help="Edit an issue")
    edit_p.add_argument("number", type=int, help="Issue number")
    edit_p.add_argument("--title", help="New issue title")
    edit_p.add_argument("--body", help="New issue body")
    edit_p.add_argument("--body-file", "-F", type=Path, help="File path containing new issue body")
    edit_p.add_argument("--add-label", action="append", dest="add_labels", help="Label to add")
    edit_p.add_argument("--remove-label", action="append", dest="remove_labels", help="Label to remove")

    # issue close
    close_p = issue_sub.add_parser("close", parents=[issue_common], help="Close an issue")
    close_p.add_argument("number", type=int, help="Issue number")
    close_p.add_argument("--comment", help="Closing comment")

    # issue delete
    del_p = issue_sub.add_parser("delete", parents=[issue_common], help="Delete an issue permanently")
    del_p.add_argument("number", type=int, help="Issue number")
    del_p.add_argument("--yes", action="store_true", help="Confirm deletion without prompt")

    return parser.parse_args(raw_args)


def _parse_activation_attestation(value):
    if value is None:
        return None
    try:
        parsed = json.loads(value)
    except (TypeError, json.JSONDecodeError) as exc:
        raise LifecycleError("malformed_attestation", "activation attestation must be a JSON object") from exc
    if not isinstance(parsed, dict):
        raise LifecycleError("malformed_attestation", "activation attestation must be a JSON object")
    return parsed


def _run_lifecycle_command(parsed):
    root_path = Path(parsed.repo_root).resolve() if parsed.repo_root else HierarchicalRootScanner.find_root()
    engine = HarnessEngine(repo_root=root_path)
    command = parsed.lifecycle_command
    try:
        if command == "start":
            result = engine.lifecycle_start(
                parsed.release_id,
                policy=parsed.policy,
                target=parsed.target,
                attestation=_parse_activation_attestation(parsed.attestation),
            )
        elif command == "status":
            result = engine.lifecycle_status(parsed.release_id)
        elif command == "advance":
            result = engine.lifecycle_advance(
                parsed.release_id,
                stage=parsed.stage,
                status=parsed.status,
                action=parsed.action,
                checkpoint=parsed.checkpoint,
                worker=parsed.worker,
                invocation_id=parsed.invocation_id,
                attempt_id=parsed.attempt_id,
                candidate_sha=parsed.candidate_sha,
            )
        elif command == "record-attempt":
            result = engine.lifecycle_record_attempt(
                parsed.release_id,
                result=parsed.result,
                attempt_id=parsed.attempt_id,
                stage_loop_fingerprint=parsed.stage_loop_fingerprint,
                worker=parsed.worker,
            )
        elif command == "resume":
            result = engine.lifecycle_resume(
                parsed.release_id,
                policy=parsed.policy,
                target=parsed.target,
                attestation=_parse_activation_attestation(parsed.attestation),
            )
        elif command == "complete":
            result = engine.lifecycle_complete(parsed.release_id, explicit_python=parsed.python)
        elif command == "package-review":
            qa_sha = parsed.qa_sha or getattr(parsed, "qa_sha_pos", None)
            if not qa_sha:
                raise LifecycleError("missing_qa_sha", "QA SHA is required (provide as positional argument or --qa-sha)")
            result = engine.lifecycle_package_review(parsed.release_id, qa_sha)
        elif command == "seal":
            candidate_sha = parsed.release_candidate_sha or getattr(parsed, "candidate_sha_pos", None)
            if not candidate_sha:
                raise LifecycleError("missing_candidate_sha", "Release candidate SHA is required (provide as positional argument or --release-candidate-sha)")
            result = engine.lifecycle_seal(parsed.release_id, candidate_sha)
        elif command == "close":
            result = engine.lifecycle_close(parsed.release_id)
        elif command == "remediate":
            controller = engine._core_controller(parsed.release_id)
            if parsed.resolve:
                res = controller.resolve_remediation(parsed.remediation_id, candidate_sha=parsed.candidate_sha)
            else:
                findings = [{"description": parsed.finding}] if parsed.finding else []
                fp = parsed.fingerprint or (HarnessEngine.compute_failure_fingerprint(parsed.finding) if parsed.finding else None)
                res = controller.record_remediation(findings, verdict=parsed.verdict, failure_fingerprint=fp)
            result = engine._core_status_payload(res)
        else:
            raise LifecycleError("unknown_lifecycle_command", "unsupported lifecycle command")
    except LifecycleError as exc:
        result = {
            "schema_version": 2,
            "release_id": getattr(parsed, "release_id", None),
            "ok": False,
            "error": exc.code,
            "message": exc.message,
            "unmet_conditions": [exc.code],
            "next_action": exc.message,
        }
        if getattr(parsed, "json", False) or command != "close":
            print(json.dumps(result, ensure_ascii=False, sort_keys=True))
        else:
            print(f"❌ Error: {exc.message} ({exc.code})", file=sys.stderr)
        sys.exit(2)
    except (TransitionError, LifecycleValidationError, CASConflict, CoreLifecycleError) as exc:
        err_code = getattr(exc, "code", exc.__class__.__name__)
        err_msg = str(exc)
        result = {
            "schema_version": 1,
            "release_id": getattr(parsed, "release_id", None),
            "ok": False,
            "error": err_code,
            "message": err_msg,
            "unmet_conditions": [err_code],
            "next_action": err_msg,
        }
        print(json.dumps(result, ensure_ascii=False, sort_keys=True))
        sys.exit(2)
    if "unmet_conditions" in result:
        result["ok"] = not bool(result["unmet_conditions"])
    if command == "close" and not getattr(parsed, "json", False):
        if result.get("ok"):
            print(f"✨ Release {parsed.release_id} closed: {result.get('message', 'branch cleaned up, working tree clean.')}")
            sys.exit(0)
        else:
            print(f"❌ Release {parsed.release_id} close failed: {result.get('message', 'error')}", file=sys.stderr)
            sys.exit(1)
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    if result.get("ok") is False:
        sys.exit(1)
    sys.exit(0)


def verify_stage2_gatekeeper(repo_root: Path, target: Optional[str] = None, quiet: bool = False) -> int:
    """Verify Gate 1 pre-implementation approval for Stage 4 execution.

    Fail-closed gatekeeper for GitHub Spec Kit /before_implement hook.
    Returns 0 if valid APPROVED Gate 1 proof exists, exits with 1 otherwise.
    """
    import hashlib
    in_progress_dir = repo_root / "tasks" / "in-progress"
    if not in_progress_dir.exists() or not in_progress_dir.is_dir():
        if not quiet:
            print("❌ ForgeFlow Gatekeeper Error: 'tasks/in-progress' directory not found.", file=sys.stderr)
        return 1

    if target:
        target_pkg = in_progress_dir / target
        if not target_pkg.exists() or not target_pkg.is_dir():
            if not quiet:
                print(f"❌ ForgeFlow Gatekeeper Error: Target package '{target}' not found in tasks/in-progress/.", file=sys.stderr)
            return 1
        active_packages = [target_pkg]
    else:
        active_packages = [p for p in in_progress_dir.iterdir() if p.is_dir() and not p.name.startswith(".")]

    if not active_packages:
        if not quiet:
            print("❌ ForgeFlow Gatekeeper Error: No active release package found in tasks/in-progress/.", file=sys.stderr)
        return 1

    for pkg in active_packages:
        gate1_file = pkg / "GATE1_REVIEW.md"
        if not gate1_file.exists():
            if not quiet:
                print(f"❌ ForgeFlow Gatekeeper Error: Gate 1 approval proof missing: {gate1_file}", file=sys.stderr)
                print("   [CRITICAL] Implementation code cannot be written before Gate 1 approval.", file=sys.stderr)
                print("   Please complete Stage 1 specification and obtain Gate 1 approval (GATE1_REVIEW.md with APPROVED verdict).", file=sys.stderr)
            return 1

        gate1_content = gate1_file.read_text(encoding="utf-8")
        if "APPROVED" not in gate1_content.upper():
            if not quiet:
                print(f"❌ ForgeFlow Gatekeeper Error: Gate 1 verdict is not APPROVED in {gate1_file}", file=sys.stderr)
            return 1

    if not quiet:
        pkg_names = ", ".join(p.name for p in active_packages)
        print(f"✅ ForgeFlow Gatekeeper: Gate 1 pre-implementation check PASSED for: {pkg_names}")
    return 0


def main(args=None):
    parsed = parse_forgeflow_args(args)

    if not parsed.command or parsed.command == "version":
        print(f"ForgeFlow v{__version__} (Autonomous Agent Governance Framework)")
        sys.exit(0)

    if parsed.command == "issue":
        from .issue import handle_issue_command
        handle_issue_command(parsed)
        sys.exit(0)

    if parsed.command == "lifecycle":
        _run_lifecycle_command(parsed)

    if parsed.command == "update":
        target = Path(parsed.path) if parsed.path else Path.cwd()
        result = apply_update(target) if parsed.apply else inspect_update(target)
        use_json = getattr(parsed, "json", False)
        print(json.dumps(result, ensure_ascii=False, sort_keys=True) if use_json else json.dumps(result, ensure_ascii=False, indent=2))
        sys.exit(0 if result["status"] in {"up_to_date", "upgrade_available"} else 1)

    if parsed.command == "check":
        if getattr(parsed, "stage", None) == 2:
            repo_root = Path(parsed.repo_root).resolve() if parsed.repo_root else HierarchicalRootScanner.find_root()
            target_pkg = parsed.target[0] if parsed.target else None
            code = verify_stage2_gatekeeper(repo_root, target=target_pkg, quiet=getattr(parsed, "quiet", False))
            sys.exit(code)
        harness_args = ["check"]
        if parsed.target:
            harness_args.extend(parsed.target)
        if parsed.all:
            harness_args.append("--all")
        if parsed.strict:
            harness_args.append("--strict")
        if parsed.json:
            harness_args.append("--json")
        if parsed.repo_root:
            harness_args.extend(["--repo-root", parsed.repo_root])
        if parsed.lifecycle:
            harness_args.extend(["--lifecycle", parsed.lifecycle])
        if getattr(parsed, "self_governance", False):
            harness_args.append("--self-governance")
        if getattr(parsed, "release_id", None):
            harness_args.extend(["--release-id", parsed.release_id])
        if getattr(parsed, "base", None):
            harness_args.extend(["--base", parsed.base])
        if getattr(parsed, "python", None):
            harness_args.extend(["--python", parsed.python])
        harness_main(harness_args)

    elif parsed.command == "review":
        harness_args = ["review"]
        if parsed.target:
            harness_args.extend(parsed.target)
        if parsed.all:
            harness_args.append("--all")
        if parsed.base:
            harness_args.extend(["--base", parsed.base])
        if parsed.spec:
            harness_args.extend(["--spec", parsed.spec])
        if parsed.strict:
            harness_args.append("--strict")
        if getattr(parsed, "fail_on_warning", False):
            harness_args.append("--fail-on-warning")
        if getattr(parsed, "no_cache", False):
            harness_args.append("--no-cache")
        if parsed.json:
            harness_args.append("--json")
        if parsed.report:
            harness_args.extend(["--report", parsed.report])
        if parsed.repo_root:
            harness_args.extend(["--repo-root", parsed.repo_root])
        harness_main(harness_args)

    elif parsed.command == "init":
        if getattr(parsed, "speckit", False):
            target_path = Path(parsed.path).absolute() if parsed.path else (Path.cwd() / parsed.target if parsed.target else (Path.cwd() / parsed.project if parsed.project else Path.cwd().absolute()))
            res = TemplateScaffolder.scaffold_speckit_hybrid(target_path, force=parsed.force)
            if parsed.json:
                print(json.dumps(res, indent=2, ensure_ascii=False))
            else:
                print(f"✅ Initialized ForgeFlow-SpecKit hybrid environment in: {target_path}")
                for d in res["created_dirs"]:
                    print(f"  📁 {d}")
                for f in res["created_files"]:
                    print(f"  📄 {f}")
                for f in res["updated_files"]:
                    print(f"  ✏️ {f} (updated)")
            sys.exit(0)

        # 1. Project mode if explicitly specified with --project
        if parsed.project:
            base_dir = Path(parsed.path).absolute() if parsed.path else Path.cwd().absolute()
            target_path = base_dir / parsed.project
            res = TemplateScaffolder.init_project_governance(
                target_path,
                project_name=parsed.project,
                force=parsed.force,
                refresh_governance=parsed.refresh_governance,
                migrate_governance_binding=parsed.migrate_governance_binding,
                continuation_policy=parsed.continuation_policy,
                migrate_continuation_policy=parsed.migrate_continuation_policy,
            )
            if parsed.json:
                print(
                    json.dumps(
                        {
                            "status": "success",
                            "mode": "project",
                            "project_name": parsed.project,
                            "target_path": str(target_path),
                            "created_dirs": res["created_dirs"],
                            "created_files": res["created_files"],
                            "updated_files": res["updated_files"],
                            "skipped_files": res["skipped_files"],
                        },
                        indent=2,
                        ensure_ascii=False,
                    )
                )
            else:
                print(f"✅ Initialized ForgeFlow project governance in: {target_path}")
                for d in res["created_dirs"]:
                    print(f"  📁 {d}")
                for f in res["created_files"]:
                    print(f"  📄 {f}")
                for f in res["updated_files"]:
                    print(f"  ✏️ {f} (updated)")
                for s in res["skipped_files"]:
                    print(f"  ⚠️ {s} (already exists, skipped)")
            sys.exit(0)

        # 2. If target is provided: determine if release mode or project mode
        if parsed.target:
            root_path = None
            try:
                root_path = HierarchicalRootScanner.find_root()
            except Exception:
                root_path = None

            is_release = False
            if root_path and (root_path / "docs" / "releases").exists():
                is_release = True
            elif (
                parsed.target.startswith("v")
                or parsed.target.startswith("t_")
                or "-" in parsed.target
                or parsed.tier != 2
            ):
                is_release = True

            if is_release:
                effective_root = Path(parsed.path).absolute() if parsed.path else (root_path if root_path else Path.cwd().absolute())
                rel_dir = effective_root / "docs" / "releases" / parsed.target
                tmpl_dir = Path(parsed.template).resolve() if parsed.template else None
                created = TemplateScaffolder.create_release_scaffold(
                    target_dir=rel_dir,
                    release_id=parsed.target,
                    tier=parsed.tier,
                    force=parsed.force,
                    custom_template_dir=tmpl_dir,
                )
                core_docs = ["PRD.md", "DESIGN.md", "ROADMAP.md", "QA_SIGNOFF.md", "COMPLETION_REPORT.md", "RELEASE_NOTES.md"]
                created_list = [str(p) for p in created.values()]
                skipped_list = [doc for doc in core_docs if doc not in created]

                if parsed.json:
                    print(
                        json.dumps(
                            {
                                "status": "success",
                                "mode": "release",
                                "release_id": parsed.target,
                                "tier": parsed.tier,
                                "target_path": str(rel_dir),
                                "created_files": created_list,
                                "skipped_files": skipped_list,
                            },
                            indent=2,
                            ensure_ascii=False,
                        )
                    )
                else:
                    tier_name = TierRules.get_tier_name(parsed.tier)
                    print(f"✅ Created release scaffold for '{parsed.target}' in: {rel_dir} ({tier_name})")
                    for name in created:
                        print(f"  📄 {name}")
                    for name in skipped_list:
                        print(f"  ⚠️ {name} (already exists, skipped)")
                sys.exit(0)
            else:
                # Target treated as project name
                target_path = Path(parsed.path).absolute() if parsed.path else (Path.cwd() / parsed.target)
                res = TemplateScaffolder.init_project_governance(
                    target_path,
                    project_name=parsed.target,
                    force=parsed.force,
                refresh_governance=parsed.refresh_governance,
                migrate_governance_binding=parsed.migrate_governance_binding,
                continuation_policy=parsed.continuation_policy,
                migrate_continuation_policy=parsed.migrate_continuation_policy,
                )
                if parsed.json:
                    print(
                        json.dumps(
                            {
                                "status": "success",
                                "mode": "project",
                                "project_name": parsed.target,
                                "target_path": str(target_path),
                            "created_dirs": res["created_dirs"],
                            "created_files": res["created_files"],
                            "updated_files": res["updated_files"],
                            "skipped_files": res["skipped_files"],
                            },
                            indent=2,
                            ensure_ascii=False,
                        )
                    )
                else:
                    print(f"✅ Initialized ForgeFlow project governance in: {target_path}")
                    for d in res["created_dirs"]:
                        print(f"  📁 {d}")
                    for f in res["created_files"]:
                        print(f"  📄 {f}")
                    for f in res["updated_files"]:
                        print(f"  ✏️ {f} (updated)")
                    for s in res["skipped_files"]:
                        print(f"  ⚠️ {s} (already exists, skipped)")
                sys.exit(0)

        # 3. No target and no --project: initialize project in CWD (or --path)
        target_path = Path(parsed.path).absolute() if parsed.path else Path.cwd().absolute()
        res = TemplateScaffolder.init_project_governance(
            target_path,
            project_name=target_path.name,
            force=parsed.force,
            refresh_governance=parsed.refresh_governance,
            migrate_governance_binding=parsed.migrate_governance_binding,
            continuation_policy=parsed.continuation_policy,
            migrate_continuation_policy=parsed.migrate_continuation_policy,
        )
        if parsed.json:
            print(
                json.dumps(
                    {
                        "status": "success",
                        "mode": "project",
                        "project_name": target_path.name,
                        "target_path": str(target_path),
                        "created_dirs": res["created_dirs"],
                        "created_files": res["created_files"],
                        "updated_files": res["updated_files"],
                        "skipped_files": res["skipped_files"],
                    },
                    indent=2,
                    ensure_ascii=False,
                )
            )
        else:
            print(f"✅ Initialized ForgeFlow project governance in: {target_path}")
            for d in res["created_dirs"]:
                print(f"  📁 {d}")
            for f in res["created_files"]:
                print(f"  📄 {f}")
            for f in res["updated_files"]:
                print(f"  ✏️ {f} (updated)")
            for s in res["skipped_files"]:
                print(f"  ⚠️ {s} (already exists, skipped)")
        sys.exit(0)

    elif parsed.command == "release":
        if parsed.release_command == "create":
            root_path = HierarchicalRootScanner.find_root()
            rel_dir = TemplateScaffolder.resolve_release_dir(root_path, parsed.release_id, stage="in-progress")
            created = TemplateScaffolder.create_release_scaffold(
                target_dir=rel_dir, release_id=parsed.release_id, tier=parsed.tier
            )
            print(f"✅ Created release scaffold in: {rel_dir}")
            for name, p in created.items():
                print(f"  📄 {name}")
            sys.exit(0)
        else:
            print("Usage: forgeflow release create <release_id> [--tier 1|2|3]")
            sys.exit(1)

    elif parsed.command == "task":
        if parsed.task_command == "create":
            root_path = HierarchicalRootScanner.find_root()
            rel_dir = TemplateScaffolder.resolve_release_dir(root_path, parsed.task_id, stage=getattr(parsed, "stage", "in-progress"))
            created = TemplateScaffolder.create_release_scaffold(
                target_dir=rel_dir, release_id=parsed.task_id, tier=parsed.tier
            )
            print(f"✅ Created task package scaffold in: {rel_dir}")
            for name, p in created.items():
                print(f"  📄 {name}")
            sys.exit(0)
        else:
            print("Usage: forgeflow task create <task_id> [--tier 1|2|3] [--stage in-progress|backlog]")
            sys.exit(1)

    elif parsed.command == "migrate":
        root_path = Path(parsed.repo_root).resolve() if getattr(parsed, "repo_root", None) else HierarchicalRootScanner.find_root()
        if getattr(parsed, "tasks", False):
            result = TemplateScaffolder.migrate_to_tasks(root_path, target_dir_name=getattr(parsed, "target", "tasks"))
            if result.get("status") == "success":
                print(f"✅ Successfully migrated {result.get('count', 0)} legacy releases to {result.get('target_dir')}/completed/:")
                for r in result.get("migrated", []):
                    print(f"  • {r}")
                print(f"✅ Created {result.get('target_dir')}/README.md non-guidance boundary guard.")
                print(f"✅ Updated .forgeflow.json governance.tasks_dir to '{result.get('target_dir')}'.")
            else:
                print(f"ℹ️ Migration skipped: {result.get('reason')}")
            sys.exit(0)
        else:
            print("Usage: forgeflow migrate --tasks [--target tasks|ff-tasks]")
            sys.exit(1)

    elif parsed.command == "status":
        root_path = HierarchicalRootScanner.find_root()
        releases = ReleaseScanner.get_all_releases(root_path)
        print(f"📍 Project Root: {root_path}")
        print(f"📦 Total Releases: {len(releases)}")
        for r in releases:
            print(f"  • {r.name}")
        sys.exit(0)

    elif parsed.command in ("doctor", "diagnose"):
        from .diagnostics import doctor_main
        d_args = []
        if getattr(parsed, "json", False):
            d_args.append("--json")
        if getattr(parsed, "report_issue", False):
            d_args.append("--report-issue")
        if getattr(parsed, "clear", False):
            d_args.append("--clear")
        code = doctor_main(d_args)
        sys.exit(code)


if __name__ == "__main__":
    main()
