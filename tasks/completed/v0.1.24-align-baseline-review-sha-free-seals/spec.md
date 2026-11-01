# Functional Specification: Align Baseline-Aware Gate 2 with SHA-Free Lifecycle Seals

- **Release ID**: `v0.1.24-align-baseline-review-sha-free-seals`
- **Tier**: `Tier 3 (Core / Architecture & Governance Control Plane)`
- **Author**: Antigravity
- **Date**: 2026-11-01
- **Target Components**:
  - `src/forgeflow/_version.py`
  - `src/forgeflow/lifecycle.py`
  - `src/forgeflow/harness.py`
  - `src/forgeflow/cli.py`
  - `src/forgeflow/templates/QA_SIGNOFF.md`
  - `src/forgeflow/templates/RELEASE_SIGNOFF.md`
  - `src/forgeflow/spec/GATES_AND_LOOPS.md`
  - `docs/spec/GATES_AND_LOOPS.md`
  - `src/forgeflow/spec/FLOW_SPEC.md`
  - `docs/spec/FLOW_SPEC.md`
  - `src/forgeflow/spec/VERSION`
  - `docs/spec/VERSION`
  - `src/forgeflow/CHANGELOG.md`
  - `docs/CHANGELOG.md`
  - `.forgeflow/config.json`
  - `tests/test_lifecycle_harness.py`
  - `tests/test_lifecycle_cli.py`
  - `tests/test_reviewer.py`

## 1. 개요 및 배경 (Overview & Context)

ForgeFlow `v0.1.22` 및 `v0.1.23`에서는 이슈 #7을 통해 Gate 2의 핵심 간극을 해소했습니다:
- `review --strict --findings-baseline <ref>` 모드는 Critical 0건 및 신규 Warning 0건(v0.1.23 Delta-Zero 포함)일 때 strict 검사를 통과하며, 기존 findings는 기준선에 의해 분류되어 리포트에 보존됩니다.
- 기존의 `review --strict`는 선택된 검사 범위 전체의 Warning 0건을 요구하는 기본 정책을 그대로 유지합니다.

그러나 다운스트림 라이프사이클 제어 평면과 공식 Gate 안내 사양은 여전히 이러한 기준선 검토 기능 및 Git-SHA 바인딩을 금지하는 프로젝트 아키텍처 정책과 완벽히 정렬되지 않았습니다:
1. **공식 Gate 2 사양 및 템플릿의 정책 구분 누락**: Gate 2 지침이 여전히 raw `review --strict` (Warning 0)만을 설명하고 있으며, 승인된 baseline을 기록하고 검증하는 방법이 템플릿에 표준화되어 있지 않습니다.
2. **라이프사이클 Evidence v2의 엄격한 Git 커밋 SHA 강제**: Lifecycle Evidence v2가 `Base-SHA`와 `QA-SHA`를 로컬 커밋 SHA로 강제하고, `lifecycle package-review`와 `lifecycle seal`이 커밋 존재 및 QA-to-candidate Git 범위 바인딩을 요구합니다.
3. **불일치로 인한 차단**: 프로젝트가 Git-SHA 바인딩을 금지하는 승인된 아키텍처 정책(ADR 001 실용적 4대 불변식)을 채택하고 baseline-aware review를 성공적으로 통과하더라도, 불필요한 commit-SHA 바인딩을 도입하지 않고는 package review 및 seal로 전진할 수 없는 구조적 모순이 발생합니다.

본 릴리즈는 Gate 2 사양 및 템플릿에 raw strict와 baseline-aware strict의 두 가지 지원 정책을 명확히 정의하고, Git-SHA 바인딩을 배제하는 프로젝트를 위한 일관된 SHA-free lifecycle evidence 경로(`Binding-Policy: sha-free`)를 validators, lifecycle transitions, templates, specs 전반에 걸쳐 완비합니다.

## 2. 요구사항 및 기능 명세 (Requirements & Specifications)

- **FR-01 (Gate 2 공식 명세 및 QA 템플릿 정비)**:
  - 공식 Gate 2 사양(`GATES_AND_LOOPS.md`, `FLOW_SPEC.md`) 및 QA 템플릿(`QA_SIGNOFF.md`)에서 두 가지 지원 리뷰 정책을 명확히 구분하여 기술한다:
    - `raw strict`: 선택된 검사 범위의 모든 Warning이 0건이어야 함 (`review --strict`). 기본값 유지.
    - `baseline-aware strict`: Critical 0건, 신규 Warning 0건이어야 함 (`review --strict --findings-baseline <ref>`). 기존 Warning은 기준선에 의해 분류·보존되며, v0.1.23 Delta-Zero(수정 스코프 내 기존 경고 비증가 허용)가 적용됨.
  - baseline이 승인되고 기록되는 방식(Gate 1 합의된 ref, 리포트 및 QA_SIGNOFF 내 baseline ref, candidate 식별자, Critical/baseline/new/resolved/modified-scope 집계)을 명시한다.
- **FR-02 (SHA-Free Lifecycle Evidence 경로 제공)**:
  - Evidence v2에 `Binding-Policy: sha-free` (기본값: `git-sha`) 정책 지원을 추가한다.
  - `Binding-Policy: sha-free`인 경우:
    - `Base-SHA` 및 `QA-SHA`에 `sha-free` (또는 `none`, `SHA-FREE`) 값을 허용한다.
    - `Reviewer` 및 `Verification` 필드의 `qa-sha`에 `sha-free` 값을 허용하거나 생략을 허용한다.
    - Git 커밋 SHA 검증 대신 실용적 4대 안전 불변식(필수 서명 승인, 100% 테스트 통과, Clean Working Tree, 패키지 매니페스트 무결성)으로 품질을 보증한다.
- **FR-03 (라이프사이클 전이 및 CLI 정렬)**:
  - `lifecycle package-review`:
    - `qa_sha` 인자가 누락되거나 `--sha-free` / `qa_sha="sha-free"`인 경우, evidence의 SHA-free 정책을 인식하여 커밋 검증 없이 clean worktree 및 패키지 무결성을 확인하고 `PACKAGE_REVIEW_PENDING`으로 정상 전이한다.
  - `lifecycle seal`:
    - `candidate_sha` 인자가 누락되거나 `--sha-free` / `candidate_sha="sha-free"`인 경우, SHA-free 정책을 인식하여 candidate 커밋 검증 및 range binding 없이 clean worktree 및 패키지 매니페스트를 검증하고 `PACKAGE_SEALED`로 밀봉한다.
  - `lifecycle complete` (`completion_ready`):
    - SHA-free 정책 적용 시 `qa_sha_missing`, `candidate_missing` 에러 없이 라이프사이클 완료를 허용한다.
- **FR-04 (기존 v2 Sealed 릴리즈 100% 하위 호환 보존)**:
  - 기존의 40자리 hex commit SHA를 사용하는 sealed 릴리즈는 기존 스키마 및 검증 규칙 그대로 유지되어 사후 감사(`forgeflow check --all --strict`)에서 일체의 회귀 없이 🟢 통과해야 한다.

## 3. 계획된 변경 경로 (Planned Paths)

- `src/forgeflow/_version.py`
- `src/forgeflow/lifecycle.py`
- `src/forgeflow/harness.py`
- `src/forgeflow/cli.py`
- `src/forgeflow/templates/QA_SIGNOFF.md`
- `src/forgeflow/templates/RELEASE_SIGNOFF.md`
- `src/forgeflow/spec/GATES_AND_LOOPS.md`
- `docs/spec/GATES_AND_LOOPS.md`
- `src/forgeflow/spec/FLOW_SPEC.md`
- `docs/spec/FLOW_SPEC.md`
- `src/forgeflow/spec/VERSION`
- `docs/spec/VERSION`
- `src/forgeflow/CHANGELOG.md`
- `docs/CHANGELOG.md`
- `.forgeflow/config.json`
- `tests/test_lifecycle_harness.py`
- `tests/test_lifecycle_cli.py`
- `tests/test_reviewer.py`
- `tasks/in-progress/v0.1.24-align-baseline-review-sha-free-seals/*`

## 4. 인수 조건 (Acceptance Criteria)

- [x] **AC-01 (공식 문서 및 템플릿 정비)**: 공식 사양서 및 QA 템플릿에 raw strict와 baseline-aware strict의 차이 및 기준선 승인/기록 방식이 명시되고, baseline 리포트는 모든 기존 finding을 계속 감사 가능하게 보존한다.
- [x] **AC-02 (신규 경고 없는 baseline Gate 2의 SHA-free package review 진입)**: baseline-aware Gate 2에서 신규 Warning이 0건인 경우 QA approval을 Git commit SHA에 바인딩하지 않고 package review에 진입할 수 있으며, 신규 Warning 추가 시에는 차단된다.
- [x] **AC-03 (SHA-free 라이프사이클 전이 및 밀봉 완결)**: SHA-free 정책 하에서 커밋 SHA나 diff 범위 감사 없이 명시적 게이트 승인, 100% 테스트 통과, clean worktree 검사, 패키지 매니페스트 무결성 검증을 통해 `package-review`, Gate 3 seal, completion이 일관되게 완료된다.
- [x] **AC-04 (기존 v2 릴리즈 하위 호환성 및 테스트 커버리지)**: 기존 v2 sealed 릴리즈들이 변함없이 감사 통과하며, 신규 테스트 스위트가 warning delta 및 전체 SHA-free 라이프사이클 전이를 빈틈없이 검증한다.
