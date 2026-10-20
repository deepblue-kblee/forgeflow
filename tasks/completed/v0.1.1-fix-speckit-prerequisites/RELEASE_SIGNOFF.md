# Release Sign-Off: Spec Kit Prerequisite Bundling & Date-Based Amnesia

**Release ID**: `v0.1.1-fix-speckit-prerequisites`  
**Target Version**: `v0.1.1`  
**Release Sign-Off Date**: 2026-10-20  
**Risk Tier**: **Tier 3 (Critical / Core / Governance Control-Plane)**  
**Gate 1 Status**: APPROVED  
**Gate 2 QA Status**: APPROVED (`0a7f248`)  
**Gate 3 Verdict**: **APPROVED (Ready for Promotion)**

---

## 1. 릴리즈 개요 및 성과 요약

GitHub Spec Kit과 ForgeFlow 하이브리드 거버넌스 구동 시 발생하던 핵심 블로커를 완벽히 해결하고 배포 무결성을 확립함:
1. **Spec Kit 필수 런타임 자산 번들링**:
   - `check-prerequisites.sh`, `common.sh`, `create-new-feature.sh`, `resolve-template.sh`, `setup-plan.sh`, `setup-tasks.sh` 6종 bash 스크립트를 프레임워크 내부에 번들링하여 `0o755` 실행 권한으로 자동 스캐폴딩.
   - `spec-template.md`, `plan-template.md`, `tasks-template.md`, `checklist-template.md` 마크다운 템플릿 번들링.
   - 후속 `/speckit.specify` ➔ `/speckit.clarify` ➔ `/speckit.plan` ➔ `/speckit.tasks` ➔ `/speckit.implement` 체인이 `exit 127` 없이 100% 매끄럽게 완주됨을 실전 도그푸딩으로 입증.
2. **거버넌스 엔진 하이브리드 지원**:
   - `validator.py` 및 `harness.py`에서 하이브리드 산출물(`spec.md`, `GATE1_REVIEW.md`, `plan.md`, `tasks.md`, `QA_SIGNOFF.md`, `RELEASE_SIGNOFF.md`)을 정식 지원하여 거버넌스 감사 🟢 ALL PASSED 달성.
3. **날짜 기반 과거 레거시 흔적 강제 폐기 (Date-Based Amnesia)**:
   - 2026-10-20 이전 생성된 모든 구버전 설정 감지 시 하위 호환을 배제하고 v0.1.0/v0.1.1 단일 규격으로 강제 재정립.
   - `AGENTS.md` 및 `SKILL.md`에 Amnesia Policy 명문화.

---

## 2. 검증 요약

- **단위/통합 테스트**: 269개 전원 통과 (Fail=0, Error=0)
- **하네스 게이트 감사**: `forgeflow check --all --strict` 🟢 ALL PASSED
- **실전 도그푸딩**: `.specify/scripts/bash/check-prerequisites.sh --json --paths-only` 및 `setup-plan.sh --json`, `setup-tasks.sh --json` 실행 성공 입증
- **로컬 배포 인스톨러**: `install.sh`를 통해 `ForgeFlow v0.1.1` 배포 및 스킬 동기화 완료

---

## 3. 최종 릴리즈 승인 서명 (Gate 3 Sign-Off)

- **Release Status**: **SEALED & PROMOTED**
- **Approved by**: AI Agent (Antigravity) & User Instruction
