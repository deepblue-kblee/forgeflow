# Architecture Plan: ForgeFlow CLI Upgrade & Smart Facade Skill

- **Release ID**: `v0.1.3-forgeflow-upgrade-and-smart-facade`
- **Status**: APPROVED ARCHITECTURE
- **Risk Tier**: Tier 3 (Critical)

---

## 1. 아키텍처 및 상세 설계 (Architecture Overview)

### 1.1 `forgeflow upgrade` CLI 구조
- **파서 등록 (`cli.py`)**:
  ```python
  upgrade_parser = subparsers.add_parser("upgrade", help="Upgrade global ForgeFlow installation to the latest version")
  upgrade_parser.add_argument("--check", action="store_true", help="Check for available updates without installing")
  upgrade_parser.add_argument("--force", action="store_true", help="Force re-install even if version is current")
  upgrade_parser.add_argument("--json", action="store_true", help="Output machine-readable JSON")
  upgrade_parser.add_argument("--repo-url", default="https://raw.githubusercontent.com/deepblue-kblee/forgeflow/main", help="Remote raw repository base URL")
  ```
- **핸들러 함수 (`handle_upgrade`)**:
  1. `repo_url/src/forgeflow/_version.py`를 `urllib.request.urlopen(..., timeout=5)`로 페치.
  2. 정규식 `r'__version__\s*=\s*["\']([^"\']+)["\']'`로 원격 버전 파싱.
  3. 버전 비교: `current_version` vs `remote_version`.
  4. `--check` 옵션인 경우:
     - 업그레이드 가능 여부(`is_upgrade_available`)를 JSON 또는 텍스트로 출력 후 `exit 0` (업그레이드 가능 시 0, 최신 시 0).
  5. 최신 버전이고 `--force`가 아니면:
     - `ForgeFlow is already up to date (v{current_version}).` 출력 후 `exit 0`.
  6. 업그레이드 실행:
     - `repo_url/install.sh`를 다운로드하여 임시 셸 파일 생성.
     - `subprocess.run(["bash", temp_script, "--force"], check=True)` 실행.
     - 완료 후 성공 메시지 출력.

### 1.2 `update-forgeflow` 스킬 지침 (스마트 파사드)
- **Step 1 (전역 검사 및 자동 승격)**:
  - `forgeflow upgrade --check --json` 실행.
  - 최신 버전이 존재하면 `forgeflow upgrade` 자동 실행하여 전역 런타임 및 `~/.agents/skills/`를 최신화.
  - 이미 최신이면 즉시 Step 2로 진행.
- **Step 2 (현재 repo 거버넌스 사양 갱신)**:
  - 현재 프로젝트 루트의 `.forgeflow.json` 버전 갱신.
  - `~/.local/forgeflow/current/lib/forgeflow/templates/speckit/scripts/bash/` 스크립트 6종 동기화 (`chmod 755`).
  - `.specify/templates/` 템플릿 4종 동기화.
  - `forgeflow check --quiet`로 검증 후 완료 보고.

---

## 2. 테스트 설계 (`tests/test_upgrade_cli.py`)
- `unittest.mock`을 사용하여 `urllib.request.urlopen` 및 `subprocess.run` 모킹.
- 시나리오 1: 이미 최신 버전인 경우 (`--check` 및 기본 실행) ➔ 설치 건너뜀.
- 시나리오 2: 원격 버전이 더 높은 경우 ➔ `--check` 시 업그레이드 가능 보고, 기본 실행 시 `install.sh` 트리거.
- 시나리오 3: `--force` 플래그 동작 ➔ 버전 같아도 실행.
- 시나리오 4: 네트워크 타임아웃/에러 시 graceful failure (에러 메시지 출력 및 `exit 1`).
