# Technical Plan: Support auto_create_branch Governance Configuration

- **Release ID**: `v0.1.19-auto-create-branch-option`
- **Tier**: `Tier 3 (Core / Governance Configuration & Implementation Control)`

## 1. 아키텍처 및 설계 원칙

### 1.1 브랜치 자동 분기 설정 해석 및 검증 로직 (`resolve_auto_create_branch`)
`src/forgeflow/scaffold.py`에 프로젝트 거버넌스 설정으로부터 `auto_create_branch`를 해석하고 엄격하게 검증하는 함수 `resolve_auto_create_branch(repo_root: Path) -> bool`을 구현한다.
- 기본값: `False` (옵션이 없거나 `.forgeflow.json`이 존재하지 않는 경우 기본적으로 격리 브랜치 자동 생성을 생략)
- `.forgeflow.json` 파일 존재 시:
  - 파싱 오류 시 `ValueError` 발생.
  - 최상위 객체가 딕셔너리가 아니거나 `governance.auto_create_branch` 키가 누락된 경우 기본값 `False` 반환.
  - 키가 존재할 경우 엄격한 타입 검증:
    - `not isinstance(val, bool)`인 경우 `ValueError(f"Invalid auto_create_branch in .forgeflow.json: expected boolean, got {type(val).__name__} ({val!r})")` 발생 (Fail-Closed).
    - `True` 또는 `False` 불리언 값 그대로 반환.

### 1.2 CLI 및 라이프사이클 분기 제어
- `src/forgeflow/cli.py`:
  - `release create` 및 `task create` 서브커맨드에 `--create-branch` (호환 별칭 `--branch`) 플래그 추가 (기본값 `False`).
  - 브랜치 생성 여부 판단: `effective_create_branch = explicit_create_branch or resolve_auto_create_branch(repo_root)`
  - `effective_create_branch`가 `True`인 경우:
    - 기존과 같이 `feat/<release-id>` 브랜치 분기(`git checkout -b feat/<release-id>`) 실행 및 `lifecycle.create(..., branch=f"feat/{release_id}")` 바인딩.
  - `effective_create_branch`가 `False`인 경우:
    - `git checkout -b` 단계를 생략(skip)하고, 현재 체크아웃된 Git 브랜치 이름을 조회하여 `lifecycle.create(..., branch=current_branch)`에 안전하게 결속.

### 1.3 릴리즈 종료 시 안전 가드 (`harness.py: close_release`)
- `harness.py`의 `close_release()`:
  - `task_branch = state.get("identity", {}).get("branch")`
  - 현재 브랜치와 `task_branch`가 동일하거나, `task_branch`가 `main`/`master`이거나, 로컬 Git refs에 해당 브랜치가 존재하지 않는 경우 브랜치 삭제 명령을 안전하게 건너뜀(skip).
  - worktree 충돌 방지: 현재 체크아웃된 브랜치와 task_branch가 일치하더라도 `auto_create_branch: false` 모드에서는 정상 완료 처리.

### 1.4 진단 엔진 연동 (`SystemDiagnostics`)
- `src/forgeflow/diagnostics.py`:
  - `.forgeflow.json`의 `governance.auto_create_branch`가 존재할 때 `bool` 타입이 아니면 `INVALID_AUTO_CREATE_BRANCH` 경고(WARNING) 이상 징후 등록.
  - 문제 원인 및 `.forgeflow.json` 교정 안내 메시지 제공.

### 1.5 규격, 템플릿 및 스킬 지침 일원화
- `FLOW_SPEC.md` 및 `SPECKIT_HOOKS_AND_NORMS.md`:
  - Stage 3 브랜치 분기 단계에 `auto_create_branch: false`(기본값)일 때 브랜치 생성 스킵 및 현재 브랜치 유지 규범 명시.
  - 향후 브랜치 자동 생성을 기본화하려면 `AGENTS.md`가 아닌 `.forgeflow.json`의 `"auto_create_branch": true` 옵션으로 제어한다는 원칙 명시.
- `~/.agents/skills/forgeflow/SKILL.md` 동기화.

### 1.6 하위 호환성 및 Zero-Dependency
- Python 3.10+ 표준 라이브러리(`json`, `pathlib`, `subprocess`)만 사용.
- 기존 프로젝트 및 318개 전체 단위 테스트 100% 호환.
