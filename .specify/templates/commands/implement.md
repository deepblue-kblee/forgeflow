---
description: Execute task implementation with Gate 1 enforcement and autonomous healing loop
---

## Pre-Execution Checks
1. Gate 1 Approval: Verify `tasks/in-progress/<release-id>/GATE1_REVIEW.md` exists with status `APPROVED`.
2. Workspace Isolation: Verify work is being conducted on branch `feat/<release-id>`.

## Implementation Directives
- Follow `tasks.md` sequentially in TDD fashion.
- Inner Loop (Loop 2): Autonomously analyze, fix, and re-test without stopping on failures (budget: 5 attempts).
- Checkpoint Commits: Create a clean git commit each time a discrete task (`- [ ] Task N.N`) and its tests 100% pass.
- Rollback: If code becomes corrupted during remediation, revert to the last clean task checkpoint.
