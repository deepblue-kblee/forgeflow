# Release Sign-Off: Gate Clarity & Removal of Spec Hash Binding

- **Release ID**: `v0.1.2-clarify-gates-and-remove-spec-hash`
- **Target Version**: `v0.1.2`
- **Release Sign-Off Date**: 2026-10-20
- **Risk Tier**: **Tier 3 (Critical / Governance Control-Plane / Public Interface)**
- **Gate 1 Status**: APPROVED
- **Gate 2 QA Status**: APPROVED (`d5f1ad6`)
- **Gate 3 Verdict**: **APPROVED (Ready for Promotion)**

---

## 1. 릴리즈 성과 요약

1. **Gate 1/2/3 위치 및 승인 주체 명확화 (Issue #2 해결)**:
   - Stage(작업 수행 단계)와 Gate(승인 관문)를 명확히 분리하여 1:1 대응 표기.
   - 각 Gate의 Before, Run, Creates, User action, Done when, Unlocks를 담은 일람표 제공.
   - 문서 내 허위/미구현 명령(`forgeflow gate1 review`, `forgeflow gate2 signoff`)을 실제 CLI 명령어로 전면 교정.
2. **`spec.md` 해시 바인딩(Spec SHA256) 제거로 에이전트 마찰 원천 해소**:
   - 사소한 공백/오타/포맷팅 변경 시에도 해시가 깨져 Loop 3 무한 루프로 헛돌던 결함 영구 해소.
   - `GATE1_REVIEW.md`의 `APPROVED` 상태만으로 Gatekeeper 통과하도록 경량화.
3. **자체 버전 갱신**:
   - `ForgeFlow v0.1.2` 판올림 및 로컬 가상환경 배포 완료.

---

## 2. 최종 릴리즈 승인 서명 (Gate 3 Sign-Off)

- **Release Status**: **SEALED & PROMOTED**
- **Approved by**: AI Agent (Antigravity) & User Instruction
