# Functional Specification: Baseline-Aware Strict Review for Gate 2

- **Release ID**: `v0.1.22-baseline-aware-strict-review`
- **Tier**: `Tier 3 (Core / Reviewer Engine & Governance Control)`
- **Author**: Antigravity
- **Date**: 2026-11-01
- **Target Component**: `src/forgeflow/_version.py`, `src/forgeflow/smell_detector.py`, `src/forgeflow/reviewer.py`, `src/forgeflow/review_scanner.py`, `src/forgeflow/cli.py`, `src/forgeflow/renderer.py`, `tests/test_reviewer.py`, `tests/test_smell_detector.py`, `tests/test_cli.py`

## 1. 개요 및 배경 (Overview & Context)

현재 `forgeflow review --strict`는 검사 대상 파일(git diff로 선택된 파일 또는 명시된 파일) 전체를 분석하여, 단 하나의 Warning(경고)이라도 존재하면 검토를 실패로 판정합니다.
이로 인해 test-only 변경이나 국소 수정 작업 시에도, 변경하지 않은 함수의 기존 Warning(예: 기존 fixture의 실제 파일시스템 경계 검증, 변경 범위 밖 helper/traversal, `from __future__ import annotations`에 대한 분석기 오탐 등)으로 인해 Gate 2가 차단되는 심각한 마찰이 발생하고 있습니다.
이는 개발자나 에이전트가 무관한 코드까지 수정을 확대하거나, 분석기 통과만을 위해 구조적 왜곡을 가하게 만드는 안티패턴을 초래합니다.

본 과업은 기존 `--strict`의 "전체 선택 범위 Warning 0건" 검사 의미와 하위 호환성을 100% 보존하면서, Gate 2에서 안전하게 기준선(revision)과 비교하여 신규 회귀만을 차단할 수 있는 `--findings-baseline <ref>` 모드를 제공합니다.
이를 통해 기존의 무관한 Warning은 감사 리포트에 온전히 보존하되 Gate 2 통과를 허용하고, 신규 발생 또는 재발한 Warning, 그리고 변경된 함수 내에 존재하는 기존 Warning은 엄격하게 차단(Fail-Closed)합니다.

## 2. 요구사항 및 기능 명세 (Requirements & Specifications)

- **FR-01 (분석기 오탐 해소 - from __future__ import annotations)**:
  - `SmellDetector`의 `Unused Import` 검출기에서 `from __future__ import ...` 문은 컴파일러 지시자이므로 미사용 임포트 경고 대상에서 제외한다.
  - 파일·규칙 전체를 끄는 광범위한 예외가 아닌, 해당 지시자에 국한된 정확한 오탐 수정이어야 한다.
- **FR-02 (스코프 추적 및 구조적 Finding 식별)**:
  - `CodeSmell`에 `scope: str = ""` 필드를 추가하여, AST 탐색 중 클래스명/함수명 계층(`ClassName.method_name` 또는 `func_name`, 최상위는 `""`)을 자동 기록한다.
  - finding 비교 시 줄 번호(`line_no`) 변경만으로 신규 경고로 오탐되지 않도록 `(file_rel_path, smell_type, scope, message_signature)` 기반의 구조적 fingerprint를 산출하여 기준선 finding과 안정적으로 매칭한다.
- **FR-03 (기준선 비교 옵션 --findings-baseline <ref>)**:
  - `forgeflow review` CLI 및 `ReviewEngine.run_review`에 `findings_baseline: Optional[str]` 옵션을 추가한다.
  - `git rev-parse --verify <ref>^{commit}`을 통해 유효한 git ref인지 사전에 엄격히 검증하고, 유효하지 않은 ref일 경우 fail-closed 에러 처리한다.
  - 대상 파일들에 대해 baseline revision 시점의 파일 내용을 `git show <ref>:<rel_path>`로 추출하여 baseline smells를 산출한다. (신규 추가된 파일은 baseline smells 0건).
- **FR-04 (동적 Finding 분류 및 Gate 2 차단 규칙)**:
  - **CRITICAL**: 기준선 유무와 무관하게 무조건 차단 (effective_critical == 0 필수).
  - **NEW / REGRESSED Warning**: 기준선에 없던 신규 Warning이거나 과거 해결된 Warning이 재발한 경우 strict 차단.
  - **MODIFIED_SCOPE Warning**: 기준선에 이미 존재하던 Warning이라도 해당 함수/메서드가 이번 변경(diff)으로 수정된 경우, 면제되지 않고 strict 차단(재검토 대상).
  - **BASELINE_EXISTING Warning**: 기준선에 이미 존재하며, 이번 변경에서 수정되지 않은 함수/코드에 위치한 Warning은 strict 차단 대상에서 제외(면제)하되, 리포트에는 계속 투명하게 표시.
  - **RESOLVED Warning**: 기준선에는 있었으나 후보 revision에서 해소된 Warning 통계 집계.
- **FR-05 (기존 --strict 무변경 보존 - 하위 호환성)**:
  - `--findings-baseline` 옵션이 지정되지 않은 경우, 기존의 `strict` 동작(전체 Warning 0건이어야 통과)은 100% 동일하게 유지된다.
- **FR-06 (감사 리포트 및 메트릭 기록 - Audit Trail)**:
  - `ReviewResult` 및 마크다운/JSON 리포트에 baseline ref, candidate SHA, critical/baseline/new/modified_scope/resolved finding 수량을 정확히 기록한다.
- **FR-07 (Zero-Dependency & Fail-Closed 원칙)**:
  - 모든 구현은 파이썬 표준 라이브러리(`ast`, `subprocess`, `dataclasses`, `pathlib`)만으로 구현한다.

## 3. 계획된 변경 경로 (Planned Paths)

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

## 4. 인수 조건 (Acceptance Criteria)

- [x] **AC-01 (새로운 Warning 추가 시 차단)**: Warning이 없는 기준선 대비 후보 코드에서 새 Warning이 추가되면 `--findings-baseline` strict 검사가 실패한다.
- [x] **AC-02 (무관한 기존 Warning 허용 및 결과 표시)**: 기준선에 이미 존재하던 Warning만 유지되고 해당 코드가 수정되지 않았다면 strict 검사를 통과하며, 해당 Warning은 결과 리포트에 온전히 표시된다.
- [x] **AC-03 (해결된 Warning 재발 시 차단)**: 기준선에서 해결되었던 Warning이 후보에서 다시 발생하면 새 finding으로 검출되어 strict 검사가 실패한다.
- [x] **AC-04 (수정된 함수의 기존 Warning 차단)**: 기존 Warning이 존재하는 함수가 변경된 경우, 자동 면제되지 않고 `MODIFIED_SCOPE`로 분류되어 strict 검사가 실패한다.
- [x] **AC-05 (줄 번호 이동 내성)**: 코드 추가/삭제로 인해 기존 finding의 line number만 이동한 경우 새 Warning으로 중복 집계되지 않고 기존 finding으로 정확히 인식된다.
- [x] **AC-06 (기존 strict 하위 호환성)**: `--findings-baseline`을 지정하지 않은 기존 `forgeflow review --strict`는 전체 Warning 0건 검사를 그대로 수행한다.
- [x] **AC-07 (리포트 증적 무결성)**: 결과 리포트 및 JSON에 baseline ref, candidate SHA, Critical 및 baseline/new/modified/resolved 카운트가 명시된다.
- [x] **AC-08 (Future import 오탐 해소)**: `from __future__ import annotations` 구문이 `Unused Import` 경고를 유발하지 않는다.
