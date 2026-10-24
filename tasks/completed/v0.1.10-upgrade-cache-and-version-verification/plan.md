# Implementation Plan: Upgrade Cache Busting, Version Inversion Guard, and Verification

- **Release ID**: `v0.1.10-upgrade-cache-and-version-verification`
- **Created Date**: 2026-10-22
- **Risk Tier**: **Tier 1 (Minor / Fast-track - CLI Reliability & UX Improvement)**

---

## 1. 아키텍처 및 세부 설계 (Architecture & Design)

### 1.1 Cache-Busting 메커니즘
- `time.time()`을 활용하여 요청 URL에 고유 쿼리 파라미터 `?t={int(time.time())}` 부착:
  - `version_url = f"{repo_url}/src/forgeflow/_version.py?t={int(time.time())}"`
  - `install_url = f"{repo_url}/install.sh?t={int(time.time())}"`
- HTTP 헤더 주입:
  ```python
  headers = {
      "User-Agent": "ForgeFlow-CLI",
      "Cache-Control": "no-cache, no-store, must-revalidate",
      "Pragma": "no-cache",
  }
  ```
  Fastly / Varnish 엣지 노드가 요청을 캐시하지 않고 원본 GitHub 저장소로 포워딩하도록 강제.

### 1.2 원격 버전 역전 감지 (Inverted Version Guard)
- `current_tuple = parse_version_tuple(__version__)`
- `remote_tuple = parse_version_tuple(remote_version)`
- 조건: `remote_tuple < current_tuple`
  - 이 경우 로컬이 원격보다 앞서 있거나 CDN 캐시 전파 지연 상태임.
  - 경고 메시지 출력:
    - 터미널: `⚠️  Warning: Remote version (v{remote_version}) is older than local version (v{__version__}). GitHub CDN cache may still be updating.`
    - JSON: `"warning": f"Remote version (v{remote_version}) is older than current version (v{__version__}). Possible CDN cache delay."`

### 1.3 설치 완료 후 실설치 버전 재검증
- `install.sh` 실행 성공 후, `~/.local/forgeflow/current/lib/forgeflow/_version.py` 파일이 존재하는지 검사:
  - 파일이 존재하면 정규식으로 `__version__`을 파싱하여 `installed_version` 결정.
  - 파일이 없으면 `remote_version` 또는 `__version__`을 fallback으로 사용.
- 성공 메시지: `print(f"🎉 Successfully upgraded ForgeFlow to v{installed_version}!")`

### 1.4 버전 승격
- `src/forgeflow/_version.py`의 `__version__`을 `"0.1.10"`으로 변경.

---

## 2. 변경 파일 목록 (Target Files)
1. `src/forgeflow/cli.py`: `handle_upgrade` 로직 보강
2. `src/forgeflow/_version.py`: 버전 `0.1.10`으로 승격
3. `tests/test_upgrade_cli.py`: 신규 테스트 케이스 추가 (Cache-busting, Inversion warning, 실설치 버전 검증)

---

## 3. 검증 전략 (Verification Strategy)
- 단위 테스트 실행: `PYTHONPATH=src python3 -m unittest discover -s tests -p "test_*.py"`
- 하네스 거버넌스 감사: `forgeflow check --all --strict`
- 모든 테스트 100% Pass 확인 후 QA Sign-off 및 릴리즈 승격.
