# Implementation plan

Design artifacts live here; execution state belongs to .forgeflow/workflows/.

1. Research: inspect all active spec/instruction surfaces and entrypoints; record contradictions and independent review findings. Keep completed release evidence immutable.
2. Add a small workflow API/CLI alongside strict lifecycle compatibility. One JSON state per task stores plan, completion conditions, required commands/results, repository/source/target identity, owner, delegated operations, baseline identity and integration/cleanup receipts. Reuse stdlib and existing safe-path utilities where suitable.
3. Standalone Git operations use explicit allowlists of paths/operations, verify current source/target and relevant content, preserve other dirty work, and avoid automatic branch/worktree allocation. Host operations remain a generic pending action/receipt boundary without Codex APIs in core. PR mode delegates through the host; local merge uses Git.
4. Pin a content-addressed local runtime/spec/template snapshot for executable continuity. New tasks pin the actual source package. Drift blocks with the snapshot command; explicit adoption updates only affected verification. Update refuses silent active-task migration, including legacy unfinished packages.
5. Rewrite hybrid default scaffold around config, pinned entrypoint/spec and optional Spec Kit assets; preserve every existing user file by default. Existing strict CLI/audit remains available. Remove date-based amnesia/overwrite assumptions and current-only default instructions.
6. Rewrite all official specs, AGENTS, README, task guard, live constitution/hooks/session state, ADR applicability and generated skills. Keep source-of-truth documents concise and refer to owning contracts. Mechanically generate packaged spec copies. Preserve historical changelog entries as history.
7. Add acceptance-driven integration coverage; update old tests only for intentional contract changes. Verify all tests and source entrypoint; independent final reviews; bump patch to 0.1.25 per existing patch policy; commit and push branch only.

## Planned paths
AGENTS.md, README.md, TODO.md, .forgeflow/config.json, .specify/**, docs/spec/**, docs/adr/**, docs/session-state/**, tasks/README.md, docs/design/lean-development-flow/**, src/forgeflow/{workflow.py,runtime.py,cli.py,scaffold.py,diagnostics.py,_version.py,legacy_templates.py,CHANGELOG.md}, src/forgeflow/{spec,adr,templates}/**, scripts/**, install.sh, pyproject.toml, tests/**.

## Review boundary
The existing Tier 3 design review is retained for this transition before src edits. The user's approval covers the proposed redesign and branch push; no repeated overall approval is required. Reviewers must identify concrete gaps against the acceptance criteria rather than reimpose the superseded default ceremony.
