# Lean development flow

Workflow: lean. This transition design is not a strict release package.

## Authorization and scope
2026-11-02 사용자 승인: 설계 방향대로 모든 현행 스펙·지침·실제 실행 동작을 최신화하고 필요한 문서 재작성/삭제를 수행한다. 이 저장소의 codex/ branch에서 구현·검증·commit·origin push까지 수행한다. main merge, 전역 설치, 배포, 이슈 종결은 범위 밖이다.

## Contract change
Before: every change requires Gate 1/2/3 documents, package sealing, unconditional strict review guidance, current-only rules, and ambiguous Git cleanup.
After: the default workflow records one plan and execution state, requires scope/acceptance/checks before implementation and passing required checks plus explicit operation authority before integration. Spec Kit handles larger plans; project commands handle verification; the selected Git/host owner handles repository operations. Existing strict evidence remains readable and immutable; strict lifecycle remains an explicit compatibility path, never an implicit migration of active work.

## Acceptance criteria
1. A small change can plan, verify and finish readiness without three sign-off documents or a package seal. Required project checks cannot be bypassed by an empty task check list.
2. Host-owned existing checkouts never create another branch from auto_create_branch. Core exposes pending host operations, accepts verifiable execution receipts, and never invents cleanup success.
3. Standalone local merge supports explicit source, target and permissions without a PR; governance-only authority permits neither merge nor deletion. Commit/push/merge/cleanup authority is recorded once and reused.
4. Verification is tied to relevant working content and declared commands/environment, not ceremonial QA commit seals. Unrelated dirty files are preserved; related unstaged/untracked work is never silently staged/reset/stashed.
5. Ready, integrated and cleaned are distinct. After successful merge and failed cleanup, resume retries cleanup only and checks observed repository state.
6. Setup/update preserve user configuration, constitution, hooks and templates. No date-based deletion or forced constitution/ADR/hook injection in the default path.
7. Active work records a content identity for runtime/spec/templates. Global current changes, including same-version replacements, cannot silently change its rules. An executable local snapshot provides continuity; explicit adoption records rationale/impact.
8. docs/spec is the editing source; shipped spec copies are mechanically synchronized and checked. All active instructions, setup assets, generated skills and CLI help share the same default/strict boundary. Historical completed evidence is not rewritten.
9. Zero third-party runtime dependencies. Behavior tests cover owner boundaries, local integration, partial cleanup recovery, dirty preservation, update preservation, baseline drift and generated-skill consistency.

## Verification
Focused new workflow/scaffold/distribution tests, full Python unittest suite, source-entrypoint smoke in a disposable repository, legacy strict archive audit, generated-skill check and spec distribution equality. Independent Security/Reliability/Maintainability design and final reviews required for this governance control-plane change.
