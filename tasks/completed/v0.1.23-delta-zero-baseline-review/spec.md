# Functional Specification: Delta-Zero Modified Scope Review and Multi-set Matching

- **Release ID**: `v0.1.23-delta-zero-baseline-review`
- **Tier**: `Tier 3 (Core / Reviewer Engine & Governance Control)`
- **Author**: Antigravity
- **Date**: 2026-11-01
- **Target Component**: `src/forgeflow/_version.py`, `src/forgeflow/reviewer.py`, `src/forgeflow/renderer.py`, `tests/test_reviewer.py`, `src/forgeflow/spec/VERSION`, `src/forgeflow/CHANGELOG.md`, `docs/CHANGELOG.md`, `.forgeflow/config.json`

## 1. 개요 및 배경 (Overview & Context)

`v0.1.22`에서 도입된 `--findings-baseline` 모드는 기준선 대비 무관한 기존 Warning을 성공적으로 면제했으나, 개발자가 수정한 함수(`MODIFIED_SCOPE`) 내에 기존 Warning이 잔존하는 경우 무조건 Gate 2 strict 검사를 차단(Fail-Closed)했습니다.
이로 인해 100줄짜리 복잡한 레거시 함수에 1줄의 버그 수정이나 로깅을 추가했을 뿐인데, 함수 전체의 기존 스멜을 전부 리팩토링해야만 Gate 2가 통과되어 작업 범위가 과도하게 폭발(Scope Creep)하는 마찰이 발견되었습니다.

본 릴리즈는 수정된 함수 내에 위치한 기존 Warning이라도, 변경 전과 비교하여 경고 수량이 새로 추가되지 않고 비증가(Delta-Zero)를 유지한다면 Gate 2 통과(리포트에는 잔존 주의 표시)를 허용함으로써 실무적 마찰을 해소합니다.
동시에 `collections.Counter` 기반의 Multi-set 슬롯 매칭을 적용하여, 동일 함수 내에서 동일한 유형의 Warning이 N개에서 N+1개로 증가하거나 신규 Warning이 추가될 때는 즉시 엄격 차단(Fail-Closed)합니다.

## 2. 요구사항 및 기능 명세 (Requirements & Specifications)

- **FR-01 (Delta-Zero Warning 비증가 허용)**:
  - 수정한 함수(`MODIFIED_SCOPE`) 내에 기존 Warning이 존재하더라도, 기준선 대비 수량이 증가하지 않았다면 Gate 2 strict 검사를 통과시킨다.
- **FR-02 (Multi-set Counter 기반 슬롯 매칭)**:
  - 기준선 Warning들을 `Counter` 다중 집합으로 집계하여, 후보 코드에서 동일한 fingerprint가 발견될 때마다 슬롯을 1개씩 차감 소비한다.
  - 슬롯을 초과하여 발생한 Warning이나 새로운 Warning은 `new_warnings`로 분류하여 즉시 차단한다.
- **FR-03 (리포트 및 감사 표시 투명성)**:
  - 수정 영역 내 잔존 경고는 `modified_scope_warnings`로 집계하여 리포트와 터미널에 주의/감사 기록으로 명확히 구분 출력한다.
- **FR-04 (Zero-Dependency & Fail-Closed 무결성)**:
  - 파이썬 표준 라이브러리(`collections.Counter`)만으로 구현하며 신규 결함은 엄격 차단한다.

## 3. 계획된 변경 경로 (Planned Paths)

- `src/forgeflow/_version.py`
- `src/forgeflow/reviewer.py`
- `src/forgeflow/renderer.py`
- `src/forgeflow/spec/VERSION`
- `src/forgeflow/CHANGELOG.md`
- `docs/CHANGELOG.md`
- `.forgeflow/config.json`
- `tests/test_reviewer.py`
- `tasks/completed/v0.1.23-delta-zero-baseline-review/*`

## 4. 인수 조건 (Acceptance Criteria)

- [x] **AC-01 (수정된 함수 내 기존 Warning 비증가 시 통과)**: 기존 Warning이 존재하는 함수를 수정하더라도 경고가 추가되지 않는다면 strict 검사를 통과한다.
- [x] **AC-02 (수정된 함수 내 신규 Warning 추가 시 차단)**: 기존 Warning이 존재하는 함수에 신규 Warning이 1건이라도 추가되면 strict 검사가 실패한다.
- [x] **AC-03 (동일 유형 Warning 슬롯 초과 차단)**: 동일 함수 내에서 동일한 유형의 Warning이 N개에서 N+1개로 증가할 경우 정확히 신규 Warning으로 검출되어 차단된다.
- [x] **AC-04 (리포트 통계 분리 표시)**: 수정 영역 잔존 경고(`modified_scope_warnings`)가 리포트 및 터미널에 주의 항목으로 정상 표기된다.
