# Release Sign-Off: Removal of Legacy Update Command & Obsolete Catalogs

- **Release ID**: `v0.1.4-remove-legacy-update-command`
- **Target Version**: `v0.1.4`
- **Release Sign-Off Date**: 2026-10-21
- **Risk Tier**: **Tier 3 (Critical / Core CLI Cleanup / Amnesia Policy Enforcement)**
- **Gate 1 Status**: APPROVED
- **Gate 2 QA Status**: APPROVED (`56e23ba`)
- **Gate 3 Verdict**: **APPROVED (Ready for Promotion)**

---

## 1. 릴리즈 성과 요약

1. **과거 유산(Legacy Update Command) 완전 제거**:
   - `forgeflow update` 서브커맨드 영구 제거.
   - 구시대 정적 바이트 카탈로그(`src/forgeflow/bundle_catalog.py`, `src/forgeflow/catalog_oracles/`) 및 관련 모듈(`src/forgeflow/update.py`, `tests/test_update.py`) 완전 삭제.
2. **CLI 인터페이스 단일화**:
   - 전역 런타임 업그레이드는 `forgeflow upgrade` 단일 명령어로 확립.
   - 작업 프로젝트 거버넌스 갱신은 스마트 파사드 스킬 `/update-forgeflow`로 확립.
3. **자체 버전 갱신**:
   - `ForgeFlow v0.1.4` 판올림 완료.

---

## 2. 최종 릴리즈 승인 서명 (Gate 3 Sign-Off)

- **Release Status**: **SEALED & PROMOTED**
- **Approved by**: AI Agent (Antigravity) & User Explicit Instruction
