# Architecture Plan: Redefining ForgeFlow Update Command & Facade Integration

- **Release ID**: `v0.1.5-redefine-update-command-and-facade`
- **Status**: APPROVED ARCHITECTURE
- **Risk Tier**: Tier 3 (Critical)

---

## 1. 아키텍처 및 상세 설계 (Architecture Overview)

### 1.1 `TemplateScaffolder.update_repo_governance` (`scaffold.py`)
- **입력**: `root_dir: Path`
- **검증**:
  - `config_path = root_dir / ".forgeflow.json"`
  - 존재하지 않거나 유효한 JSON이 아니면 `raise ValueError("Not a valid ForgeFlow repository (.forgeflow.json missing).")`
- **실행**:
  1. `config_path` 파싱:
     - 기존 `governance`, `paths` 설정 유지.
     - `previous_version = data.get("forgeflow_version", "unknown")`
     - `data["forgeflow_version"] = __version__`
     - `config_path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")`
  2. `TemplateScaffolder.scaffold_speckit_hybrid(root_dir, force=True)` 재실행:
     - `.specify/scripts/bash/*` 6종 복사 및 `chmod 755` 권한 부여.
     - `.specify/templates/*` 4종 템플릿 복사.
     - `.specify/templates/commands/implement.md` 복사.
     - `.specify/extensions.yml` 및 `constitution.md` 최신화 (사용자 규칙 보존).
     - 주의: `tasks/` 내의 파일들은 건드리지 않고 디렉토리 존재만 확인.
  3. 결과 반환:
     ```python
     {
         "status": "success",
         "previous_version": previous_version,
         "current_version": __version__,
         "updated_files": [...],
     }
     ```

### 1.2 `cli.py` 내 `forgeflow update` 서브커맨드 및 핸들러
- **파서 등록**:
  ```python
  update_parser = subparsers.add_parser("update", help="Update local repository governance specifications and Spec Kit assets")
  update_parser.add_argument("--path", default=None, help="Target project repository root (default: current directory)")
  update_parser.add_argument("--json", action="store_true", help="Output machine-readable JSON")
  update_parser.add_argument("--quiet", action="store_true", help="Suppress non-error output")
  ```
- **핸들러 함수 (`handle_update`)**:
  - 타깃 디렉터리 resolve.
  - `TemplateScaffolder.update_repo_governance(target_dir)` 호출.
  - 성공 메시지 및 갱신 파일 요약 출력 (또는 JSON).

### 1.3 `update-forgeflow` 스킬 지침 개편
- 에이전트는 두 단계를 순차 호출:
  ```bash
  # Step 1: 전역 환경 최신화 (원격과 비교하여 필요시 자동 업그레이드)
  forgeflow upgrade --check --json
  # upgrade_available=true 시 forgeflow upgrade 실행

  # Step 2: 현재 작업 repo 사양 갱신
  forgeflow update
  ```

---

## 2. 테스트 설계 (`tests/test_update_cli.py`)
- 시나리오 1: 정상 ForgeFlow 프로젝트에서 `forgeflow update` 실행 ➔ 버전 갱신, 스크립트 복사 및 0o755 권한, tasks 디렉터리 파일 보존 확인.
- 시나리오 2: `.forgeflow.json`이 없는 빈 디렉터리에서 `forgeflow update` 실행 ➔ 에러 메시지와 함께 `exit 1`.
- 시나리오 3: `--json` 옵션 테스트 ➔ 구조화된 JSON 응답 및 `previous_version`, `current_version` 검증.
