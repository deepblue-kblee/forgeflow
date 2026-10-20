# Specification: Redefining ForgeFlow Update Command & Facade Integration

- **Release ID**: `v0.1.5-redefine-update-command-and-facade`
- **Created**: 2026-10-21
- **Risk Tier**: **Tier 3 (Critical / Core CLI Interface / Public Interface)**
- **Status**: DRAFT (Stage 1 Specification)

---

## 1. 배경 및 문제 정의 (Background & Problem)

1. **전역과 로컬의 기능 대칭성 완성 필요**:
   - `forgeflow upgrade`는 OS 사용자 계정 전역(Global)의 CLI 바이너리 및 에이전트 스킬을 판올림합니다.
   - 반면 개별 작업 리포지토리(Local Repo)의 거버넌스 사양(`.forgeflow.json`, `.specify/scripts/bash/`, 템플릿)을 최신 버전으로 갱신하는 독립 CLI 명령어가 부재했습니다.
   - 과거 구버전 번들 카탈로그를 참조하던 레거시 `update`를 폐기한 자리에, **현대 Spec Kit 하이브리드 규격에 맞는 로컬 리포지토리 거버넌스 사양 갱신 전용 `forgeflow update` 명령어를 새롭게 정의**해야 합니다.

2. **스마트 파사드(`/update-forgeflow`)의 캡슐화**:
   - 에이전트 스킬인 `/update-forgeflow`는 내부에서 파일 복사 경로를 장황하게 처리할 필요 없이, `forgeflow upgrade`(전역 갱신) ➔ `forgeflow update`(로컬 갱신)를 순차 호출하도록 간결하게 단일화합니다.
   - 사용자는 터미널에서 `forgeflow update`로 현재 repo만 가볍게 갱신하거나, AI에게 `/update-forgeflow`를 지시하여 전역+로컬 올인원 갱신을 선택할 수 있습니다.

---

## 2. 요구사항 (Requirements)

- **REQ-1 (`forgeflow update` CLI 서브커맨드 구현)**:
  - `src/forgeflow/cli.py`에 `update` 서브커맨드를 추가한다:
    ```bash
    forgeflow update [--path PATH] [--quiet] [--json]
    ```
  - 동작 로직:
    1. 대상 리포지토리의 `.forgeflow.json` 존재 여부 확인 (미존재 시 `exit 1`).
    2. 기존 `tasks/in-progress/` 및 `tasks/completed/` 내의 릴리즈 아티팩트는 100% 안전하게 보존.
    3. `.forgeflow.json`의 `forgeflow_version`을 현재 프레임워크 버전(`__version__`)으로 갱신.
    4. `.specify/scripts/bash/` 스크립트 6종(`check-prerequisites.sh`, `common.sh`, `create-new-feature.sh`, `resolve-template.sh`, `setup-plan.sh`, `setup-tasks.sh`)을 프레임워크 템플릿으로부터 덮어쓰고 실행 권한(`chmod 755`) 부여.
    5. `.specify/templates/` 템플릿 4종 및 `.specify/templates/commands/implement.md` 최신화.
    6. `.specify/extensions.yml` 및 `.specify/memory/constitution.md` 최신화 (사용자 커스텀 규칙 보존).
    7. `forgeflow check --stage 2 --quiet` 및 기본 정합성 검증 수행.
    8. 갱신된 파일 목록과 버전 변경 내역을 텍스트 또는 JSON으로 출력.

- **REQ-2 (`update-forgeflow` 스킬 지침 캡슐화 및 단일화)**:
  - `scripts/install-skills.sh` 및 `~/.agents/skills/update-forgeflow/SKILL.md` 지침을 개정한다:
    - Step 1: `forgeflow upgrade --check` 확인 후 필요 시 `forgeflow upgrade` 실행 (전역 런타임 최신화).
    - Step 2: `forgeflow update` 실행 (현재 repo 사양 갱신).

- **REQ-3 (단위 및 통합 테스트)**:
  - `tests/test_update_cli.py`를 신규 작성하여 `update` 커맨드의 버전 갱신, 스크립트 0o755 권한 부여, 템플릿 복사, `tasks/` 보존, 비-ForgeFlow 프로젝트에서의 거부 동작 등을 100% 검증한다.

- **REQ-4 (문서화 및 버전 갱신)**:
  - `README.md` 및 `docs/spec/FLOW_SPEC.md`에 `forgeflow update`와 `forgeflow upgrade`의 역할 분담 및 `/update-forgeflow` 파사드 안내를 명문화한다.
  - 자체 버전을 `v0.1.5`로 판올림한다.

---

## 3. 인수 조건 (Acceptance Criteria)

- **AC-1**: ForgeFlow 프로젝트 루트에서 `forgeflow update` 실행 시 `.forgeflow.json` 버전이 갱신되고 `.specify/scripts/bash/*` 스크립트에 `0o755` 실행 권한이 부여되며 성공 코드 `0`을 반환한다.
- **AC-2**: `tasks/in-progress/` 및 `tasks/completed/`의 기존 작업 파일들이 `forgeflow update` 실행 후에도 전혀 손상되거나 삭제되지 않는다.
- **AC-3**: `.forgeflow.json`이 없는 디렉토리에서 `forgeflow update` 실행 시 적절한 에러 메시지와 함께 `exit 1`로 거부된다.
- **AC-4**: `update-forgeflow` 스킬 지침이 `forgeflow upgrade` ➔ `forgeflow update` 체인으로 캡슐화된다.
- **AC-5**: 신규 테스트 `test_update_cli.py`를 포함한 전체 테스트 스위트 100% Pass 및 `forgeflow check --all --strict` 🟢 ALL PASSED를 달성한다.
- **AC-6**: `src/forgeflow/_version.py`가 `0.1.5`로 갱신된다.

---

## 4. 계획된 변경 범위 (Planned Scope)

- `src/forgeflow/scaffold.py` (`update_repo_governance` 메서드 추가)
- `src/forgeflow/cli.py` (`update` 서브커맨드 및 핸들러 구현)
- `scripts/install-skills.sh` (`update-forgeflow` 스킬 지침 개정)
- `~/.agents/skills/update-forgeflow/SKILL.md` (스킬 동기화)
- `tests/test_update_cli.py` (신규 테스트)
- `README.md` & `docs/spec/FLOW_SPEC.md` (문서 최신화)
- `src/forgeflow/_version.py` (0.1.5 판올림)
