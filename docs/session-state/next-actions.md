# Next Actions

## 현재 진행 과업 (Current In-Progress Tasks)

1. **마크다운 문서 전수 점검 및 최신화 (완료 단계)**:
   - `AGENTS.md`: 옛버전 산출물(`PRD.md`, `DESIGN.md`) 제거 및 최신 Spec Kit 하이브리드 아키텍처(`spec.md`, `plan.md`, `tasks.md`, `GATE1_REVIEW.md`, `QA_SIGNOFF.md`, `RELEASE_SIGNOFF.md`) 반영.
   - `AGENTS.md` & `SKILL.md`: 2026-10-20(v0.1.0 릴리즈일) 이전 과거 버전/흔적 강제 폐기 규범(Date-Based Amnesia Policy) 주입.
   - `README.md`, `session-state`: 최신 규격과 상태로 동기화.

2. **GitHub Issue #1 해결 (실전 Spec Kit 하이브리드 도그푸딩)**:
   - Spec Kit 스킬 체인(`/speckit-specify` ➔ `/speckit-clarify` ➔ Gate 1 ➔ `/speckit-plan` ➔ `/speckit-tasks` ➔ `/speckit-implement`)으로 실제 피쳐/이슈 수명주기 직접 구동.
   - `setup-forgeflow` 및 `scaffold_speckit_hybrid`에 누락된 `.specify/scripts/bash/*` 및 템플릿 번들링 구현.
   - 하이브리드 워크플로우 실제 동작 검증 및 `install.sh`/스킬 배포 완결.
