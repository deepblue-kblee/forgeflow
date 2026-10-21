# Gate 3 Release Sign-Off: Append Boot Anchor to Root Guides

- **Release ID**: `v0.1.8-append-boot-anchor`
- **Release Version**: `0.1.8`
- **Release Date**: 2026-10-21
- **Risk Tier**: **Tier 1 (Minor / Fast-track - Local Scaffolding Improvement)**
- **Gate 3 Status**: **APPROVED**

---

## 1. 릴리즈 개요 (Release Summary)

본 릴리즈는 `AGENTS.md` 및 `CLAUDE.md` 파일에 ForgeFlow 세션 부팅 앵커를 주입할 때, 기존 상단/중간에 위치하던 주석 마커 블록을 완전히 삭제하고 문서 맨 마지막(하단)으로 이동하여 안전하게 추가하도록 개선한 마이너 릴리즈이다.
이를 통해 타깃 프로젝트의 메인 타이틀과 개요를 최상위에 온전히 유지하고 비침습적인 거버넌스 바인딩을 달성한다.

---

## 2. 변경 내역 및 산출물 (Changelog & Artifacts)

- `src/forgeflow/scaffold.py`: 정규식 클린징 기반의 앵커 삭제 및 맨 끝 추가(append) 엔진 구현.
- `tests/test_boot_anchor.py`: 상단/중간 위치 기존 주석 삭제 및 하단 재배치 검증 단위 테스트 2종 추가 (총 9개 테스트 통과).
- `src/forgeflow/_version.py`: 버전 `0.1.8` 승격.
- `docs/spec/CHANGELOG.md` & `src/forgeflow/templates/spec/CHANGELOG.md`: v0.1.8 변경 내역 등재.

---

## 3. 검증 증적 (Verification Evidence)

- **Unit Tests**: 284개 단위 테스트 100% 통과.
- **QA Sign-Off**: Gate 2 APPROVED 완료 ([QA_SIGNOFF.md](QA_SIGNOFF.md)).
- **Governance Audit**: `forgeflow check` 🟢 PASS 확인 예정.

---

## 4. 최종 승인 (Sign-Off)

- **Release Gate 3 Verdict**: **APPROVED**
- **Authority**: ForgeFlow System Integrator & User Pre-Approval
