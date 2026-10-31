# Functional Specification: Support auto_create_branch Governance Configuration

- **Release ID**: `v0.1.19-auto-create-branch-option`
- **Tier**: `Tier 3 (Core / Governance Configuration & Implementation Control)`
- **Author**: Antigravity
- **Date**: 2026-10-31
- **Target Component**: `src/forgeflow/scaffold.py`, `src/forgeflow/lifecycle.py`, `src/forgeflow/harness.py`, `src/forgeflow/diagnostics.py`, `src/forgeflow/cli.py`, `src/forgeflow/_version.py`, `tests/test_scaffold.py`, `tests/test_harness.py`, `tests/test_diagnostics.py`

## 1. 개요 및 배경 (Overview & Context)

ForgeFlow의 기존 구현 순서 및 명세는 Stage 3 격리 구현 단계 진입 시 무조건 `feat/<release-id>` 브랜치를 자동 분기(`git checkout -b feat/<release-id>`)하도록 규정되어 있다. 

그러나 실제 AI 에이전트 협업 환경에서는 Claude Code, OpenCode 또는 사용자가 사전에 Git worktree를 구성하여 격리된 작업 디렉토리에서 작업을 수행하는 경우가 빈번하다. 이러한 환경에서 ForgeFlow가 별도 브랜치를 다시 생성하면 worktree와 중복 브랜치가 엉키고 워킹 트리가 복잡해지는 문제가 발생한다.

또한 향후 프로젝트별로 브랜치 자동 분기 정책을 기본 활성화하고자 할 때 `AGENTS.md` 같은 지침 문서를 매번 수정하거나 프롬프트를 덧붙이지 않고, 리포지토리의 설정 파일(`.forgeflow.json`)만으로 단일 진실 공급원(SSOT)으로서 일관되게 제어할 수 있어야 한다.

따라서 작업 디렉토리의 거버넌스 설정(`.forgeflow.json`)에 `auto_create_branch` 옵션을 도입하여 기본적으로 브랜치 자동 분기를 생략하고, 필요 시 켜거나 사용자의 명시적 요청에 따라 유연하게 분기할 수 있도록 개선한다.

## 2. 요구사항 및 사용자 가치 (Requirements & User Value)

- **FR-01 (설정 옵션 도입 및 false 기본값)**:
  `.forgeflow.json`의 `governance.auto_create_branch` 옵션을 지원한다. 해당 옵션이 명시되지 않거나 `.forgeflow.json`이 누락된 경우 기본값은 `false`로 동작한다.
- **FR-02 (브랜치 자동 분기 Skip 제어)**:
  `auto_create_branch`가 `false`인 경우, Stage 3 진입 시 별도 격리 브랜치 생성을 건너뛰고(skip) 현재 체크아웃된 브랜치(worktree)에서 구현 및 TDD 체크포인트를 그대로 진행한다.
- **FR-03 (사용자 명시적 오버라이드 지원)**:
  설정 파일에서 `auto_create_branch: false`이더라도 사용자가 CLI 실행 시 명시적 플래그(예: `forgeflow task create <id> --branch` 또는 `forgeflow release create <id> --branch`)를 주거나 에이전트에게 명시적으로 요청한 경우에는 브랜치를 생성하여 전환한다.
- **FR-04 (단일 진실 공급원 및 지침 오염 방지)**:
  프로젝트별 브랜치 생성 정책은 오직 `.forgeflow.json`의 `governance.auto_create_branch`를 통해서만 제어되며, `AGENTS.md`나 프롬프트에 불필요한 규칙을 중복 기록하지 않는다.
- **FR-05 (안전한 라이프사이클 종료 Fast-Path)**:
  별도 브랜치를 생성하지 않고 작업한 경우(현재 브랜치와 task branch가 동일하거나 task branch가 생성되지 않은 경우), `forgeflow lifecycle close` 실행 시 브랜치 삭제 실패나 worktree 충돌 오류 없이 깨끗하게 릴리즈를 종료(Fast-Path)한다.
- **FR-06 (엄격한 타입 검증 및 진단)**:
  `auto_create_branch` 값은 엄격히 `bool` 타입이어야 하며(`True` 또는 `False`), 비불리언 값(문자열, 숫자 등)이 지정된 경우 명확한 `ValueError`로 fail-closed 차단하고 `forgeflow doctor`에서 이상 징후로 검출한다.
- **FR-07 (Zero-Dependency 원칙 및 100% 호환성)**:
  Python 3.10+ 표준 라이브러리만으로 구현하며 기존 기능 및 테스트 스위트와 100% 호환된다.

## 3. 계획된 변경 경로 (Planned Paths)

- `src/forgeflow/_version.py`
- `src/forgeflow/scaffold.py`
- `src/forgeflow/lifecycle.py`
- `src/forgeflow/harness.py`
- `src/forgeflow/diagnostics.py`
- `src/forgeflow/cli.py`
- `src/forgeflow/templates/spec/FLOW_SPEC.md`
- `src/forgeflow/templates/spec/SPECKIT_HOOKS_AND_NORMS.md`
- `src/forgeflow/templates/spec/CHANGELOG.md`
- `docs/spec/FLOW_SPEC.md`
- `docs/spec/SPECKIT_HOOKS_AND_NORMS.md`
- `docs/spec/CHANGELOG.md`
- `tests/test_scaffold.py`
- `tests/test_harness.py`
- `tests/test_diagnostics.py`
- `tasks/in-progress/v0.1.19-auto-create-branch-option/*`

## 4. 인수 조건 (Acceptance Criteria)

- [x] **AC-01 (설정 미지정 시 기본값 false)**: `.forgeflow.json`에 `auto_create_branch`가 없거나 파일이 없으면 `resolve_auto_create_branch()`가 `False`를 반환한다.
- [x] **AC-02 (설정 파일 명시 반영)**: `"auto_create_branch": true`일 때 `True`를, `"auto_create_branch": false`일 때 `False`를 정확히 반환한다.
- [x] **AC-03 (비불리언 값 엄격 검증)**: `"auto_create_branch"`에 문자열 `"true"`, 숫자 `1` 등이 입력된 경우 `ValueError`를 발생시키고 `forgeflow doctor`에서 `INVALID_CONFIG_DETECTED` 이상 징후로 검출된다.
- [x] **AC-04 (브랜치 분기 생략 및 현재 브랜치 바인딩)**: `auto_create_branch: false`인 환경에서 lifecycle 생성 및 태스크 진행 시 브랜치가 분기되지 않고 현재 브랜치가 identity에 정상 결속된다.
- [x] **AC-05 (Close 시 안전한 단일 브랜치 처리)**: 분기 브랜치 없이 완료된 릴리즈에 대해 `forgeflow lifecycle close`가 브랜치 삭제 오류 없이 안전하게 종료된다.
- [x] **AC-06 (전체 테스트 100% 통과)**: 신규 단위 테스트 추가 및 전체 테스트 스위트(318+건)와 `forgeflow check --all --strict`가 결함 없이 🟢 통과한다.
