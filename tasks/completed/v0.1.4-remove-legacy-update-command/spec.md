# Specification: Removal of Legacy Update Command & Obsolete Catalogs

- **Release ID**: `v0.1.4-remove-legacy-update-command`
- **Created**: 2026-10-21
- **Risk Tier**: **Tier 3 (Critical / Core CLI Cleanup / Amnesia Policy Enforcement)**
- **Status**: DRAFT (Stage 1 Specification)

---

## 1. 배경 및 문제 정의 (Background & Problem)

1. **`update`와 `upgrade`의 혼선 및 과거 레거시 잔재**:
   - `forgeflow upgrade`는 원격 공식 릴리즈를 감지하여 OS 전역의 CLI 및 스킬을 판올림하는 최신 공식 명령어입니다.
   - 반면 `forgeflow update`는 2026-10-20 이전 v0.4.4~v0.22.0 시절의 구버전 잔재로서, 당시 `docs/forgeflow/` 하위 파일들의 불변 바이트 해시 카탈로그(`bundle_catalog.py`, `catalog_oracles/`)를 비교하던 구시대의 유산입니다.
   - 이는 현재의 Spec Kit 하이브리드 아키텍처(`.specify/`, `tasks/`)와 전혀 호환되지 않으며, 사용자와 에이전트에게 불필요한 혼선을 유발합니다.

2. **과거 버전 및 흔적 강제 폐기 규범 (Date-Based Amnesia Policy) 준수**:
   - [AGENTS.md](../../AGENTS.md) 4조에 따라 2026-10-20 이전 생성된 모든 레거시 구조와 코드는 하위 호환을 배제하고 일체 영구 폐기해야 합니다.

---

## 2. 요구사항 (Requirements)

- **REQ-1 (`forgeflow update` 서브커맨드 제거)**:
  - `src/forgeflow/cli.py`에서 `update` 서브커맨드 정의, 파서 및 실행 디스패치 로직을 완전히 삭제한다.
  - `src/forgeflow/cli.py` 상단의 `from .update import apply as apply_update, inspect as inspect_update` 임포트를 제거한다.

- **REQ-2 (레거시 번들 카탈로그 및 업데이트 모듈 영구 삭제)**:
  - `src/forgeflow/update.py` 삭제.
  - `src/forgeflow/bundle_catalog.py` 삭제.
  - `src/forgeflow/catalog_oracles/` 디렉터리 및 하위 파일 삭제.
  - `tests/test_update.py` 삭제.
  - `tests/test_cli.py` 내의 레거시 `update` CLI 테스트 메서드 삭제.

- **REQ-3 (CLI 표준 정립)**:
  - 이제 CLI는 전역 업그레이드를 위한 `forgeflow upgrade`만을 단일 표준으로 제공한다.
  - 로컬 작업 repo의 거버넌스 사양 갱신은 스마트 파사드 스킬인 `/update-forgeflow`로 일원화한다.

- **REQ-4 (테스트 무결성 및 버전 갱신)**:
  - 남아있는 모든 단위 및 통합 테스트가 100% 통과함을 보장한다.
  - `src/forgeflow/_version.py`를 `0.1.4`로 판올림한다.

---

## 3. 인수 조건 (Acceptance Criteria)

- **AC-1**: `forgeflow --help` 실행 시 서브커맨드 목록에서 `update`가 완전히 제거되고 `upgrade`만 정상 노출된다.
- **AC-2**: `forgeflow update` 실행 시 `invalid choice: 'update'`가 발생하며 구버전 명령어가 동작하지 않는다.
- **AC-3**: `src/forgeflow/update.py`, `bundle_catalog.py`, `catalog_oracles/`, `tests/test_update.py`가 코드베이스에서 영구 삭제된다.
- **AC-4**: 전체 테스트 스위트 100% Pass 및 `forgeflow check --all --strict` 🟢 ALL PASSED를 달성한다.
- **AC-5**: `_version.py`가 `0.1.4`로 갱신된다.

---

## 4. 계획된 변경 범위 (Planned Scope)

- `src/forgeflow/cli.py`
- `src/forgeflow/update.py` (삭제)
- `src/forgeflow/bundle_catalog.py` (삭제)
- `src/forgeflow/catalog_oracles/*` (삭제)
- `tests/test_update.py` (삭제)
- `tests/test_cli.py`
- `src/forgeflow/_version.py`
