# Gate 2 QA Sign-off: Baseline-Aware Strict Review for Gate 2

- **Release ID**: `v0.1.22-baseline-aware-strict-review`
- **Tier**: `Tier 3 (Core / Reviewer Engine & Governance Control)`
- **QA Sign-off Date**: 2026-11-01
- **Verdict**: `APPROVED`
- **Regression Test Result**: 342 passed in 15.80s (100% Pass)

## 1. 품질 및 테스트 검증 요약

- **새로운 Warning 추가 시 차단 검증 (AC-01)**:
  - `test_baseline_aware_clean_baseline_fails_on_new_warning`: Warning이 없는 기준선 대비 후보 코드에서 새 Warning(Silent Exception 등)이 추가되었을 때, `new_warnings=1`로 집계되며 strict 검사가 정확히 실패함을 검증.
- **무관한 기존 Warning 허용 및 결과 표시 검증 (AC-02)**:
  - `test_baseline_aware_unchanged_existing_warning_passes`: 기준선에 이미 존재하던 Warning이 유지되고 변경되지 않은 다른 함수만 수정된 경우, `exempt_warnings=1`, `new_warnings=0`, `modified_scope_warnings=0`으로 면제 승인되어 strict 통과함을 검증. 또한 결과 smells 목록에는 기존 Warning이 계속 정상 표시됨을 확인.
- **해결된 Warning 재발 시 차단 검증 (AC-03)**:
  - `test_baseline_aware_resolved_warning_reported`: 기준선에서 해결된 Warning이 후보에서 재발하면 새 finding으로 검출되어 strict 실패함을 확인.
- **수정된 함수의 기존 Warning 차단 검증 (AC-04)**:
  - `test_baseline_aware_modified_function_with_warning_fails`: 기존 Warning이 존재하는 함수가 수정된 경우, 자동 면제되지 않고 `modified_scope_warnings=1`로 분류되어 strict 검사가 차단(Fail-Closed)됨을 검증.
- **줄 번호 이동 내성 검증 (AC-05)**:
  - `test_baseline_aware_line_shift_does_not_duplicate_warning`: 코드 상단에 주석/코드가 추가되어 기존 함수의 line number가 이동하더라도, 구조적 fingerprint에 의해 새 Warning으로 중복 집계되지 않고 기존 경고로 매칭됨을 검증.
- **기존 strict 하위 호환성 검증 (AC-06)**:
  - `test_strict_without_baseline_fails_on_any_warning`: `--findings-baseline`이 지정되지 않은 기존 `forgeflow review --strict`는 Warning이 1건이라도 존재하면 100% 실패하는 기존 엄격 규칙을 유지함을 확인.
- **리포트 증적 무결성 검증 (AC-07)**:
  - `test_forgeflow_review_findings_baseline_cli`: CLI 실행 시 `findings_baseline`, `baseline_stats`가 JSON 및 마크다운 리포트에 정상 기록됨을 확인.
- **Future import 오탐 해소 검증 (AC-08)**:
  - `test_future_import_annotations_not_reported_as_unused`: `from __future__ import annotations` 구문이 `Unused Import` 경고를 유발하지 않음을 검증.
- **전체 단위 및 회귀 테스트 통과**:
  - 총 342개 단위 테스트 100% 통과 (0 failures, 0 errors).

## 2. 변경 파일 무결성 대조

계획된 변경 경로(Planned Paths)와 실제 변경 파일이 100% 일치함:
- `src/forgeflow/_version.py`
- `src/forgeflow/smell_detector.py`
- `src/forgeflow/reviewer.py`
- `src/forgeflow/review_scanner.py`
- `src/forgeflow/cli.py`
- `src/forgeflow/renderer.py`
- `src/forgeflow/spec/VERSION`
- `src/forgeflow/CHANGELOG.md`
- `docs/CHANGELOG.md`
- `.forgeflow/config.json`
- `tests/test_reviewer.py`
- `tests/test_smell_detector.py`
- `tests/test_cli.py`
- `tasks/in-progress/v0.1.22-baseline-aware-strict-review/*`
