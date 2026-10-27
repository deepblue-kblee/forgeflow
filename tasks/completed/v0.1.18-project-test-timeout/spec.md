# Functional Specification: Support Project-Level Regression Test Timeout

- **Release ID**: `v0.1.18-project-test-timeout`
- **Tier**: `Tier 3 (Core / Governance Configuration & Runtime Test Runner)`
- **Author**: Antigravity
- **Date**: 2026-10-27
- **Target Component**: `src/forgeflow/runner.py`, `src/forgeflow/diagnostics.py`, `src/forgeflow/_version.py`, `tests/test_runner.py`

## 1. 개요 및 배경 (Overview & Context)

ForgeFlow의 `RuntimeTestRunner.run_tests()`는 엄격 감사(`strict audit`) 및 자가 치유 루프(Loop 2) 수행 시 타깃 프로젝트의 단위/회귀 테스트를 실행한다. 현재 구현에서는 `timeout=60.0`으로 고정되어 있어 타깃 프로젝트 단위에서 타임아웃 임계값을 설정할 수 없다.

이로 인해 Memograph와 같이 회귀 테스트 스위트 전체(407건)가 약 71.7초에 걸쳐 정상 통과함에도 불구하고, 60초 하드코딩 제한으로 인해 가짜 타임아웃(False Timeout) 실패가 발생하는 문제가 제기되었다 (GitHub Issue #6).

장기 실행 테스트는 설치된 아티팩트 검증, 복구 시나리오, 쿼리 보안 경계 등 핵심적인 회귀 안전선을 보호하므로 테스트를 임의로 생략할 수 없다. 따라서 프로젝트별 거버넌스 설정(`.forgeflow.json`)을 통해 안전하게 타임아웃을 상향 조정할 수 있는 기능이 필요하다.

## 2. 요구사항 및 사용자 가치 (Requirements & User Value)

- **FR-01 (프로젝트별 타임아웃 오버라이드 지원)**:
  타깃 프로젝트의 `.forgeflow.json`에 `governance.test_timeout_seconds` 설정이 명시된 경우, `RuntimeTestRunner.run_tests()`는 해당 초 단위 값을 `subprocess.run(..., timeout=...)`에 적용해야 한다.
- **FR-02 (안전한 기본값 보존)**:
  해당 설정이 명시되지 않은 프로젝트에서는 기존의 60.0초 타임아웃 제한을 그대로 유지하여 전역 기본값 변경으로 인한 의도치 않은 회귀를 방지한다.
- **FR-03 (엄격한 설정 유효성 검증 및 Fail-Closed)**:
  잘못된 설정 값(불리언, 비숫자 문자열, NaN/Infinity 등 비유한값, 0 이하의 값)이 지정된 경우, 이를 조용히 묵인하거나 기본값으로 은폐하지 않고 즉시 명확하고 조치 가능한 `ValueError` 설정 오류로 차단한다.
- **FR-04 (진단 엔진 연동)**:
  `forgeflow doctor`(`SystemDiagnostics`)에서 `.forgeflow.json`의 `test_timeout_seconds` 설정을 검사하여, 유효하지 않은 값이 감지되면 이상 징후(`INVALID_CONFIG_DETECTED`)로 보고하고 조치 가이드를 제공한다.
- **FR-05 (Zero-Dependency 원칙 및 호환성)**:
  Python 3.10+ 표준 라이브러리(`json`, `math`, `typing`, `pathlib`)만으로 동작하며 기존 `run_tests` API 시그니처와 100% 호환성을 유지한다.

## 3. 계획된 변경 경로 (Planned Paths)

- `src/forgeflow/_version.py`
- `src/forgeflow/runner.py`
- `src/forgeflow/diagnostics.py`
- `src/forgeflow/templates/spec/FLOW_SPEC.md`
- `src/forgeflow/templates/spec/CHANGELOG.md`
- `docs/spec/CHANGELOG.md`
- `tests/test_runner.py`
- `tasks/in-progress/v0.1.18-project-test-timeout/*`

## 4. 인수 조건 (Acceptance Criteria)

- [x] **AC-01 (설정 기반 오버라이드 정상 동작)**: `.forgeflow.json`에 `governance.test_timeout_seconds: 120`이 구성된 프로젝트에서 `RuntimeTestRunner.run_tests()`가 120초 타임아웃으로 실행된다.
- [x] **AC-02 (기본값 폴백 보존)**: 설정이 없거나 `.forgeflow.json`이 존재하지 않는 경우 기본값 60.0초가 정확히 적용된다.
- [x] **AC-03 (잘못된 설정 거부 및 오류 발생)**: `test_timeout_seconds` 값이 `True`, `False`, `"60"`, `0`, `-15`, `float('inf')`, `float('nan')`인 경우 명확한 `ValueError`를 발생시킨다.
- [x] **AC-04 (진단 엔진 사전 검출)**: `DiagnosticAnalyzer.analyze()`에서 잘못된 `test_timeout_seconds` 값을 감지하여 WARNING 이상 징후를 등록한다.
- [x] **AC-05 (테스트 스위트 커버리지 및 전체 통과)**: 신규 단위 테스트가 `tests/test_runner.py`에 추가되고 전체 단위 테스트(318건) 및 `forgeflow check --all --strict`가 결함 없이 🟢 통과한다.
