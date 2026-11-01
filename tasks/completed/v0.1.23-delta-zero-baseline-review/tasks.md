# Tasks & Implementation Checklist: Delta-Zero Modified Scope Review

- **Release ID**: `v0.1.23-delta-zero-baseline-review`

---

## 1. 구현 태스크 분해 (Atomic Tasks)

- [x] **Task 1: Multi-set Counter 슬롯 매칭 엔진 구현**
  - [x] 1.1: `ReviewEngine.run_review`에 `collections.Counter` 기반 기준선 Warning 다중 집합 집계 적용
  - [x] 1.2: 후보 Warning 탐색 시 슬롯 차감 및 슬롯 초과분 `new_smells` 판정 로직 구현
  - [x] 1.3: `resolved_warnings` 수량을 미소비된 기준선 슬롯 합계로 정확히 계산

- [x] **Task 2: Strict 판정 완화 및 리포트 통계 갱신**
  - [x] 2.1: Strict 통과 조건을 `effective_critical == 0 and new_w == 0`으로 변경 (Delta-Zero 허용)
  - [x] 2.2: Markdown 리포트 및 터미널 렌더링에 `MODIFIED_SCOPE_EXISTING` 주의/감사 통계 분리 표기

- [x] **Task 3: 단위 테스트 및 회귀 검증**
  - [x] 3.1: `test_baseline_aware_modified_function_with_non_increasing_warning_passes` 작성 및 통과
  - [x] 3.2: `test_baseline_aware_modified_function_with_new_warning_fails` 작성 및 통과
  - [x] 3.3: 전체 343개 단위 테스트 100% 통과

- [x] **Task 4: 버전 승격 및 패키지 밀봉**
  - [x] 4.1: `src/forgeflow/_version.py` 버전 `0.1.23` 승격
  - [x] 4.2: 하네스 감사 `forgeflow check --all --strict` 전수 🟢 ALL PASSED 확인
