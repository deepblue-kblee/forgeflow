# Gate 2 QA Sign-off: Support Project-Level Regression Test Timeout

- **Release ID**: `v0.1.18-project-test-timeout`
- **Tier**: `Tier 3 (Core / Governance Configuration & Runtime Test Runner)`
- **QA Sign-off Date**: 2026-10-27
- **Verdict**: `APPROVED`
- **Regression Test Result**: 318 passed in 14.17s (100% Pass)

## 1. 품질 및 테스트 검증 요약

- **프로젝트별 타임아웃 오버라이드 검증 (AC-01)**:
  - `test_run_tests_propagates_configured_timeout`: `.forgeflow.json`의 `governance.test_timeout_seconds: 150` 설정이 `subprocess.run(..., timeout=150.0)`에 올바르게 주입됨을 확인.
  - `test_valid_integer_timeout`, `test_valid_float_timeout`: 정수 및 부동소수점 타임아웃 설정 파싱 확인.
- **기본값 60초 폴백 보존 검증 (AC-02)**:
  - `test_default_timeout_when_no_config`: `.forgeflow.json`이 존재하지 않을 때 기본값 60.0초 유지 확인.
  - `test_default_timeout_when_key_absent`: `.forgeflow.json`에 `test_timeout_seconds` 키가 없을 때 기본값 60.0초 유지 확인.
- **Fail-Closed 엄격 유효성 검증 (AC-03)**:
  - `test_reject_bool_values`: `True`, `False` 불리언 값에 대해 `ValueError` 발생 확인.
  - `test_reject_string_values`: `"120"` 문자열 값에 대해 `ValueError` 발생 확인.
  - `test_reject_zero_and_negative_values`: `0`, `-1`, `-50.0` 값에 대해 `ValueError` 발생 확인.
  - `test_reject_malformed_json`: 비정상 JSON 파일에 대해 `ValueError` 발생 확인.
- **타임아웃 만료 시 리포팅 검증**:
  - `test_run_tests_timeout_expired_reports_custom_timeout`: 타임아웃 만료 시 에러 출력에 실제 적용된 커스텀 타임아웃 초(`Tests timed out after 120.0 seconds.`)가 정확히 반영됨을 확인.
- **진단 엔진 연동 검증 (AC-04)**:
  - `test_diagnostics_detects_invalid_test_timeout`: 음수/비정상 타임아웃이 설정된 경우 `DiagnosticAnalyzer.analyze()`가 `INVALID_TEST_TIMEOUT` WARNING 이상 징후를 정확히 보고함을 확인.
- **전체 회귀 테스트 스위트 통과 (AC-05)**:
  - 총 318개 단위 테스트 100% 통과 (0 failures, 0 errors).

## 2. 변경 파일 무결성 대조

계획된 변경 경로(Planned Paths)와 실제 변경 파일이 100% 일치함:
- `src/forgeflow/_version.py`
- `src/forgeflow/runner.py`
- `src/forgeflow/diagnostics.py`
- `src/forgeflow/templates/spec/FLOW_SPEC.md`
- `src/forgeflow/templates/spec/CHANGELOG.md`
- `docs/spec/CHANGELOG.md`
- `docs/spec/FLOW_SPEC.md`
- `tests/test_runner.py`
- `tasks/in-progress/v0.1.18-project-test-timeout/*`
