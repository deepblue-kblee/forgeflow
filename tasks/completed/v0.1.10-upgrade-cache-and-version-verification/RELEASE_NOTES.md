# Release Notes: ForgeFlow v0.1.10

- **Release ID**: `v0.1.10-upgrade-cache-and-version-verification`
- **Release Version**: `v0.1.10`
- **Release Date**: 2026-10-22

---

## 1. 개요 (Overview)

ForgeFlow v0.1.10은 `forgeflow upgrade` 실행 시 GitHub Raw CDN의 300초 강제 캐싱으로 인해 발생하던 버전 확인 불일치 및 메시지 표기 오류를 방지하기 위해 네트워크 캐시 우회(Cache-busting), 역전 버전 방어(Inversion guard), 그리고 설치 완료 후 실제 로컬 패키지 버전 검증 로직을 도입했습니다.

---

## 2. 주요 개선 사항 (Key Improvements)

1. **Cache-Busting 헤더 및 타임스탬프 쿼리**:
   - `raw.githubusercontent.com`에 버전 및 인스톨러 요청 시 `Cache-Control: no-cache, no-store, must-revalidate` 및 `Pragma: no-cache` 헤더 부여.
   - 요청 URL에 `?t={timestamp}` 타임스탬프 쿼리 파라미터를 추가하여 Fastly/Varnish CDN 엣지 노드의 캐시를 우회하고 항상 최신 커밋을 조회.
2. **원격 버전 역전 감지 (Inverted Version Guard)**:
   - CDN 캐시 전파 지연으로 인해 원격 버전이 로컬 버전보다 낮게 조회될 경우(`remote < current`), 이상 징후를 감지하고 터미널 경고 문구 및 JSON `warning` 필드를 출력.
3. **실설치 버전 재검증 및 메시지 정확성 보장**:
   - `install.sh` 실행 성공 후 사전 변수가 아닌 실제 설치된 `_version.py`를 직접 확인하여 정확한 업그레이드 완료 메시지(`🎉 Successfully upgraded ForgeFlow to v{installed_version}!`) 출력.
