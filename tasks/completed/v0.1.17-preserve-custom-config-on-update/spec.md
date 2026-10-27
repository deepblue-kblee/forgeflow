# Functional Specification: Preserve Custom Configuration on Update

- **Release ID**: `v0.1.17-preserve-custom-config-on-update`
- **Tier**: `Tier 1 (Minor / Fast-track)`
- **Author**: Antigravity
- **Date**: 2026-10-27
- **Target Component**: `src/forgeflow/scaffold.py`, `tests/test_update_cli.py`

## 1. 개요 및 배경 (Overview & Context)
ForgeFlow가 설치된 다운스트림 작업 리포지토리의 루트에는 프로젝트 거버넌스 설정 파일인 `.forgeflow.json`이 배치된다.
사용자는 작업 리포지토리의 필요에 따라 거버넌스 설정(예: `governance.strict_mode`, `governance.max_loop_budget`, 커스텀 `tasks_dir`, 사용자 정의 최상위 메타데이터/플러그인 설정 등)을 수정하여 사용할 수 있다.

그러나 기존의 `forgeflow update`(`TemplateScaffolder.update_repo_governance`) 및 `scaffold_speckit_hybrid`는 다음과 같은 결함과 위험이 존재한다:
1. `scaffold_speckit_hybrid(force=True)` 실행 시 최상위 키가 `forgeflow_version`, `governance`, `paths`로 하드코딩되어 있어, 사용자가 추가한 임의의 최상위 커스텀 키나 섹션이 덮어쓰기 과정에서 유실될 위험이 있다.
2. 프레임워크 새 버전에 새로운 기본 설정 키가 추가되었을 때 기존 사용자 설정을 파괴하지 않고 안전하게 병합하는 딥 머지(Deep Merge) 메커니즘이 부재하다.
3. 버전 정보(`forgeflow_version`)가 이미 최신 버전과 동일하고 설정 내용에 변경이 없는 경우에도 무조건 파일을 다시 쓰고 `updated_files`에 포함시키는 불필요한 덮어쓰기(unnecessary write)가 발생한다.

## 2. 요구사항 및 사용자 가치 (Requirements & User Value)
- **FR-01 (사용자 커스텀 값 100% 보존)**: `forgeflow update` 실행 시 사용자가 수정한 모든 key/value(최상위 키, 중첩된 딕셔너리 값)는 기본 템플릿 값에 의해 덮어써지지 않고 원형 그대로 보존되어야 한다.
- **FR-02 (새로운 기본 키 안전 병합)**: 프레임워크 신규 버전에 새로운 기본 설정 키가 도입된 경우, 기존 사용자 설정 키를 덮어쓰지 않고 누락된 신규 키만 안전하게 기본값으로 보강(Deep Merge with User Precedence)해야 한다.
- **FR-03 (불필요한 덮어쓰기 방지 및 멱등성)**: 버전 정보가 이미 최신이며 내용에 실질적인 변경이 없는 경우, 파일을 덮어쓰지 않고 `updated_files`에서도 제외해야 한다.
- **FR-04 (단일 모듈 국소 수정 및 하위 호환성)**: 기존 Zero-Dependency 원칙(Python 3.10+ 표준 라이브러리만 사용)을 준수하며, 기존 CLI 파라미터 및 반환 스키마와의 100% 호환성을 유지한다.

## 3. 계획된 변경 경로 (Planned Paths)
- `src/forgeflow/_version.py`
- `src/forgeflow/scaffold.py`
- `tests/test_update_cli.py`
- `docs/spec/CHANGELOG.md`
- `src/forgeflow/templates/spec/CHANGELOG.md`
- `tasks/in-progress/v0.1.17-preserve-custom-config-on-update/*`

## 4. 인수 조건 (Acceptance Criteria)
- [x] **AC-01 (사용자 커스텀 설정 100% 보존)**: `governance.strict_mode: false`, `governance.max_loop_budget: 12`, 커스텀 `tasks_dir`, 사용자 최상위 키/객체가 `forgeflow update` 실행 후에도 전혀 덮어써지지 않고 그대로 유지된다.
- [x] **AC-02 (새로운 기본 키 재귀적 보강)**: 새 기본 템플릿에만 존재하는 키는 기존 설정을 침해하지 않고 deep merge를 통해 누락 없이 추가된다.
- [x] **AC-03 (무변경 덮어쓰기 방지)**: 이미 버전이 최신이고 내용에 실질적인 변경이 없는 경우 `.forgeflow.json`을 다시 쓰지 않고 `updated_files` 목록에서도 제외된다.
- [x] **AC-04 (단위 및 회귀 테스트 통과)**: 신규 단위 테스트 4종을 포함하여 전체 단위 테스트 100% 통과 및 `forgeflow check --all --strict` 🟢 ALL PASSED를 달성한다.
