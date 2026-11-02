#!/usr/bin/env python3
"""
ForgeFlow & Harness Unified CLI Entrypoints
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

from . import __version__
from .renderer import ReportRenderer
from .reviewer import ReviewEngine
from .scaffold import TemplateScaffolder
from .scanner import HierarchicalRootScanner


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

    from .workflow import add_parser as add_workflow_parser
    add_workflow_parser(subparsers)

    # Command: init
    init_parser = subparsers.add_parser("init", help="Initialize a lean ForgeFlow project")
    init_parser.add_argument("target", nargs="?", default=None, help="Optional project directory name")
    init_parser.add_argument("--project", type=str, default=None, help="Project directory name")
    init_parser.add_argument("--speckit", "--hybrid", action="store_true", dest="speckit", help="Add Spec Kit scripts and templates")
    init_parser.add_argument("--force", action="store_true", help="Accepted for compatibility; user files are preserved")
    init_parser.add_argument("--json", action="store_true", help="Output machine-readable JSON")
    init_parser.add_argument("--path", type=str, default=None, help="Target directory")

    # Command: review
    rev_parser = subparsers.add_parser("review", help="Run AST code smell detection and 2-axis review")
    rev_parser.add_argument("target", nargs="*", default=None, help="Target files or directories")
    rev_parser.add_argument("--all", action="store_true", help="Review all source files")
    rev_parser.add_argument("--base", type=str, default=None, help="Base git ref for diff")
    rev_parser.add_argument("--findings-baseline", type=str, default=None, help="Baseline git ref for comparing warnings")
    rev_parser.add_argument("--spec", type=str, default=None, help="Explicit spec file path")
    rev_parser.add_argument("--strict", action="store_true", help="Fail on warning smells")
    rev_parser.add_argument("--fail-on-warning", action="store_true", help="Fail if any warning smells are found")
    rev_parser.add_argument("--no-cache", action="store_true", help="Disable incremental AST checkpoint cache")
    rev_parser.add_argument("--json", action="store_true", help="Output JSON report")
    rev_parser.add_argument("--report", type=str, default=None, help="Custom markdown report output path")
    rev_parser.add_argument("--repo-root", type=str, default=None, help="Explicit repository root")

    # Command: version
    subparsers.add_parser("version", help="Show ForgeFlow version")

    # Command: upgrade
    upgrade_parser = subparsers.add_parser("upgrade", help="Upgrade global ForgeFlow installation to the latest version")
    upgrade_parser.add_argument("--check", action="store_true", help="Check for available updates without installing")
    upgrade_parser.add_argument("--force", action="store_true", help="Force upgrade/reinstall without confirmation prompt")
    upgrade_parser.add_argument("--json", action="store_true", help="Output machine-readable JSON")
    upgrade_parser.add_argument(
        "--repo-url",
        default="https://raw.githubusercontent.com/deepblue-kblee/forgeflow/main",
        help="Remote repository base URL (version and installer are fetched from the same revision)",
    )
    upgrade_parser.add_argument(
        "--revision",
        default=None,
        help="Immutable revision/ref to fetch and install (default: ref in --repo-url, normally main)",
    )

    # Command: update
    update_parser = subparsers.add_parser(
        "update",
        help="Update local repository governance specifications and Spec Kit assets to the latest version",
    )
    update_parser.add_argument(
        "--path",
        default=None,
        help="Target project repository root (default: current directory or detected root)",
    )
    update_parser.add_argument("--json", action="store_true", help="Output machine-readable JSON")
    update_parser.add_argument("--quiet", action="store_true", help="Suppress non-error output")
    update_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Inventory and plan changes without writing files",
    )

    # Command: doc (alias: spec)
    doc_parser = subparsers.add_parser(
        "doc",
        aliases=["spec"],
        help="Inspect and display official ForgeFlow specifications",
    )
    doc_parser.add_argument(
        "name",
        nargs="?",
        default=None,
        help="Specification document name (e.g. FLOW_SPEC, GATES_AND_LOOPS, SPECKIT_HOOKS_AND_NORMS)",
    )
    doc_parser.add_argument(
        "extra",
        nargs="?",
        default=None,
        help="Optional second argument (e.g. when calling 'forgeflow doc show FLOW_SPEC')",
    )
    doc_parser.add_argument("--list", action="store_true", help="List all available official specifications")
    doc_parser.add_argument("--path", type=str, default=None, help="Explicit specification directory or repository path")
    doc_parser.add_argument("--json", action="store_true", help="Output machine-readable JSON")

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


def parse_version_tuple(v_str):
    """Parse version string into integer tuple for comparison (e.g. '0.1.2' -> (0, 1, 2))."""
    import re
    nums = re.findall(r"\d+", str(v_str))
    return tuple(map(int, nums)) if nums else (0,)


def _with_revision(repo_url: str, revision: str | None) -> tuple[str, str]:
    base = repo_url.rstrip("/")
    if base.startswith("https://raw.githubusercontent.com/"):
        root, current_ref = base.rsplit("/", 1)
        ref = revision or current_ref
        return f"{root}/{ref}", ref
    return base, revision or "main"


def handle_upgrade(args):
    """Check or install a verified distribution from one resolved revision."""
    import hashlib
    import re
    import tempfile
    import urllib.request

    from .distribution import (
        derive_clone_url,
        read_package_metadata,
        resolve_installation_target,
        resolve_revision,
        verify_installed_distribution,
    )

    repo_url = getattr(args, "repo_url", "https://raw.githubusercontent.com/deepblue-kblee/forgeflow/main").rstrip("/")
    check_only = getattr(args, "check", False)
    force = getattr(args, "force", False)
    as_json = getattr(args, "json", False)
    base_url, ref = _with_revision(repo_url, getattr(args, "revision", None))
    if not re.match(r"^(https?|file)://", base_url) or any(char in base_url for char in ("\n", "\r")):
        message = f"Invalid repository URL: {base_url}"
        if as_json:
            print(json.dumps({"status": "error", "message": message, "current_version": __version__}))
        else:
            print(f"❌ ForgeFlow Upgrade Error: {message}", file=sys.stderr)
        return 1

    http_headers = {
        "User-Agent": "ForgeFlow-CLI",
        "Cache-Control": "no-cache, no-store, must-revalidate",
        "Pragma": "no-cache",
    }

    def fetch(url: str, timeout: int = 10) -> bytes:
        request = urllib.request.Request(url, headers=http_headers)
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return response.read()

    try:
        version_bytes = fetch(f"{base_url}/src/forgeflow/_version.py", timeout=5)
        version_text = version_bytes.decode("utf-8")
        match = re.search(r'__version__\s*=\s*["\']([^"\']+)["\']', version_text)
        remote_version = match.group(1).strip() if match else None
    except Exception as e:
        if as_json:
            print(json.dumps({"status": "error", "message": f"Failed to fetch remote version: {e}", "current_version": __version__}))
        else:
            print(f"❌ ForgeFlow Upgrade Error: Failed to check remote version from {base_url}: {e}", file=sys.stderr)
        return 1
    if not remote_version:
        if as_json:
            print(json.dumps({"status": "error", "message": "Failed to parse remote version", "current_version": __version__}))
        else:
            print("❌ ForgeFlow Upgrade Error: Remote version could not be parsed.", file=sys.stderr)
        return 1

    try:
        installer_bytes = fetch(f"{base_url}/install.sh")
    except Exception as e:
        if as_json:
            print(json.dumps({"status": "error", "message": f"Failed to download installer: {e}"}))
        else:
            print(f"❌ ForgeFlow Upgrade Error: Failed to download installer from {base_url}: {e}", file=sys.stderr)
        return 1
    if not installer_bytes.startswith(b"#!") or b"forgeflow" not in installer_bytes.lower():
        message = "Downloaded installer is not a recognizable ForgeFlow installer."
        if as_json:
            print(json.dumps({"status": "error", "message": message}))
        else:
            print(f"❌ ForgeFlow Upgrade Error: {message}", file=sys.stderr)
        return 1

    source_identity = hashlib.sha256(version_bytes + b"\0" + installer_bytes).hexdigest()
    clone_url = derive_clone_url(base_url)
    resolved_revision = resolve_revision(clone_url, ref)
    revision_resolved = bool(re.fullmatch(r"[0-9a-f]{40}", resolved_revision))
    target = resolve_installation_target()
    current_metadata = read_package_metadata(target["prefix"])
    installed = bool(current_metadata.get("version"))
    current_installed_version = current_metadata.get("version") if installed else None
    installed_revision = current_metadata.get("source_revision") or current_metadata.get("git_commit")
    current_source_identity = current_metadata.get("source_identity")
    if not installed:
        identity_comparison = "not-installed"
    elif current_source_identity:
        identity_comparison = "same" if current_source_identity == source_identity else "different"
    else:
        identity_comparison = "unknown"

    current_tuple = parse_version_tuple(current_installed_version or "0")
    remote_tuple = parse_version_tuple(remote_version)
    same_version_different_build = (
        installed
        and remote_tuple == current_tuple
        and (
            identity_comparison == "different"
            or (
                installed_revision
                and resolved_revision
                and installed_revision != resolved_revision
            )
        )
    )
    if same_version_different_build and identity_comparison != "different":
        identity_comparison = "different"
    is_upgrade_available = (not installed) or remote_tuple > current_tuple or same_version_different_build
    is_remote_older = installed and remote_tuple < current_tuple
    warning_msg = None
    if is_remote_older:
        warning_msg = (
            f"Remote version (v{remote_version}) is older than installed version (v{current_installed_version}). "
            "GitHub CDN cache may still be updating."
        )

    if not as_json:
        print("🔍 Checking ForgeFlow version...")
        print(f"• Installed version: {'v' + current_installed_version if installed else 'not installed'}")
        print(f"• Latest version:    v{remote_version}")
        print(f"• Source revision:   {resolved_revision}")
        print(f"• Source identity:   {source_identity[:16]} ({identity_comparison})")
        if warning_msg:
            print(f"⚠️  Warning: {warning_msg}")
        print()

    if check_only:
        payload = {
            "status": "success",
            "installed": installed,
            "current_version": current_installed_version,
            "remote_version": remote_version,
            "upgrade_available": is_upgrade_available,
            "source_identity": source_identity,
            "source_revision": resolved_revision,
            "revision_resolved": revision_resolved,
            "identity_comparison": identity_comparison,
            "target": target,
        }
        if same_version_different_build:
            payload["reason"] = "same-version-different-build"
        if warning_msg:
            payload["warning"] = warning_msg
        if as_json:
            print(json.dumps(payload))
        else:
            if is_upgrade_available:
                print(f"🚀 Update available: {'not installed' if not installed else 'v' + current_installed_version} ➔ v{remote_version}")
                print("   Run 'forgeflow upgrade' to install.")
            else:
                print(f"✅ ForgeFlow is up to date (v{current_installed_version}).")
        return 0

    if not installed and not force:
        message = (
            f"No installed distribution was found at {target['prefix']}. "
            "Run install.sh explicitly or use 'forgeflow upgrade --force' after reviewing the target."
        )
        if as_json:
            print(json.dumps({"status": "error", "message": message, "upgraded": False, "installed": False, "target": target}))
        else:
            print(f"❌ ForgeFlow Upgrade Error: {message}", file=sys.stderr)
        return 1

    if installed and not is_upgrade_available and not force:
        if as_json:
            payload = {
                "status": "success",
                "message": f"ForgeFlow is already up to date (v{current_installed_version}).",
                "current_version": current_installed_version,
                "remote_version": remote_version,
                "upgraded": False,
                "source_identity": source_identity,
                "identity_comparison": identity_comparison,
            }
            if warning_msg:
                payload["warning"] = warning_msg
            print(json.dumps(payload))
        else:
            print(f"✅ ForgeFlow is already up to date (v{current_installed_version}). (Use --force to reinstall)")
        return 0

    if not force and not as_json:
        action_label = "upgrade to" if is_upgrade_available else "reinstall"
        try:
            answer = input(f"Do you want to {action_label} v{remote_version}? [y/N]: ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            print("\nUpgrade cancelled.")
            return 0
        if answer not in ("y", "yes"):
            print("Upgrade cancelled.")
            return 0

    if not clone_url:
        message = (
            "Cannot prove the installation source for this repository URL. "
            "Set FORGEFLOW_REPO to the matching Git repository or use a raw.githubusercontent.com URL."
        )
        if as_json:
            print(json.dumps({"status": "error", "message": message, "upgraded": False}))
        else:
            print(f"❌ ForgeFlow Upgrade Error: {message}", file=sys.stderr)
        return 1
    if not revision_resolved and not base_url.startswith("file://"):
        message = (
            f"Could not resolve an immutable commit for revision {resolved_revision!r}. "
            "Installation is refused to avoid mixing different builds; retry with a commit SHA."
        )
        if as_json:
            print(json.dumps({
                "status": "error", "message": message, "upgraded": False,
                "source_revision": resolved_revision,
            }))
        else:
            print(f"❌ ForgeFlow Upgrade Error: {message}", file=sys.stderr)
        return 1

    if not as_json:
        action_ing = "Upgrading ForgeFlow" if is_upgrade_available else "Reinstalling ForgeFlow"
        print(f"📦 {action_ing}: v{current_installed_version} ➔ v{remote_version}...")

    with tempfile.TemporaryDirectory(prefix="forgeflow-upgrade-") as temp_dir:
        temp_installer = Path(temp_dir) / "install.sh"
        temp_installer.write_bytes(installer_bytes)
        env = dict(os.environ)
        env.update({
            "FORGEFLOW_INSTALL_DIR": target["prefix"],
            "FORGEFLOW_BIN_DIR": target["bin_dir"],
            "FORGEFLOW_SKILLS_DIR": target["skills_dir"],
            "FORGEFLOW_REPO": clone_url,
            "FORGEFLOW_REVISION": resolved_revision,
            "FORGEFLOW_EXPECTED_VERSION": remote_version,
            "FORGEFLOW_SOURCE_IDENTITY": source_identity,
        })
        try:
            result = subprocess.run(
                ["bash", str(temp_installer), "--force"],
                capture_output=as_json,
                text=True,
                env=env,
            )
        except Exception as e:
            if as_json:
                print(json.dumps({"status": "error", "message": f"Installer could not run: {e}", "upgraded": False}))
            else:
                print(f"❌ ForgeFlow Upgrade Error: Installer could not run: {e}", file=sys.stderr)
            return 1
        if result.returncode != 0:
            if as_json:
                print(json.dumps({
                    "status": "error",
                    "message": "Installer exited with failure",
                    "returncode": result.returncode,
                    "stderr": result.stderr,
                    "upgraded": False,
                }))
            else:
                print(f"❌ ForgeFlow Upgrade Error: Installer exited with code {result.returncode}", file=sys.stderr)
            return result.returncode

    verification = verify_installed_distribution(
        target,
        expected_version=remote_version,
        expected_source_identity=source_identity,
        expected_revision=resolved_revision,
    )
    if not verification["ok"]:
        if as_json:
            print(json.dumps({
                "status": "error",
                "message": "Installer exited successfully but the installed distribution could not be verified.",
                "upgraded": False,
                "errors": verification["errors"],
                "observed": verification["observed"],
                "target": target,
            }))
        else:
            print("❌ ForgeFlow Upgrade Error: Installed distribution could not be verified.", file=sys.stderr)
            for error in verification["errors"]:
                print(f"   • {error}", file=sys.stderr)
        return 1

    installed_version = remote_version
    highlights = None
    try:
        changelog = Path(target["prefix"]) / "current" / "lib" / "forgeflow" / "CHANGELOG.md"
        if changelog.is_file():
            from .scaffold import TemplateScaffolder
            highlights = TemplateScaffolder.extract_changelog_section(installed_version, changelog_file=changelog)
    except Exception:
        pass
    if as_json:
        payload = {
            "status": "success",
            "message": f"Successfully upgraded ForgeFlow to v{installed_version}.",
            "previous_version": current_installed_version,
            "current_version": installed_version,
            "upgraded": True,
            "source_identity": source_identity,
            "source_revision": resolved_revision,
            "identity_comparison": identity_comparison,
            "target": target,
            "observed": verification["observed"],
        }
        if highlights:
            payload["release_highlights"] = highlights
        print(json.dumps(payload))
    else:
        print(f"🎉 Successfully upgraded ForgeFlow to v{installed_version}!")
        print(f"   Installed at: {target['prefix']}")
        print(f"   Entrypoint:   {target['bin_dir']}/forgeflow")
        if highlights:
            print("\n------------------------------------------------------------")
            print(f"📋 Release Highlights for v{installed_version}:")
            print(highlights)
            print("------------------------------------------------------------")
            print("💡 전체 세부 사양서 열람: 'forgeflow doc show changelog'")
    return 0


def handle_update(args):
    """Refresh a current 0.2.x project; legacy layouts require forgeflow-migrate."""
    target_dir = Path(args.path).resolve() if getattr(args, "path", None) else HierarchicalRootScanner.find_root()
    as_json = getattr(args, "json", False)
    quiet = getattr(args, "quiet", False)
    dry_run = getattr(args, "dry_run", False)
    try:
        res = TemplateScaffolder.update_repo_governance(target_dir, dry_run=dry_run)
    except Exception as e:
        if as_json:
            print(json.dumps({"status": "error", "message": str(e), "target_dir": str(target_dir)}))
        else:
            print(f"ForgeFlow Update Error: {e}", file=sys.stderr)
        return 1

    if as_json:
        print(json.dumps(res, indent=2, ensure_ascii=False))
    elif not quiet:
        print(f"ForgeFlow update: {res['status']}")
        print(f"   Project Root: {res['target_dir']}")
        print(f"   Version:      v{res.get('previous_version')} -> v{res.get('current_version')}")
        if dry_run:
            print("   Mode:         dry-run (no files written)")
        for label, key in (("Created", "created_files"), ("Updated", "updated_files")):
            values = res.get(key) or []
            if values:
                print(f"   {label} ({len(values)}):")
                for value in values:
                    print(f"     - {value}")
        for item in res.get("blockers") or []:
            print(f"   Blocker: {item['reason']}")
        for action in res.get("next_actions") or []:
            print(f"   Next: {action}")
    return {"applied": 0, "no-op": 0, "planned": 0, "needs-action": 3}.get(res.get("status"), 1)


OFFICIAL_SPECS = [
    {
        "id": "README",
        "filename": "README.md",
        "title": "Specification Index & Situational Router",
        "description": "공식 사양서 색인 및 작업 단계별 상황 라우팅 가이드",
    },
    {
        "id": "FLOW_SPEC",
        "filename": "FLOW_SPEC.md",
        "title": "Development Workflow, Ownership & Finalization",
        "description": "요구·계획·구현·검증·통합·정리의 상태 및 실행 계약",
    },
    {
        "id": "GATES_AND_LOOPS",
        "filename": "GATES_AND_LOOPS.md",
        "title": "Verification, Progress & Strict Compatibility",
        "description": "필수 검증, 증거 재사용, 실패 조사 및 strict 호환 경로",
    },
    {
        "id": "SPECKIT_HOOKS_AND_NORMS",
        "filename": "SPECKIT_HOOKS_AND_NORMS.md",
        "title": "GitHub Spec Kit Integration",
        "description": "Spec Kit 위임, 비파괴 setup 및 선택적 hook",
    },
    {
        "id": "ANTI_PATTERNS",
        "filename": "ANTI_PATTERNS.md",
        "title": "Design Boundaries & Anti-Patterns",
        "description": "권한·소유권·검증·기준 변경의 설계 경계",
    },
    {
        "id": "DISTRIBUTION_SPEC",
        "filename": "DISTRIBUTION_SPEC.md",
        "title": "Distribution, Packaging & Upgrade Specification",
        "description": "OS 계정 레벨 배포, 버전 관리, forgeflow upgrade 및 update 규격",
    },
    {
        "id": "PHILOSOPHY_AND_COMPASS",
        "filename": "PHILOSOPHY_AND_COMPASS.md",
        "title": "Philosophy & Architecture Compass",
        "description": "프레임워크 핵심 설계 철학, SSOT 경계 및 에이전트 행동 지침",
    },
    {
        "id": "REFACTORING_GUIDE",
        "filename": "REFACTORING_GUIDE.md",
        "title": "Modular Decomposition & Refactoring Guide",
        "description": "모듈 분리, 클린 아키텍처 및 복잡도 제어 가이드라인",
    },
    {
        "id": "CHANGELOG",
        "filename": "CHANGELOG.md",
        "title": "Release History & Evolution",
        "description": "프레임워크 릴리즈 이력 및 변경 사항 일람 (spec 외부 격리 보관)",
    },
]


def resolve_spec_directory(custom_path: Optional[str] = None) -> Optional[Path]:
    """Find the directory containing official specifications."""
    if custom_path:
        cp = Path(custom_path).resolve()
        for candidate in [cp, cp / ".forgeflow" / "spec", cp / "docs" / "spec", cp / "spec", cp / "templates" / "spec"]:
            if candidate.is_dir() and (candidate / "FLOW_SPEC.md").is_file():
                return candidate

    # A task's absolute pinned command keeps its own rules even when launched
    # from another project's cwd. An explicit --path remains the override.
    package = Path(__file__).resolve().parent
    identity = package.parent.name
    if (package.name == "forgeflow" and len(identity) == 64
            and all(char in "0123456789abcdef" for char in identity)
            and package.parent.parent.name == "runtime"
            and package.parent.parent.parent.name == ".forgeflow"):
        executing_spec = package / "spec"
        if (executing_spec / "FLOW_SPEC.md").is_file():
            return executing_spec

    # 1. Project local .forgeflow/spec or workspace docs/spec/
    try:
        root = HierarchicalRootScanner.find_root()
        source_entry = root / "src" / "forgeflow" / "cli.py"
        if source_entry.resolve() == Path(__file__).resolve():
            return root / "docs" / "spec"
        proj_spec = root / ".forgeflow" / "spec"
        if proj_spec.is_dir() and (proj_spec / "FLOW_SPEC.md").is_file():
            return proj_spec
        local_spec = root / "docs" / "spec"
        if local_spec.is_dir() and (local_spec / "FLOW_SPEC.md").is_file():
            return local_spec
    except Exception:
        pass

    # 2. Package spec/
    try:
        pkg_spec = Path(__file__).resolve().parent / "spec"
        if pkg_spec.is_dir() and (pkg_spec / "FLOW_SPEC.md").is_file():
            return pkg_spec
        legacy_pkg_spec = Path(__file__).resolve().parent / "templates" / "spec"
        if legacy_pkg_spec.is_dir() and (legacy_pkg_spec / "FLOW_SPEC.md").is_file():
            return legacy_pkg_spec
    except Exception:
        pass

    # 3. Global user installation ~/.local/share/forgeflow/current/lib/forgeflow/spec
    global_share_spec = Path.home() / ".local" / "share" / "forgeflow" / "current" / "lib" / "forgeflow" / "spec"
    if global_share_spec.is_dir() and (global_share_spec / "FLOW_SPEC.md").is_file():
        return global_share_spec

    global_legacy_spec = Path.home() / ".local" / "forgeflow" / "current" / "lib" / "forgeflow" / "templates" / "spec"
    if global_legacy_spec.is_dir() and (global_legacy_spec / "FLOW_SPEC.md").is_file():
        return global_legacy_spec

    return None


def handle_doc(args):
    """Handle forgeflow doc (or spec) command to display specifications."""
    as_json = getattr(args, "json", False)
    spec_dir = resolve_spec_directory(getattr(args, "path", None))

    if not spec_dir:
        msg = "Official specifications directory not found."
        if as_json:
            print(json.dumps({"status": "error", "message": msg}))
        else:
            print(f"❌ Error: {msg}", file=sys.stderr)
        return 1

    # Normalize name argument
    name = getattr(args, "name", None)
    extra = getattr(args, "extra", None)
    if name == "show" and extra:
        name = extra
    elif name == "list":
        name = None

    show_list = getattr(args, "list", False) or not name

    if show_list:
        specs_data = []
        for s in OFFICIAL_SPECS:
            file_path = spec_dir / s["filename"]
            specs_data.append({
                "id": s["id"],
                "filename": s["filename"],
                "title": s["title"],
                "description": s["description"],
                "path": str(file_path),
                "exists": file_path.is_file(),
            })

        if as_json:
            print(json.dumps({
                "status": "success",
                "spec_dir": str(spec_dir),
                "count": len(specs_data),
                "specifications": specs_data,
            }, indent=2, ensure_ascii=False))
        else:
            print(f"🌊 ForgeFlow Official Specifications (SSOT)")
            print(f"   Directory: {spec_dir}\n")
            print(f"   {'#':<3} {'Specification ID':<25} {'Title':<45} {'Filename'}")
            print(f"   {'-'*3} {'-'*25} {'-'*45} {'-'*25}")
            for i, s in enumerate(specs_data, 1):
                print(f"   {i:<3} {s['id']:<25} {s['title']:<45} {s['filename']}")
                print(f"       └─ {s['description']}")
            print(f"\n💡 View full specification: forgeflow doc <id|filename> (e.g. forgeflow doc FLOW_SPEC)")
        return 0

    # Query single spec
    norm_name = name.strip()
    if norm_name.lower().endswith(".md"):
        norm_name = norm_name[:-3]
    norm_id = norm_name.upper().replace("-", "_")

    matched = None
    for s in OFFICIAL_SPECS:
        if s["id"] == norm_id or s["filename"].upper() == f"{norm_id}.MD":
            matched = s
            break

    if not matched:
        # Fallback: check if exact file exists in spec_dir
        candidate_file = spec_dir / name
        if not candidate_file.is_file():
            candidate_file = spec_dir / f"{name}.md"
        if candidate_file.is_file():
            matched = {
                "id": candidate_file.stem.upper(),
                "filename": candidate_file.name,
                "title": candidate_file.stem,
                "description": "",
            }

    if not matched:
        msg = f"Specification '{name}' not found."
        valid_ids = [s["id"] for s in OFFICIAL_SPECS]
        if as_json:
            print(json.dumps({"status": "error", "message": msg, "available": valid_ids}))
        else:
            print(f"❌ Error: {msg}", file=sys.stderr)
            print(f"   Available specifications: {', '.join(valid_ids)}", file=sys.stderr)
            print(f"   Run 'forgeflow doc --list' to see all specifications.", file=sys.stderr)
        return 1

    file_path = spec_dir / matched["filename"]
    if not file_path.is_file() and matched["id"] == "CHANGELOG":
        candidates = [
            spec_dir.parent / "CHANGELOG.md",
            Path.home() / ".local" / "share" / "forgeflow" / "CHANGELOG.md",
            Path.home() / ".local" / "forgeflow" / "CHANGELOG.md",
        ]
        try:
            root = HierarchicalRootScanner.find_root()
            candidates.extend([root / "docs" / "CHANGELOG.md", root / "src" / "forgeflow" / "CHANGELOG.md", root / "CHANGELOG.md"])
        except Exception:
            pass
        for cand in candidates:
            if cand.is_file():
                file_path = cand
                break

    if not file_path.is_file():
        msg = f"Specification file not found at: {file_path}"
        if as_json:
            print(json.dumps({"status": "error", "message": msg}))
        else:
            print(f"❌ Error: {msg}", file=sys.stderr)
        return 1

    content = file_path.read_text(encoding="utf-8")
    if as_json:
        print(json.dumps({
            "status": "success",
            "id": matched["id"],
            "filename": matched["filename"],
            "title": matched["title"],
            "path": str(file_path),
            "content": content,
        }, indent=2, ensure_ascii=False))
    else:
        print(f"<!-- ForgeFlow Specification: {matched['id']} ({file_path}) -->\n")
        print(content)
    return 0


def main(args=None):
    parsed = parse_forgeflow_args(args)

    if not parsed.command or parsed.command == "version":
        print(f"ForgeFlow v{__version__} (Autonomous Agent Governance Framework)")
        sys.exit(0)

    if parsed.command == "upgrade":
        code = handle_upgrade(parsed)
        sys.exit(code)

    if parsed.command == "workflow":
        from .workflow import handle_command
        sys.exit(handle_command(parsed))

    if parsed.command == "update":
        code = handle_update(parsed)
        sys.exit(code)

    if parsed.command in ("doc", "spec"):
        code = handle_doc(parsed)
        sys.exit(code)

    if parsed.command == "issue":
        from .issue import handle_issue_command
        handle_issue_command(parsed)
        sys.exit(0)

    elif parsed.command == "review":
        root_path = Path(parsed.repo_root).resolve() if parsed.repo_root else HierarchicalRootScanner.find_root()
        engine = ReviewEngine(repo_root=root_path)
        targets = [Path(t) for t in parsed.target] if parsed.target else None
        result = engine.run_review(
            targets=targets,
            all_files=parsed.all,
            base_ref=parsed.base,
            explicit_spec=parsed.spec,
            strict=parsed.strict,
            fail_on_warning=getattr(parsed, "fail_on_warning", False),
            no_cache=getattr(parsed, "no_cache", False),
            report_dest=Path(parsed.report) if parsed.report else None,
            findings_baseline=getattr(parsed, "findings_baseline", None),
        )
        if parsed.json:
            print(ReportRenderer.render_json_review(result))
        else:
            print(ReportRenderer.render_terminal_review(result))
        sys.exit(0 if result.passed else 1)

    elif parsed.command == "init":
        if parsed.path:
            target_path = Path(parsed.path).absolute()
        elif parsed.target:
            target_path = (Path.cwd() / parsed.target).absolute()
        elif parsed.project:
            target_path = (Path.cwd() / parsed.project).absolute()
        else:
            target_path = Path.cwd().absolute()
        if getattr(parsed, "speckit", False):
            res = TemplateScaffolder.scaffold_speckit_hybrid(target_path, force=parsed.force)
        else:
            res = TemplateScaffolder.scaffold_lean_project(target_path, force=parsed.force)
        if parsed.json:
            print(json.dumps(res, indent=2, ensure_ascii=False))
        else:
            print(f"Initialized ForgeFlow project in: {target_path}")
            for path in res.get("created_dirs", []):
                print(f"  + {path}")
            for path in res.get("created_files", []):
                print(f"  + {path}")
            for path in res.get("updated_files", []):
                print(f"  ~ {path}")
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
