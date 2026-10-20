# Specification: Comprehensive Cleanup of Legacy Documentation & SHA Mechanisms

- **Release ID**: `v0.1.6-cleanup-legacy-spec-and-sha`
- **Created Date**: 2026-10-21
- **Risk Tier**: **Tier 3 (Critical / Core Governance Specification & Constitution Surface)**

---

## 1. 개요 및 목적 (Overview & Purpose)

이전 릴리즈(v0.1.2~v0.1.5)를 통해 `spec.md` 해시 바인딩 제거, CLI 명령어 정비, 전역 `upgrade`와 로컬 `update` 명령어 분리 등의 개선이 이루어졌으나, 사양 문서 및 헌법 템플릿에 과거 유산과 잔재가 남아있음이 확인되었다.
본 릴리즈는 프레임워크 전수 문서, 헌법 템플릿, 번들 템플릿, 스캐폴더 코드를 대상으로 남아있는 과거 유산을 완전히 청산하고 단일 진실 공급원(SSOT) 정합성을 100% 회복한다.

---

## 2. 주요 정비 대상 및 요구사항 (Requirements)

1. **원자적 루프 정의 정정**:
   - 자가 치유(Loop 2) 루프마다 `git commit (새 SHA 발행)`을 강제하던 규정을 삭제하고, 루프 내부에서는 작업 트리에서 수정-테스트를 반복한 뒤 모든 테스트가 통과된 최종 시점에만 원자적 구현 커밋 1개를 생성하도록 정정.
2. **`spec.md` 해시 바인딩(Spec SHA256) 잔재 완전 제거**:
   - `FLOW_SPEC.md`, `GATES_AND_LOOPS.md`, `README.md` 등에 남아있는 해시 바인딩 설명과 스키마 행 삭제.
3. **과거 버전 번호 및 예시 일괄 교정**:
   - `FLOW_SPEC.md`, `GOVERNANCE.md` 내의 2026-10-20 이전 과거 버전 번호(v0.22/v0.23, v0.5.0/v0.4.1 예시)를 v0.1.x 표준으로 교정.
4. **모호한 '사전 심사' 표현 교정**:
   - `FLOW_SPEC.md`, `GATES_AND_LOOPS.md`, `README.md`의 '사전 심사'를 공식 표준 명칭인 'Gate 1: 명세 승인 (Spec Sign-Off)'으로 통일.
5. **Stage 번호 정정**:
   - `GATES_AND_LOOPS.md`, `REFACTORING_GUIDE.md`에서 구현 단계를 가리키던 'Stage 4'를 Spec Kit 하이브리드 표준인 'Stage 3'으로 정정.
6. **`DISTRIBUTION_SPEC.md` 및 `CHANGELOG.md` 최신화**:
   - 배포 규격서에 `upgrade`(전역)와 `update`(로컬), `/update-forgeflow`(스마트 파사드)의 명확한 역할 분리 반영.
   - 변경 이력 문서에 v0.1.2부터 v0.1.5까지의 릴리즈 내역 누락분 보강.
7. **헌법 및 스캐폴더 동기화**:
   - `.specify/memory/constitution.md`, `src/forgeflow/scaffold.py`, `scripts/install-skills.sh`, `src/forgeflow/templates/spec/*` 전수 동기화.
8. **버전 판올림**:
   - `src/forgeflow/_version.py`를 `0.1.6`으로 갱신.

---

## 3. 인수 조건 (Acceptance Criteria)

- **AC-1**: `FLOW_SPEC.md`, `.specify/memory/constitution.md`, `scaffold.py`, `install-skills.sh`의 제3조에서 루프 중 `git commit (새 SHA 발행)` 강제 문구가 제거되고, 구현 완료 시 단일 커밋 생성으로 정정된다.
- **AC-2**: `FLOW_SPEC.md`, `GATES_AND_LOOPS.md`, `README.md`에서 `Spec SHA256` 해시 바인딩 및 '사전 심사' 문구가 완전히 제거되고 '명세 승인(Spec Sign-Off)'으로 단일화된다.
- **AC-3**: `FLOW_SPEC.md`와 `GOVERNANCE.md`의 과거 버전 표기(`0.23.0`, `0.22.0` 등)가 v0.1.x 표준으로 교정된다.
- **AC-4**: `GATES_AND_LOOPS.md`와 `REFACTORING_GUIDE.md`의 구현 단계 표기가 `Stage 3`으로 일치된다.
- **AC-5**: `DISTRIBUTION_SPEC.md`에 `upgrade`와 `update`의 대칭 구조가 명확히 기술되고, `CHANGELOG.md`에 최신 릴리즈 이력이 완비된다.
- **AC-6**: `docs/spec/`과 `src/forgeflow/templates/spec/` 간의 100% 바이트 일치가 유지되며 (`test_scaffold.py` 통과), 전체 단위 테스트 100% 통과 및 `forgeflow check --all --strict` 🟢 ALL PASSED를 달성한다.
