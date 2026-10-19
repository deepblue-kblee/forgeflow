---
description: Execute task implementation with Gate 1 enforcement and autonomous healing loop
---

## Pre-Execution Checks
1. Gate 1 Approval: Verify `tasks/in-progress/<release-id>/GATE1_REVIEW.md` exists with status `APPROVED`.
2. Spec Integrity: Ensure `spec.md` hash matches the signature in `GATE1_REVIEW.md`.

## Implementation Directives
- Follow `tasks.md` sequentially in TDD fashion.
- Do not stop on test failures; autonomously analyze, fix, re-test, and commit (Loop 2).
- Respect loop budget of 5 remediation attempts per error fingerprint.
