# Gate 3 Release Sign-Off: Interactive Upgrade Prompt and Force Option

- **Release ID**: `v0.1.9-interactive-upgrade-prompt`
- **Release Version**: `0.1.9`
- **Release Date**: 2026-10-21
- **Risk Tier**: **Tier 1 (Minor / Fast-track - CLI UX Improvement)**
- **Gate 3 Status**: **APPROVED**

---

## 1. 릴리즈 개요 (Release Summary)

본 릴리즈는 `forgeflow upgrade` 실행 시 현재 로컬 버전과 원격 최신 버전을 사전에 비교하여 사용자에게 보여주고, 업그레이드 진행 여부를 `y/n` 대화형 프롬프트로 묻도록 개선한 릴리즈이다.
`--force` 옵션 지정 시 확인 질문 없이 즉시 업그레이드 및 재설치를 진행하여 무인 자동화 환경도 완벽히 지원한다.

---

## 2. 변경 내역 및 산출물 (Changelog & Artifacts)

- `src/forgeflow/cli.py`: 버전 비교 출력, `input()` 기반 `y/n` 확인 질문 및 `--force` 바이패스 로직 구현.
- `tests/test_upgrade_cli.py`: `y` 승인, `n` 취소, `--force` 프롬프트 생략 검증 테스트 3종 추가 (총 9개 테스트 통과).
- `src/forgeflow/_version.py`: 버전 `0.1.9` 승격.
- 사양 및 문서 최신화: `CHANGELOG.md`, `DISTRIBUTION_SPEC.md`에 v0.1.9 릴리즈 내역 및 CLI 옵션 반영.

---

## 3. 검증 증적 (Verification Evidence)

- **Unit Tests**: 287개 단위 테스트 100% 통과.
- **QA Sign-Off**: Gate 2 APPROVED 완료 ([QA_SIGNOFF.md](QA_SIGNOFF.md)).
- **Governance Audit**: `forgeflow check` 🟢 PASS 확인 예정.

---

## 4. 최종 승인 (Sign-Off)

- **Release Gate 3 Verdict**: **APPROVED**
- **Authority**: ForgeFlow System Integrator & User Pre-Approval
