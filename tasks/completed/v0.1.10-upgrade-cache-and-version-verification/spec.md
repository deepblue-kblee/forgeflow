# Specification: Upgrade Cache Busting, Version Inversion Guard, and Verification

- **Release ID**: `v0.1.10-upgrade-cache-and-version-verification`
- **Created Date**: 2026-10-22
- **Risk Tier**: **Tier 1 (Minor / Fast-track - CLI Reliability & UX Improvement)**

---

## 1. 개요 및 목적 (Overview & Purpose)

사용자가 `forgeflow upgrade`를 실행할 때, GitHub Raw CDN(`raw.githubusercontent.com`)의 기본 300초(5분) 캐시로 인해 GitHub 원본에 최신 버전이 푸시되었음에도 엣지 서버에서 과거 버전 응답이 반환되는 문제가 확인되었다.
이로 인해 `install.sh`(Git 실시간 클론)는 최신 버전을 설치하지만, CLI의 버전 확인 및 완료 메시지는 과거 버전을 표시하는 불일치 현상(`v0.1.7 ➔ v0.1.7...`, `Current: v0.1.9, Latest: v0.1.7`)이 발생했다.

이를 방지하기 위해 다음 3대 방어 및 검증 로직을 구현한다:
1. **Cache Busting**: `_version.py` 및 `install.sh` 다운로드 요청 시 `Cache-Control: no-cache`, `Pragma: no-cache` 헤더 부여 및 타임스탬프 쿼리(`?t=...`)를 적용하여 CDN 캐시 우회.
2. **원격 버전 역전 감지 (Inverted Version Guard)**: CDN 응답 버전(`remote_version`)이 로컬 버전(`current_version`)보다 낮은 경우 이상 징후를 감지하고 CDN 캐시 지연 안내 및 로컬 최신 상태 유지 처리.
3. **설치 완료 후 실설치 버전 재검증**: 사전 변수 문자열 포맷팅 대신, 설치 완료 후 실제 로컬 패키지/바이너리 버전을 확인하여 정확한 업그레이드 성공 메시지 출력.

---

## 2. 세부 요구사항 (Detailed Requirements)

1. **Cache Busting 헤더 및 쿼리 적용**:
   - `urllib.request.Request` 생성 시 `Cache-Control: no-cache`, `Pragma: no-cache` 헤더 추가.
   - `version_url` 및 `install_url`에 타임스탬프 쿼리 문자열(`?t={int(time.time())}`)을 추가하여 Fastly/Varnish CDN 캐시 우회.
2. **원격 버전 역전 감지 (Inverted Version Guard)**:
   - `remote_tuple < current_tuple`인 경우:
     - 비대화형/JSON 모드: payload에 `"warning": "Remote version appears older than current local version (possible CDN cache delay)."` 포함.
     - 터미널 모드: `⚠️ Warning: Remote version (v{remote_version}) is older than local version (v{__version__}). GitHub CDN cache may still be updating.` 경고 출력.
     - 이 경우 `is_upgrade_available`은 False로 유지되고 강제 재설치(`--force`)가 아니면 업그레이드를 권장하지 않음.
3. **설치 완료 후 실제 버전 확인 및 메시지 출력**:
   - `install.sh` 실행 성공 후, 기존의 사전 변수 `print(f"🎉 Successfully upgraded ForgeFlow to v{remote_version}!")` 대신, 실제 갱신된 활성 버전을 확인(`~/.local/forgeflow/current/lib/forgeflow/_version.py` 파싱 또는 `__version__` 재확인, 폴백으로 `remote_version`)하여 정확한 완료 메시지 출력.
4. **버전 승격**:
   - `src/forgeflow/_version.py`를 `0.1.10`으로 승격.
5. **단위 테스트 (`tests/test_upgrade_cli.py`) 동기화**:
   - Cache-busting 헤더 및 쿼리 요청 검증.
   - Remote version이 Local version보다 낮을 때의 역전 감지 경고 출력 검증.
   - 업그레이드 완료 후 실제 설치 버전 반영 출력 검증.

---

## 3. 인수 조건 (Acceptance Criteria)

- **AC-1**: `forgeflow upgrade` 실행 시 원격 버전 요청 URL에 타임스탬프 파라미터가 포함되고 `no-cache` 헤더가 전달된다.
- **AC-2**: 원격 버전이 로컬 버전보다 낮게 조회될 경우 CDN 캐시 갱신 지연 경고 문구가 터미널에 표시된다.
- **AC-3**: 업그레이드 성공 메시지에 실제 갱신된 버전이 올바르게 출력된다.
- **AC-4**: `tests/test_upgrade_cli.py` 단위 테스트가 추가/갱신되고 전체 테스트 스위트 100% Pass 및 `forgeflow check --all --strict` 🟢 ALL PASSED를 달성한다.
- **AC-5**: `src/forgeflow/_version.py`가 `0.1.10`으로 승격된다.
