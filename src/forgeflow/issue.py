#!/usr/bin/env python3
"""
ForgeFlow Issue Tracking & Local Cache Module.

Provides fast read-through caching for GitHub Issues to optimize agent cycles,
token consumption, and developer ergonomics without third-party dependencies.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import re
import subprocess
import sys
from typing import Any, Dict, List, Optional

DEFAULT_REPO = "deepblue-kblee/forgeflow"


def get_repo_root() -> Path:
    """Locate git repository root directory."""
    current = Path.cwd().resolve()
    while current != current.parent:
        if (current / ".git").exists():
            return current
        current = current.parent
    return Path.cwd()


def detect_repo_from_git() -> str:
    """Detect GitHub repository slug (owner/repo) from git remote."""
    try:
        res = subprocess.run(
            ["git", "config", "--get", "remote.origin.url"],
            capture_output=True,
            text=True,
            check=False,
        )
        url = res.stdout.strip()
        match = re.search(r"github\.com[:/]([^/]+/[^/.]+?)(?:\.git)?$", url)
        if match:
            return match.group(1)
    except Exception:
        pass
    return DEFAULT_REPO


def get_cache_dir(repo_root: Optional[Path] = None) -> Path:
    """Return the local issue cache directory (.cache/issues)."""
    root = repo_root or get_repo_root()
    cache_dir = root / ".cache" / "issues"
    cache_dir.mkdir(parents=True, exist_ok=True)
    return cache_dir


def run_gh_command(args: List[str]) -> subprocess.CompletedProcess[str]:
    """Execute a GitHub CLI command securely without invoking a shell."""
    cmd = ["gh"] + args
    return subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        check=False,
    )


class IssueTracker:
    """Handles issue operations with local-first file caching."""

    def __init__(self, repo: Optional[str] = None, cache_dir: Optional[Path] = None) -> None:
        self.repo = repo or detect_repo_from_git()
        self.cache_dir = cache_dir or get_cache_dir()

    def _issue_cache_path(self, number: int) -> Path:
        return self.cache_dir / f"{number}.json"

    def _index_cache_path(self) -> Path:
        return self.cache_dir / "index.json"

    def _invalidate_index_cache(self) -> None:
        """Invalidate the cached issue list index."""
        index_path = self._index_cache_path()
        if index_path.exists():
            try:
                os.remove(index_path)
            except OSError:
                pass

    def create(
        self,
        title: str,
        body: str,
        labels: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Create an issue on GitHub and cache it locally."""
        cmd = ["issue", "create", "--repo", self.repo, "--title", title, "--body", body]
        if labels:
            for label in labels:
                cmd.extend(["--label", label])

        result = run_gh_command(cmd)
        if result.returncode != 0:
            raise RuntimeError(f"GitHub CLI issue create failed: {result.stderr.strip()}")

        output = result.stdout.strip()
        match = re.search(r"/issues/(\d+)$", output)
        if not match:
            raise RuntimeError(f"Could not extract issue number from output: {output}")

        number = int(match.group(1))
        issue_data = self.view(number, refresh=True)
        self._invalidate_index_cache()
        return issue_data

    def view(self, number: int, refresh: bool = False) -> Dict[str, Any]:
        """Fetch issue details with read-through local cache."""
        cache_path = self._issue_cache_path(number)
        if not refresh and cache_path.exists():
            try:
                with open(cache_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass

        fields = "number,title,body,state,labels,url,createdAt,updatedAt,comments"
        cmd = [
            "issue",
            "view",
            str(number),
            "--repo",
            self.repo,
            "--json",
            fields,
        ]
        result = run_gh_command(cmd)
        if result.returncode != 0:
            raise RuntimeError(f"Failed to view issue #{number}: {result.stderr.strip()}")

        data: Dict[str, Any] = json.loads(result.stdout)
        if "labels" in data and isinstance(data["labels"], list):
            data["labels"] = [
                l["name"] if isinstance(l, dict) and "name" in l else str(l)
                for l in data["labels"]
            ]

        with open(cache_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        return data

    def list(self, state: str = "open", refresh: bool = False) -> List[Dict[str, Any]]:
        """List issues with caching."""
        index_path = self._index_cache_path()
        if not refresh and index_path.exists():
            try:
                with open(index_path, "r", encoding="utf-8") as f:
                    index_data = json.load(f)
                    if index_data.get("state") == state and "issues" in index_data:
                        return index_data["issues"]
            except Exception:
                pass

        fields = "number,title,state,labels,updatedAt"
        cmd = [
            "issue",
            "list",
            "--repo",
            self.repo,
            "--state",
            state,
            "--json",
            fields,
        ]
        result = run_gh_command(cmd)
        if result.returncode != 0:
            raise RuntimeError(f"Failed to list issues: {result.stderr.strip()}")

        issues: List[Dict[str, Any]] = json.loads(result.stdout)
        for issue in issues:
            if "labels" in issue and isinstance(issue["labels"], list):
                issue["labels"] = [
                    l["name"] if isinstance(l, dict) and "name" in l else str(l)
                    for l in issue["labels"]
                ]

        with open(index_path, "w", encoding="utf-8") as f:
            json.dump({"state": state, "issues": issues}, f, ensure_ascii=False, indent=2)

        return issues

    def edit(
        self,
        number: int,
        title: Optional[str] = None,
        body: Optional[str] = None,
        add_labels: Optional[List[str]] = None,
        remove_labels: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Edit an issue on GitHub and refresh local cache."""
        cmd = ["issue", "edit", str(number), "--repo", self.repo]
        if title:
            cmd.extend(["--title", title])
        if body:
            cmd.extend(["--body", body])
        if add_labels:
            for l in add_labels:
                cmd.extend(["--add-label", l])
        if remove_labels:
            for l in remove_labels:
                cmd.extend(["--remove-label", l])

        result = run_gh_command(cmd)
        if result.returncode != 0:
            raise RuntimeError(f"Failed to edit issue #{number}: {result.stderr.strip()}")

        issue_data = self.view(number, refresh=True)
        self._invalidate_index_cache()
        return issue_data

    def close(self, number: int, comment: Optional[str] = None) -> Dict[str, Any]:
        """Close an issue on GitHub and update local cache."""
        cmd = ["issue", "close", str(number), "--repo", self.repo]
        if comment:
            cmd.extend(["--comment", comment])

        result = run_gh_command(cmd)
        if result.returncode != 0:
            raise RuntimeError(f"Failed to close issue #{number}: {result.stderr.strip()}")

        cache_path = self._issue_cache_path(number)
        cached_data: Dict[str, Any] = {}
        if not cache_path.exists():
            try:
                cached_data = self.view(number, refresh=True)
            except Exception:
                cached_data = {}
        else:
            try:
                with open(cache_path, "r", encoding="utf-8") as f:
                    cached_data = json.load(f)
            except Exception:
                pass

        if cached_data:
            cached_data["state"] = "CLOSED"
            with open(cache_path, "w", encoding="utf-8") as f:
                json.dump(cached_data, f, ensure_ascii=False, indent=2)
        else:
            if cache_path.exists():
                cache_path.unlink(missing_ok=True)

        self._invalidate_index_cache()
        return cached_data

    def delete(self, number: int, confirm: bool = False) -> bool:
        """Permanently delete an issue on GitHub and purge from cache."""
        if not confirm:
            raise ValueError(f"Confirmation required to delete issue #{number}")

        cmd = ["issue", "delete", str(number), "--repo", self.repo, "--yes"]
        result = run_gh_command(cmd)
        if result.returncode != 0:
            raise RuntimeError(f"Failed to delete issue #{number}: {result.stderr.strip()}")

        cache_path = self._issue_cache_path(number)
        if cache_path.exists():
            try:
                os.remove(cache_path)
            except OSError:
                pass

        self._invalidate_index_cache()
        return True


def format_issue_summary(issue: Dict[str, Any]) -> str:
    """Format single-line summary of an issue."""
    labels = issue.get("labels", [])
    labels_str = f" [{', '.join(labels)}]" if labels else ""
    return f"#{issue.get('number')} ({issue.get('state')}){labels_str}: {issue.get('title')}"


def format_issue_detail(issue: Dict[str, Any]) -> str:
    """Format full details of an issue for terminal view."""
    lines = [
        f"Issue #{issue.get('number')}: {issue.get('title')}",
        f"State: {issue.get('state')}",
        f"URL: {issue.get('url', '')}",
        f"Created: {issue.get('createdAt', '')}",
        f"Updated: {issue.get('updatedAt', '')}",
    ]
    labels = issue.get("labels", [])
    if labels:
        lines.append(f"Labels: {', '.join(labels)}")

    lines.append("")
    lines.append("Description:")
    body = issue.get("body", "").strip()
    if body:
        lines.extend(f"  {line}" for line in body.splitlines())
    else:
        lines.append("  (No description provided)")

    comments = issue.get("comments", [])
    if comments:
        lines.append("")
        lines.append(f"Comments ({len(comments)}):")
        for c in comments:
            author = c.get("author", {}).get("login", "unknown")
            created = c.get("createdAt", "")
            lines.append(f"  --- {author} at {created} ---")
            c_body = c.get("body", "").strip()
            lines.extend(f"    {line}" for line in c_body.splitlines())

    return "\n".join(lines)


def normalize_issue_args(raw_args: List[str]) -> List[str]:
    """Normalize raw CLI args so 'forgeflow issue --title ...' maps to 'forgeflow issue create --title ...'."""
    if not raw_args:
        return ["--help"]

    subcommands = {"create", "list", "view", "edit", "close", "delete"}
    first = raw_args[0]

    # If first arg is a known subcommand or help flag, keep as is
    if first in subcommands or first in {"-h", "--help"}:
        return list(raw_args)

    # If flags like --repo are specified before subcommand
    # e.g., ['--repo', 'owner/repo', '--title', 'foo'] or ['--title', 'foo']
    # Check if any element is a subcommand
    has_subcommand = any(arg in subcommands for arg in raw_args)
    if not has_subcommand:
        # Prepend 'create' as default action
        return ["create"] + list(raw_args)

    return list(raw_args)


def handle_issue_command(args: argparse.Namespace) -> None:
    """Execute issue command based on parsed arguments."""
    tracker = IssueTracker(repo=args.repo)

    if args.issue_command == "create":
        body = args.body
        if args.body_file:
            if not args.body_file.exists():
                print(f"Error: Body file '{args.body_file}' does not exist.", file=sys.stderr)
                sys.exit(1)
            try:
                body = args.body_file.read_text(encoding="utf-8")
            except Exception as e:
                print(f"Error reading body file '{args.body_file}': {e}", file=sys.stderr)
                sys.exit(1)
        issue = tracker.create(args.title, body, args.labels)
        if getattr(args, "json", False):
            print(json.dumps(issue, ensure_ascii=False, indent=2))
        else:
            print(f"Created and cached: {format_issue_summary(issue)}")
            print(f"등록된 issue는 GitHub 사이트에서 확인할 수 있습니다: {issue.get('url', '')}")

    elif args.issue_command == "view":
        issue = tracker.view(args.number, refresh=args.refresh)
        if getattr(args, "json", False):
            print(json.dumps(issue, ensure_ascii=False, indent=2))
        else:
            print(format_issue_detail(issue))

    elif args.issue_command == "edit":
        body = args.body
        if getattr(args, "body_file", None):
            if not args.body_file.exists():
                print(f"Error: Body file '{args.body_file}' does not exist.", file=sys.stderr)
                sys.exit(1)
            try:
                body = args.body_file.read_text(encoding="utf-8")
            except Exception as e:
                print(f"Error reading body file '{args.body_file}': {e}", file=sys.stderr)
                sys.exit(1)
        if not any([args.title, body, args.add_labels, args.remove_labels]):
            print(
                "Error: At least one field (--title, --body, --body-file, --add-label, --remove-label) must be specified to edit.",
                file=sys.stderr,
            )
            sys.exit(1)
        issue = tracker.edit(
            args.number,
            title=args.title,
            body=body,
            add_labels=args.add_labels,
            remove_labels=args.remove_labels,
        )
        if getattr(args, "json", False):
            print(json.dumps(issue, ensure_ascii=False, indent=2))
        else:
            print(f"Updated and cached: {format_issue_summary(issue)}")

    elif args.issue_command == "list":
        issues = tracker.list(state=args.state, refresh=args.refresh)
        if getattr(args, "json", False):
            print(json.dumps(issues, ensure_ascii=False, indent=2))
        else:
            if not issues:
                print(f"No issues found (state: {args.state}).")
            else:
                for issue in issues:
                    print(format_issue_summary(issue))

    elif args.issue_command == "close":
        issue = tracker.close(args.number, comment=args.comment)
        if getattr(args, "json", False):
            print(json.dumps(issue, ensure_ascii=False, indent=2))
        else:
            print(f"Closed and cached: {format_issue_summary(issue)}")

    elif args.issue_command == "delete":
        tracker.delete(args.number, confirm=args.yes)
        if getattr(args, "json", False):
            print(json.dumps({"status": "deleted", "number": args.number}, ensure_ascii=False, indent=2))
        else:
            print(f"Deleted issue #{args.number} from GitHub and local cache.")
