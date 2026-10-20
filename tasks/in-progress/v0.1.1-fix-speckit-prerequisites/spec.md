# Feature Specification: Spec Kit Prerequisite Bundling & Date-Based Amnesia Enforcement

**Feature Identifier**: `v0.1.1-fix-speckit-prerequisites`  
**Target Release**: `v0.1.1`  
**Created**: 2026-10-20  
**Status**: DRAFT (Stage 1: Specify)

---

## 1. 개요 및 목적 (Executive Summary & Problem Statement)

### 1.1 배경 및 현재 결함
ForgeFlow v0.1.0은 GitHub Spec Kit과의 하이브리드 거버넌스를 표방하며 공개되었으나, 실제 셋업 과정에서 두 가지 심각한 결함이 확인되었다:

1. **Spec Kit 필수 런타임 자산 누락 (Exit 127 블로커)**:
   * `setup-forgeflow` 및 `forgeflow init --speckit` 실행 시 `.specify/memory/constitution.md`, `.specify/extensions.yml`, `.specify/templates/commands/implement.md`만 생성되고, Spec Kit 공식 에이전트 스킬들(`speckit-clarify`, `speckit-plan`, `speckit-tasks` 등)이 반드시 요구하는 `.specify/scripts/bash/*` 스크립트와 필수 마크다운 템플릿(`spec-template.md`, `plan-template.md`, `tasks-template.md` 등)이 누락된다.
   * 이로 인해 사용자가 셋업 후 안내에 따라 `/speckit-clarify`나 `/speckit-plan`을 실행하면 bash 스크립트 부재로 즉시 `exit 127 (Command Not Found)`이 발생하여 전체 워크플로우가 차단된다.
2. **과거 버전 잔재 혼입 및 하위 호환성 혼선**:
   * 2026-10-20(v0.1.0 공식 릴리즈일) 이전에 작성된 비공개 프로토타입 이력(과거 v0.1.0 ~ v0.22.1)의 설정(`.forgeflow.json`)이나 산출물 문서(`PRD.md`, `DESIGN.md`), 과거 메모리가 남아 있을 경우 에이전트가 이를 참조하여 새 워크플로우와 충돌을 빚는다.
   * 과거 버전과의 불필요한 하위 호환성을 유지하려 하지 않고, 2026-10-20을 기준으로 과거 흔적을 전면 폐기(Date-Based Amnesia)하고 v0.1.0 표준으로 강제 재정립해야 한다.

### 1.2 목적 (Objectives)
- ForgeFlow 배포 패키지 및 스캐폴더 내부에 Spec Kit 필수 bash 스크립트 6종과 템플릿을 번들링하여, `setup-forgeflow` 또는 `forgeflow init --speckit` 1회 실행만으로 후속 `/speckit.specify` ➔ `/speckit.clarify` ➔ Gate 1 ➔ `/speckit.plan` ➔ `/speckit.tasks` ➔ `/speckit.implement` 체인이 단 한 번의 단절 없이 100% 매끄럽게 완주되도록 보장한다.
- 2026-10-20 이전의 레거시 설정 및 흔적을 감지 시 전면 폐기하고 v0.1.0 단일 규격으로 정렬하는 강제 규칙을 스킬과 CLI 엔진에 주입한다.

---

## 2. 사용자 시나리오 및 페르소나 (User Scenarios)

### 시나리오 1: 신규 프로젝트 하이브리드 초기화
* **사용자**: AI 에이전트를 통해 신규 프로젝트를 생성하는 엔지니어
* **행동**: 프로젝트 루트에서 `/setup-forgeflow` (또는 `forgeflow init --speckit`) 실행
* **결과**:
  * `.forgeflow.json`, `.specify/memory/constitution.md`, `.specify/extensions.yml`, `.specify/templates/commands/implement.md` 정상 생성
  * `.specify/scripts/bash/check-prerequisites.sh`, `common.sh`, `setup-plan.sh`, `setup-tasks.sh`, `create-new-feature.sh`, `resolve-template.sh` 생성 및 실행 권한(chmod +x) 부여
  * `.specify/templates/spec-template.md`, `plan-template.md`, `tasks-template.md`, `checklist-template.md` 정상 생성
  * 후속 `/speckit.specify` ➔ `/speckit-clarify` ➔ `/speckit-plan`이 에러 없이 즉시 구동됨

### 시나리오 2: 2026-10-20 이전 레거시가 혼입된 프로젝트 정비
* **사용자**: 과거 프로토타입 시절의 구버전 설정이나 메모리가 남아 있는 프로젝트를 인계받은 개발자
* **행동**: `/setup-forgeflow` 실행
* **결과**:
  * 2026-10-20 이전 레거시 설정 및 메모리를 감지하고 하위 호환을 시도하지 않고 즉시 폐기 및 클린업
  * v0.1.0 단일 표준 설정 및 하이브리드 런타임으로 즉각 초기화

---

## 3. 기능 요구사항 (Functional Requirements)

### FR-01: Spec Kit 핵심 런타임 bash 스크립트 번들링 및 배포
- 프레임워크 패키지 내부에 다음 6개 공식 bash 스크립트를 번들링해야 한다:
  1. `check-prerequisites.sh`: 사전 조건 및 feature.json 검증
  2. `common.sh`: 공통 유틸리티 및 JSON 헬퍼
  3. `create-new-feature.sh`: 피쳐 디렉토리 생성 및 번호 매김
  4. `resolve-template.sh`: 템플릿 리졸버
  5. `setup-plan.sh`: `/speckit-plan` 컨텍스트 및 경로 해석
  6. `setup-tasks.sh`: `/speckit-tasks` 템플릿 주입 및 체크리스트 해석
- `TemplateScaffolder.scaffold_speckit_hybrid` 및 `forgeflow init --speckit` 실행 시 대상 프로젝트의 `.specify/scripts/bash/` 아래에 위 6개 파일을 복사하고 실행 권한(`0o755`)을 부여해야 한다.

### FR-02: Spec Kit 표준 마크다운 템플릿 번들링 및 배포
- 프레임워크 패키지 내부에 다음 4개 공식 마크다운 템플릿을 번들링해야 한다:
  1. `spec-template.md`: 사용자 중심 기능 명세 템플릿
  2. `plan-template.md`: 아키텍처 및 기술 설계 템플릿
  3. `tasks-template.md`: TDD 원자적 태스크 체크리스트 템플릿
  4. `checklist-template.md`: 명세 품질 검증 체크리스트 템플릿
- 하이브리드 스캐폴딩 시 대상 프로젝트의 `.specify/templates/` 아래에 위 4개 파일을 생성해야 한다.

### FR-03: 2026-10-20 이전 과거 버전/흔적 강제 폐기 규범 (Date-Based Amnesia)
- `setup-forgeflow` 스킬 및 CLI는 2026-10-20 이전에 생성된 설정(`.forgeflow.json`), 메모리, 구버전 산출물(`PRD`, `DESIGN` 등)을 발견하면 하위 호환 마이그레이션을 거부하고 폐기·클린업 후 v0.1.0 표준으로 재작성하도록 강제해야 한다.
- 에이전트는 과거 메모리에 얽매이지 않고 현재 사용자의 새 요구사항으로 `spec.md`를 신규 작성해야 한다.

### FR-04: 거버넌스 감사(`forgeflow check`) 및 진단(`doctor`) 검증 규칙 강화
- `forgeflow check` 및 `forgeflow doctor`는 하이브리드 환경 감지 시:
  - `.specify/scripts/bash/check-prerequisites.sh` 및 `setup-plan.sh`의 존재 및 실행 권한 여부를 검증해야 한다.
  - 누락 시 명확한 에러 메시지와 함께 해결 가이드를 출력해야 한다.

### FR-05: 배포 인스톨러(`install.sh`) 및 스킬 동기화
- `install.sh` 및 `scripts/install-skills.sh`가 설치하는 `setup-forgeflow` 스킬 명세에 본 번들링 및 Date-Based Amnesia 지침을 영구 반영해야 한다.

---

## 4. 비기능 품질 속성 (Non-Functional Requirements)

1. **Zero-Dependency 원칙 유지**: 모든 번들링, 템플릿 추출, 파일 권한 부여 로직은 Python 3.10+ 표준 라이브러리(`importlib.resources`, `pathlib`, `os`, `stat`, `shutil`)만으로 100% 동작해야 한다.
2. **Fail-Closed 실행 무결성**: 스크립트 누락이나 실행 권한 누락 시 조용히 넘기지 않고 명확히 실패(`exit 1`)를 반환하여 사전에 결함을 방어해야 한다.
3. **크로스 플랫폼 호환성**: macOS 및 Linux 환경에서 셸 스크립트 라인 엔딩(`\n`)과 실행 권한이 완벽하게 보존되어야 한다.

---

## 5. 범위 외 사항 (Out of Scope)

- 2026-10-20 이전 비공개 프로토타입 버전(v0.1.0 ~ v0.22.1)의 복잡한 스키마 변환 및 데이터 마이그레이션 (사용자 지침에 따라 전면 폐기 대상)
- PowerShell(`.ps1`) 및 Python 전용 Spec Kit 스크립트 지원 (현재 macOS/Linux bash 타깃에 집중)

---

## 6. 인수 조건 (Acceptance Criteria)

- [ ] **AC-1**: `forgeflow init --speckit` 실행 시 `.specify/scripts/bash/`에 6개 스크립트가 생성되고 모두 실행 권한(`-rwxr-xr-x`)을 갖는다.
- [ ] **AC-2**: `forgeflow init --speckit` 실행 시 `.specify/templates/`에 `spec-template.md`, `plan-template.md`, `tasks-template.md`, `checklist-template.md`가 생성된다.
- [ ] **AC-3**: 프로젝트 루트에서 `.specify/scripts/bash/check-prerequisites.sh --json --paths-only` 실행 시 `exit 0` 및 올바른 JSON 페이로드가 반환된다.
- [ ] **AC-4**: 2026-10-20 이전의 레거시 설정이 존재하는 프로젝트에서 `setup-forgeflow` 실행 시 v0.1.0 표준으로 안전하게 대체된다.
- [ ] **AC-5**: 기존 단위 테스트 264개 전원 통과 및 신규 하이브리드 번들링 검증 테스트가 100% Pass한다.
- [ ] **AC-6**: `forgeflow check --all --strict` 감사에서 결함 0건(🟢 ALL PASSED)을 유지한다.
