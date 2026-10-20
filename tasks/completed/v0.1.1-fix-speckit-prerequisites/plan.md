# Implementation Plan: Spec Kit Prerequisite Bundling & Date-Based Amnesia

**Feature Identifier**: `v0.1.1-fix-speckit-prerequisites`  
**Target Release**: `v0.1.1`  
**Created**: 2026-10-20  
**Phase**: Stage 3 (Plan & Task Breakdown)  
**Gate 1 Status**: APPROVED (SHA256 verified)

---

## 1. 아키텍처 개요 및 설계 원칙

### 1.1 설계 목표
`setup-forgeflow` 및 `forgeflow init --speckit` 실행 시 대상 프로젝트에 완전한 Spec Kit 로컬 실행 환경을 주입하여, 후속 Spec Kit 체인(`/speckit.specify` ➔ `/speckit.clarify` ➔ `/speckit.plan` ➔ `/speckit.tasks` ➔ `/speckit.implement`)이 어떤 사전 작업 없이도 100% 자급자족(Self-Contained)으로 완주되도록 만든다.

### 1.2 번들 디렉토리 레이아웃
ForgeFlow 패키지 내부에 Spec Kit 공식 런타임 자산을 구조화하여 번들링한다:

```text
src/forgeflow/templates/speckit/
├── scripts/
│   └── bash/
│       ├── check-prerequisites.sh      # feature.json 및 사전 문서 검증
│       ├── common.sh                   # bash 공통 유틸리티
│       ├── create-new-feature.sh       # 피쳐 브랜치 및 폴더 생성
│       ├── resolve-template.sh         # 템플릿 탐색/결합
│       ├── setup-plan.sh               # plan 셋업 및 경로 해석
│       └── setup-tasks.sh              # tasks 셋업 및 체크리스트 해석
└── templates/
    ├── spec-template.md                # 기능 명세서 템플릿
    ├── plan-template.md                # 기술 계획서 템플릿
    ├── tasks-template.md               # 태스크 체크리스트 템플릿
    └── checklist-template.md           # 품질 체크리스트 템플릿
```

---

## 2. 모듈별 기술 설계

### 2.1 스캐폴더 확장 (`src/forgeflow/scaffold.py`)
- `TemplateScaffolder.scaffold_speckit_hybrid(root: Path, force: bool = False)` 메서드 확장:
  1. 기존의 `tasks/`, `.forgeflow.json`, `constitution.md`, `extensions.yml`, `implement.md` 생성 로직 유지.
  2. `src/forgeflow/templates/speckit/scripts/bash/` 내의 모든 `.sh` 파일을 대상 프로젝트의 `.specify/scripts/bash/`로 복사.
  3. 모든 스크립트에 `0o755` (`rwxr-xr-x`) 실행 권한 부여.
  4. `src/forgeflow/templates/speckit/templates/` 내의 모든 템플릿을 대상 프로젝트의 `.specify/templates/`로 복사.
  5. 2026-10-20 이전 과거 설정 감지 시:
     - 기존 `.forgeflow.json`의 `forgeflow_version`이 2026-10-20 이전 프로토타입 버전이거나 형식이 다를 경우, 최신 v0.1.0 표준으로 덮어쓰고 경고 메시지 출력 (Date-Based Amnesia).

### 2.2 진단 및 헬스체크 확장 (`src/forgeflow/diagnostics.py`)
- `doctor` 명령어에 `check_speckit_prerequisites(root_path: Path)` 진단기 추가:
  - `.specify/scripts/bash/check-prerequisites.sh` 존재 및 실행 권한(`os.access(p, os.X_OK)`) 확인.
  - `.specify/scripts/bash/setup-plan.sh` 존재 및 실행 권한 확인.
  - `.specify/templates/spec-template.md` 존재 확인.
  - 결함 발견 시 `forgeflow init --speckit` 재실행을 유도하는 친절한 조치 가이드 제공.

### 2.3 패키징 및 배포 동기화 (`pyproject.toml`, `install.sh`)
- `pyproject.toml`의 `[tool.setuptools.package-data]`에 `"forgeflow.templates" = ["*.md", "spec/*.md", "speckit/**"]` 포함 보장.
- `install.sh`의 파일 복사 로직에 `templates/speckit/` 하위 스크립트 실행 권한 보존 확인.

---

## 3. 테스트 및 검증 계획 (TDD Strategy)

1. **`test_hybrid_scaffold.py` 신규/확장 테스트**:
   - `test_scaffold_speckit_hybrid_creates_scripts_with_executable_permissions`: 6개 bash 스크립트 생성 및 0o755 권한 검증.
   - `test_scaffold_speckit_hybrid_creates_all_templates`: 4개 템플릿 파일 생성 검증.
   - `test_scaffold_prunes_legacy_pre_release_configs`: 2026-10-20 이전 과거 설정 감지 및 v0.1.0 교체 검증.
2. **실행 적합성 테스트 (Incident-Fit Oracle)**:
   - 스캐폴딩 후 `.specify/scripts/bash/check-prerequisites.sh --json --paths-only` 실행하여 `exit 0` 및 JSON 응답 반환 검증.
3. **전체 스위트 회귀 검증**:
   - 기존 264개 단위 테스트 100% 통과 유지.
