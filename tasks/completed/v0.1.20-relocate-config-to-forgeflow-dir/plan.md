# Architecture & Technical Plan: Relocate Configuration to .forgeflow/config.json with Update Migration

- **Release ID**: `v0.1.20-relocate-config-to-forgeflow-dir`
- **Tier**: `Tier 3 (Core / Governance Configuration & Implementation Control)`
- **Target Specification**: [spec.md](spec.md)

## 1. 아키텍처 개요 (Architecture Overview)

```text
[Legacy Layout (Pre-v0.1.20)]
repo_root/
  ├── .forgeflow.json           <-- 기존 설정 파일
  ├── .forgeflow/
  │     └── diagnostics/
  └── tasks/

[Modern Layout (v0.1.20+)]
repo_root/
  ├── .forgeflow/
  │     ├── config.json         <-- 표준 canonical 설정 파일
  │     └── diagnostics/
  └── tasks/
```

## 2. 모듈별 기술 설계 (Component Technical Design)

### 2.1 `src/forgeflow/scaffold.py`
- 상수 및 경로 정의:
  - `CONFIG_REL_PATH = Path(".forgeflow") / "config.json"`
  - `LEGACY_CONFIG_REL_PATH = Path(".forgeflow.json")`
- 설정 파일 경로 해석 헬퍼 `get_config_path(root: Path, write_intent: bool = False) -> Path`:
  - `write_intent=False`인 경우: `.forgeflow/config.json`이 존재하면 우선 반환, 없고 `.forgeflow.json`이 존재하면 레거시 경로 반환, 둘 다 없으면 기본 `.forgeflow/config.json` 반환.
  - `write_intent=True`인 경우: 표준 `.forgeflow/config.json` 반환.
- `_journal_target` 화이트리스트에 `.forgeflow/config.json` 및 `.forgeflow.json` 등록.
- `scaffold_speckit_hybrid`:
  - `.forgeflow/` 디렉터리 생성(`mkdir(parents=True, exist_ok=True)`).
  - 새 설정 파일 `root / ".forgeflow" / "config.json"`에 쓰기.
  - 만약 루트에 기존 `.forgeflow.json`이 있고 새 설정 파일이 없으면 기존 데이터를 로드 및 딥 머지하여 `.forgeflow/config.json`으로 기록.
  - `created_files`/`updated_files`에 `".forgeflow/config.json"` 추가.
- `update_repo_governance`:
  - 새 설정 파일(`new_cfg = root / ".forgeflow" / "config.json"`)과 구버전 설정 파일(`old_cfg = root / ".forgeflow.json"`) 탐색.
  - 구버전만 존재하거나 마이그레이션이 필요한 경우:
    - `old_cfg` 내용을 로드하여 딥 머지 수행.
    - `new_cfg.parent.mkdir(parents=True, exist_ok=True)` 후 `new_cfg`에 저장.
    - `old_cfg.unlink(missing_ok=True)`로 구버전 파일 제거.
    - `updated_files`에 `".forgeflow/config.json"` 기록.
  - `new_cfg`가 이미 존재하는 경우: 기존 로직대로 딥 머지 및 버전 갱신.
- `update_tasks_dir_in_config`:
  - `get_config_path(repo_root)`를 조회하여 존재하는 파일에 `tasks_dir` 업데이트.

### 2.2 `src/forgeflow/runner.py`
- `_resolve_test_timeout(repo_root: Path) -> Optional[float]`:
  - `new_path = repo_root / ".forgeflow" / "config.json"`
  - `old_path = repo_root / ".forgeflow.json"`
  - `new_path`가 존재하면 우선 사용, 없으면 `old_path` 사용.

### 2.3 `src/forgeflow/scanner.py`
- `is_repo_root`:
  - `(probe / ".forgeflow" / "config.json").exists() or (probe / ".forgeflow.json").exists()` 포함.
- `_read_configured_tasks_dir(repo_root: Path) -> str`:
  - `new_path = repo_root / ".forgeflow" / "config.json"`
  - `old_path = repo_root / ".forgeflow.json"`
  - 우선순위에 따라 로드.

### 2.4 `src/forgeflow/diagnostics.py`
- config 검사:
  - `new_path` 우선, `old_path` 폴백.
  - 진단 리포트 안내 remedy 문구를 `.forgeflow/config.json`으로 업데이트.

### 2.5 `src/forgeflow/cli.py`
- `tasks-dir` 등 안내 메시지 문구를 `.forgeflow/config.json`으로 업데이트.

## 3. 테스트 및 검증 전략 (Testing Strategy)
- 단위 테스트:
  - `tests/test_scaffold.py`: 신규 스캐폴딩 시 `.forgeflow/config.json` 생성 검증.
  - `tests/test_update_cli.py`: 레거시 `.forgeflow.json` 보유 저장소에서 `forgeflow update` 시 `.forgeflow/config.json`으로 자동 마이그레이션 및 구버전 파일 삭제 검증.
  - `tests/test_runner.py`: 새 경로 및 구버전 경로 모두 타임아웃 파싱 검증.
  - `tests/test_tasks_architecture.py`: tasks_dir 설정이 `.forgeflow/config.json`에서 정상 작동 검증.
- 하네스 게이트 감사:
  - `forgeflow check --stage 2` 통과 확인.
  - 전체 단위 테스트(324+건) 100% 통과 확인.
  - `forgeflow check --all --strict` 🟢 ALL PASSED 확인.
