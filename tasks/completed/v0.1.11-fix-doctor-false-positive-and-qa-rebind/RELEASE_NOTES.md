# Release Notes: ForgeFlow v0.1.11

- **Release ID**: `v0.1.11-fix-doctor-false-positive-and-qa-rebind`
- **Release Version**: `v0.1.11`
- **Release Date**: 2026-10-24
- **Related Issues**: GitHub Issue #3, GitHub Issue #4

---

## 1. 개요 (Overview)

ForgeFlow v0.1.11은 진단 엔진(`forgeflow doctor`)의 거짓 양성(False Positive) 결함(Issue #4)과, Gate 2 통과 후 패키지 메타데이터 부기 작업 시 발생하던 불필요한 전체 QA 재바인딩 병목 현상(Issue #3)을 해결했습니다.

---

## 2. 주요 개선 사항 (Key Improvements)

1. **`forgeflow doctor` LEGACY_CONFIG_DETECTED 오탐 제거 (Issue #4)**:
   - `diagnostics.py`의 `forgeflow_version != "0.1.0"` 하드코딩 검사를 버전 튜플 비교(`parse_version_tuple(v) < (0, 1, 0)`)로 교정.
   - `0.1.1` 이상의 최신 버전으로 정상 갱신된 환경에서 레거시 경고가 발생하는 오탐 결함 원천 해소.
2. **하네스 화이트리스트 확장 및 패키지 메타데이터 안전 승계 (Issue #3)**:
   - `harness.py`의 `_candidate_disallowed_paths`에 최신 Spec Kit 하이브리드 표준 문서(`spec.md`, `plan.md`, `tasks.md`, `GATE1_REVIEW.md`, `CHANGE_NOTE.md`, `checklist.md`, `status.md`)를 전수 반영.
   - 실제 런타임 코드와 테스트가 불변인 상태에서 패키지 부기(Bookkeeping: 체크리스트 체크, 릴리즈 노트 작성 등)가 수행되어도 QA-SHA 바인딩이 안전하게 보존됨.
3. **릴리즈 ID 조기 사전 검증 (Preflight Check)**:
   - `forgeflow check --stage 2` 시점에 `validate_release_id`를 선제 검증하여, 유효하지 않은 릴리즈 ID 형식을 조기 차단하고 사후 디렉토리 변경 마찰을 원천 예방.
4. **거버넌스 승인 권한 경계 명문화**:
   - `FLOW_SPEC.md` 및 `GATES_AND_LOOPS.md`에 Gate 2(기술적 품질 검증에 따른 에이전트/QA 자동 승인)와 Gate 3(사용자 최종 배포 패키지 Go/No-Go 인간 승인)의 역할 책임을 단일 진실 공급원(SSOT)으로 분리 명시.
