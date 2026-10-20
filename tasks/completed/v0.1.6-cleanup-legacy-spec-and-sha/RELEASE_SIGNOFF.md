# Release Sign-Off: Comprehensive Cleanup of Legacy Documentation & SHA Mechanisms

- **Release ID**: `v0.1.6-cleanup-legacy-spec-and-sha`
- **Target Version**: `v0.1.6`
- **Release Sign-Off Date**: 2026-10-21
- **Risk Tier**: **Tier 3 (Critical / Core Governance Specification & Constitution Surface)**
- **Gate 1 Status**: APPROVED
- **Gate 2 QA Status**: APPROVED (`b926f827b633bf20435be8eb653feebff53245d4`)
- **Gate 3 Verdict**: **APPROVED (Ready for Promotion)**

---

## 1. 릴리즈 성과 요약

1. **원자적 루프 정의 현대화**:
   - Loop 2 자가 치유 시 단위 테스트가 실패할 때마다 `git commit (새 SHA 발행)`을 강제하던 과거 규정을 삭제하고, 루프 내부에서는 작업 트리에서 수정-테스트를 반복한 뒤 모든 테스트가 통과된 최종 시점에 원자적 구현 커밋 1개를 생성하도록 단일화.
2. **`spec.md` 해시 바인딩(Spec SHA256) 잔재 완전 제거**:
   - 사양 문서, 스키마 예시, 템플릿, 안내 문서에서 해시 바인딩 설명을 영구 삭제.
3. **거버넌스 용어 및 Stage 표기 단일화**:
   - 모호한 '사전 심사' 표현을 'Gate 1: 명세 승인 (Spec Sign-Off)'으로 완전 통일.
   - 하이브리드 워크플로우에 맞춰 구현 단계를 'Stage 3'으로 일치화.
4. **배포 사양 및 버전 관리 정비**:
   - `DISTRIBUTION_SPEC.md`에 전역 `upgrade`와 로컬 `update`, 스마트 파사드 `/update-forgeflow`의 명확한 역할 분리 반영.
   - 2026-10-20 이전 과거 버전 번호(v0.22/v0.23 등)를 v0.1.x 표준으로 청산.
   - `CHANGELOG.md`에 v0.1.2부터 v0.1.6까지의 최신 릴리즈 이력 완비.
5. **자체 버전 갱신**:
   - `ForgeFlow v0.1.6` 판올림 완료.

---

## 2. 최종 릴리즈 승인 서명 (Gate 3 Sign-Off)

- **Release Status**: **SEALED & PROMOTED**
- **Approved by**: AI Agent (Antigravity) & User Explicit Approval
