# Specification: ForgeFlow CLI Upgrade & Smart Facade Skill

- **Release ID**: `v0.1.3-forgeflow-upgrade-and-smart-facade`
- **Created**: 2026-10-21
- **Risk Tier**: **Tier 3 (Critical / Core CLI Interface / Public Interface)**
- **Status**: DRAFT (Stage 1 Specification)

---

## 1. 배경 및 문제 정의 (Background & Problem)

1. **전역 런타임 업데이트와 로컬 작업 repo 갱신의 관심사 분리 필요**:
   - `forgeflow`는 OS 사용자 계정 수준에 전역 배포되는 런타임/CLI/에이전트 스킬(`~/.local/forgeflow`, `~/.agents/skills`)과, 개별 Git 프로젝트 레벨의 거버넌스 설정(`.forgeflow.json`, `.specify/`)이라는 두 가지 계층을 가집니다.
   - 기존에는 CLI 자체에 최신 릴리즈를 감지하고 전역 패키지를 업데이트하는 내장 명령어(`forgeflow upgrade`)가 부재하여, 사용자가 수동으로 `curl ... | bash`를 직접 재실행해야 했습니다.

2. **`update-forgeflow` 스킬의 스마트 파사드(Smart Facade) 진화**:
   - 다중 작업 공간(Repo A, Repo B, Repo C) 환경에서 사용자가 어느 프로젝트에서든 `/update-forgeflow`를 지시했을 때:
     - 1단계: 원격 최신 버전과 로컬 전역 CLI 버전을 비교하여, 구버전인 경우 `forgeflow upgrade`를 호출해 전역 환경을 먼저 최신화합니다. (이미 최신이면 건너뜁니다)
     - 2단계: 최신화된 전역 템플릿과 자산을 바탕으로 현재 작업 디렉토리의 거버넌스 사양을 동기화합니다.
   - 이를 통해 전역 버전 불일치(Skew) 오류를 방지하고 "Just Works" 사용자 경험을 제공합니다.

---

## 2. 요구사항 (Requirements)

- **REQ-1 (`forgeflow upgrade` CLI 서브커맨드 구현)**:
  - `src/forgeflow/cli.py`에 `upgrade` 서브커맨드를 추가한다.
  - 서브커맨드 인자:
    - `--check`: 실제 설치를 수행하지 않고 원격 최신 버전과 현재 버전을 비교하여 업데이트 가능 여부만 확인.
    - `--force`: 현재 버전과 원격 버전이 동일하더라도 강제로 재설치/동기화 실행.
    - `--json`: 기계 판독 가능한 JSON 형식으로 결과 출력.
    - `--repo-url`: 원격 배포 리포지토리 URL 지정 (기본값: `https://raw.githubusercontent.com/deepblue-kblee/forgeflow/main`).
  - 외부 의존성 없이 Python 표준 라이브러리(`urllib.request`, `subprocess`, `json`)만 사용한다 (Zero-Dependency 원칙).
  - 업그레이드 시 원격 `install.sh`를 안전하게 fetch하여 실행하고, 완료 후 변경된 버전을 안내한다.

- **REQ-2 (`update-forgeflow` 스킬 지침 개편)**:
  - `scripts/install-skills.sh` 및 `~/.agents/skills/update-forgeflow/SKILL.md`를 2단계 하이브리드 파사드 모델로 갱신한다:
    - **Step 1 (전역 런타임 최신화)**: `forgeflow upgrade --check`로 원격 새 버전을 감지하고, 필요시 `forgeflow upgrade`를 자동 실행하여 전역 CLI 및 스킬을 먼저 승격.
    - **Step 2 (현재 작업 repo 사양 동기화)**: 현재 프로젝트의 `.forgeflow.json`, `.specify/scripts/bash/`, `.specify/templates/`를 최신 전역 패키지로부터 동기화하고 `forgeflow check --quiet`로 검증.

- **REQ-3 (단위 및 통합 테스트)**:
  - `tests/test_upgrade_cli.py`를 신규 작성하여 `upgrade --check`, `upgrade --json`, 버전 비교 로직, 네트워크 예외 처리, 이미 최신 버전일 때의 조기 종료 등을 100% 검증한다.

- **REQ-4 (문서화 및 버전 갱신)**:
  - `README.md` 및 `docs/spec/FLOW_SPEC.md`에 `forgeflow upgrade` CLI 사용법과 `/update-forgeflow` 스마트 파사드 동작 원리를 명시한다.
  - 자체 버전을 `v0.1.3`으로 판올림한다.

---

## 3. 인수 조건 (Acceptance Criteria)

- **AC-1**: `forgeflow upgrade --check` 실행 시 현재 버전과 원격 최신 버전을 비교하여 업데이트 필요 여부와 상태 코드를 올바르게 반환한다.
- **AC-2**: `forgeflow upgrade` 실행 시 이미 최신 버전이면 `Already up to date` 메시지와 함께 불필요한 재설치를 생략하고 `exit 0`으로 종료한다 (`--force` 지정 시에는 강제 재설치 수행).
- **AC-3**: `update-forgeflow` 스킬 문서에 1단계 전역 최신화(`forgeflow upgrade`) ➔ 2단계 로컬 repo 동기화 절차가 명문화된다.
- **AC-4**: 신규 단위 테스트 `test_upgrade_cli.py`를 포함한 전체 테스트 스위트 100% Pass를 달성한다.
- **AC-5**: `forgeflow check --all --strict` 하네스 거버넌스 감사를 🟢 통과한다.
- **AC-6**: `src/forgeflow/_version.py`가 `0.1.3`으로 갱신된다.

---

## 4. 계획된 변경 범위 (Planned Scope)

- `src/forgeflow/cli.py` (`upgrade` 서브커맨드 및 핸들러 구현)
- `src/forgeflow/_version.py` (`0.1.3` 판올림)
- `scripts/install-skills.sh` (`update-forgeflow` 스킬 템플릿 개정)
- `~/.agents/skills/update-forgeflow/SKILL.md` (로컬 전역 스킬 동기화)
- `tests/test_upgrade_cli.py` (신규 테스트 작성)
- `README.md` & `docs/spec/FLOW_SPEC.md` (문서 최신화)
