# Technical Plan: Support Project-Level Regression Test Timeout

- **Release ID**: `v0.1.18-project-test-timeout`
- **Tier**: `Tier 3 (Core / Governance Configuration & Runtime Test Runner)`

## 1. 아키텍처 및 설계 원칙

### 1.1 타임아웃 해석 및 검증 로직 (`resolve_test_timeout`)
`RuntimeTestRunner` 내에 프로젝트별 타임아웃을 해석하고 검증하는 전용 정적 메서드 `resolve_test_timeout(repo_root: Path) -> float`를 구현한다.
- 기본값: `DEFAULT_TEST_TIMEOUT = 60.0`
- `.forgeflow.json` 파일이 없거나 디렉터리가 아니면 기본값 `60.0` 반환.
- `.forgeflow.json` 파일이 존재할 경우:
  - JSON 파싱 오류 시 `ValueError` 발생.
  - 최상위 객체가 딕셔너리가 아니거나 `governance.test_timeout_seconds` 키가 없으면 기본값 `60.0` 반환.
  - 키가 존재할 경우 엄격한 타입 및 값 검증(Strict Validation):
    1. 불리언 검증: `isinstance(val, bool)`인 경우 `ValueError` 발생 (Python에서 `bool`이 `int`의 하위 클래스이므로 `True/False`가 숫자로 오인되는 것 방지).
    2. 숫자 타입 검증: `not isinstance(val, (int, float))`인 경우 `ValueError` 발생.
    3. 유한성 검증: `not math.isfinite(val)` (`inf`, `-inf`, `nan`)인 경우 `ValueError` 발생.
    4. 양수 검증: `val <= 0`인 경우 `ValueError` 발생.
  - 모든 검증을 통과하면 `float(val)` 반환.

### 1.2 `run_tests` 연동 및 전파
`RuntimeTestRunner.run_tests(repo_root, explicit_python=None, test_dir=None, timeout=None)`:
- `timeout` 매개변수가 `None`이면 `RuntimeTestRunner.resolve_test_timeout(repo_root)`를 호출하여 유효 타임아웃(`effective_timeout`) 결정.
- `timeout` 매개변수에 명시적인 숫자 값이 전달된 경우 이를 우선 적용 (테스트/CLI 인라인 오버라이드 지원).
- `subprocess.run(..., timeout=effective_timeout)`에 적용.
- `subprocess.TimeoutExpired` 발생 시 `output`에 실제 적용된 `effective_timeout`을 표기.

### 1.3 진단 엔진 연동 (`SystemDiagnostics`)
`src/forgeflow/diagnostics.py`의 진단 항목에 `.forgeflow.json` 설정 검증을 확장:
- `governance.test_timeout_seconds`가 존재하지만 유효하지 않은 값인 경우 `INVALID_TEST_TIMEOUT` 경고 이상 징후 등록.
- 사용자에게 친절한 교정 안내 제공.

### 1.4 하위 호환성 및 Zero-Dependency
- Python 표준 라이브러리(`json`, `math`, `typing`, `pathlib`)만 사용.
- 기존의 모든 `run_tests` 호출 지점(기본 60초 가정)과 100% 호환성 유지.
