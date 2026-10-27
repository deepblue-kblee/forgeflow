# Implementation Tasks: Support Project-Level Regression Test Timeout

- **Release ID**: `v0.1.18-project-test-timeout`
- **Tier**: `Tier 3 (Core / Governance Configuration & Runtime Test Runner)`

## Tasks

- [x] Task 1: `tests/test_runner.py`에 TDD 실패 테스트 케이스 작성 (Red)
  - `.forgeflow.json` 부재 또는 키 누락 시 60.0초 기본값 검증
  - `governance.test_timeout_seconds` 양수 정수/실수 오버라이드 검증
  - 비정상 값(불리언, 문자열, 음수, 0, 무한대, NaN)에 대한 `ValueError` 검증
  - `run_tests`의 `subprocess.run` 타임아웃 인자 전달 및 타임아웃 만료 시 메시지 검증
- [x] Task 2: `src/forgeflow/runner.py`에 타임아웃 해석 및 검증 로직 구현 (Green)
  - `DEFAULT_TEST_TIMEOUT = 60.0` 정의
  - `RuntimeTestRunner.resolve_test_timeout` 구현 (불리언 방어, 유한수 검증, 양수 검증)
  - `RuntimeTestRunner.run_tests`에 `effective_timeout` 해석 로직 연동
- [x] Task 3: `src/forgeflow/diagnostics.py`에 진단 규칙 연동
  - 유효하지 않은 `test_timeout_seconds` 설정 검출 및 WARNING 이상 징후 등록
- [x] Task 4: 문서 및 사양 갱신
  - `FLOW_SPEC.md`에 `governance.test_timeout_seconds` 스키마 반영
  - `CHANGELOG.md` 갱신
  - `src/forgeflow/_version.py` 버전 0.1.18 승격
- [x] Task 5: 전체 단위 테스트 및 하네스 게이트 검증
  - 306+개 단위 테스트 100% 통과 확인
  - `forgeflow check --stage 2` 및 `forgeflow check --all --strict` 🟢 ALL PASSED 확인
