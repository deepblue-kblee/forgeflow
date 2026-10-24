# Tasks: Upgrade Cache Busting, Version Inversion Guard, and Verification

- **Release ID**: `v0.1.10-upgrade-cache-and-version-verification`
- **Created Date**: 2026-10-22
- **Risk Tier**: **Tier 1 (Minor / Fast-track - CLI Reliability & UX Improvement)**

---

## 작업 체크리스트 (Atomic Task List)

- [x] **Task 1: Pre-Implementation Gatekeeper Check**
  - `forgeflow check --stage 2` 실행 및 Gate 1 승인 통과 확인

- [x] **Task 2: CLI Upgrade Logic Enhancement (`src/forgeflow/cli.py`)**
  - Cache-busting: `Cache-Control`, `Pragma` 헤더 추가 및 URL에 `?t={int(time.time())}` 적용
  - Inverted Version Guard: `remote_tuple < current_tuple`일 때 CDN 지연 경고 문구 출력 및 JSON payload warning 추가
  - Verified Installed Version: `install.sh` 실행 완료 후 `~/.local/forgeflow/current/lib/forgeflow/_version.py` 파싱하여 실제 버전 메시지 출력

- [x] **Task 3: Version Bump (`src/forgeflow/_version.py`)**
  - `__version__ = "0.1.10"`으로 승격

- [x] **Task 4: Unit Tests Synchronization (`tests/test_upgrade_cli.py`)**
  - Cache-busting 헤더 및 쿼리 요청 단위 테스트 작성
  - Remote version 역전(Inversion) 경고 출력 단위 테스트 작성
  - 실설치 버전 반영 출력 단위 테스트 작성

- [x] **Task 5: Full Test Suite & Governance Verification**
  - 전체 단위 테스트 100% Pass 확인 (`python3 -m unittest`)
  - 전체 릴리즈 거버넌스 감사 통과 (`forgeflow check --all --strict`)

- [x] **Task 6: QA Sign-Off & Release Seal (Gate 2 & 3)**
  - `QA_SIGNOFF.md` 작성 및 Gate 2 승인
  - `RELEASE_SIGNOFF.md` 작성 및 Gate 3 승인
  - `tasks/in-progress/`에서 `tasks/completed/`로 패키지 밀봉/이동
