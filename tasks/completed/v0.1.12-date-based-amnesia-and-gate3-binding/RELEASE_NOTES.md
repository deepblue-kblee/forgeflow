# Release Notes: ForgeFlow v0.1.12

- **Release ID**: `v0.1.12-date-based-amnesia-and-gate3-binding`
- **Release Version**: `v0.1.12`
- **Release Date**: 2026-10-24

---

## 1. 개요 (Overview)

ForgeFlow v0.1.12는 2026-10-20 이전 과거 구버전(v0.4.4 ~ v0.23.0)과 향후 자연스럽게 도달할 신규 버전(0.22.0+) 간의 버전 번호 충돌을 원천 차단하기 위해 **날짜 기반 기억상실 규범(Date-Based Amnesia: 기준일 2026-10-20)**을 진단 엔진에 실질적으로 반영했습니다.
동시에 Gate 2와 Gate 3 사이의 중간 SHA 불일치 마찰을 해소하기 위해 **Gate 3 최종 단일 릴리즈 바인딩 사양**을 확립했습니다.

---

## 2. 주요 개선 사항 (Key Improvements)

1. **Date-Based Amnesia (2026-10-20) 정밀 판별 로직 탑재**:
   - `diagnostics.py`에 파일 수정 시각(`mtime`), 기준일(`2026-10-20`), 및 Spec Kit 하이브리드 표준 자산(`.specify/memory/constitution.md`) 존재 여부를 교차 검증.
   - 과거 0.22.x/0.23.0 구버전 설정을 확실히 레거시로 감지하면서, 미래의 0.22.0+ 최신 정상 환경을 완벽히 구분.
2. **Gate 3 최종 단일 릴리즈 바인딩 확립**:
   - Gate 2는 기술적 품질 합격 체크포인트로 운영하고, 모든 패키지 문서 정리가 끝난 Gate 3 시점에서 최종 커밋 스냅샷을 단일 Release-SHA로 최종 결속하여 패키지를 밀봉.
