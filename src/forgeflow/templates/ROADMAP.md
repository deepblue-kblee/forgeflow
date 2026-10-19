# 🗺️ Roadmap - {{RELEASE_ID}}

## 마일스톤 및 진행 현황 (Milestones & Status)

### Stage 1: 기획 및 설계 (Planning & Specification)
- [ ] `PRD.md` 작성 및 요구사항 ID 도출
- [ ] `DESIGN.md` 작성 및 RTM 추적 매트릭스 수립

### Stage 2: Gate 1 사전 승인 (Pre-Implementation Gate)
- [ ] Gate 1 심사 통과: APPROVED (Implementation Authorized)

### Stage 3: 격리 워크스페이스 구축 및 브랜치 분기
- [ ] 작업 브랜치 생성 및 C0 체크포인트 기록

### Stage 4: 격리 구현 및 자가 치유 루프 (Loop 2/3)
- [ ] 핵심 기능 구현
- [ ] 단위/통합 테스트 작성 및 실행 (100% Pass)
- [ ] 하네스 검증기 통과 (`harness check --strict`)

### Stage 5: QA Sign-off, Release Package 및 완료 (Gate 2 / Gate 3)
- [ ] `QA_SIGNOFF.md` 작성 및 Gate 2 승인
- [ ] `forgeflow lifecycle package-review` 검토 전이
- [ ] `COMPLETION_REPORT.md` 및 `RELEASE_SIGNOFF.md` 작성
- [ ] Gate 3 Release Sign-off 및 패키지 씰 (`forgeflow lifecycle seal`)
- [ ] 수명주기 완료 (`forgeflow lifecycle complete`)
