# Release Sign-Off: Purge Legacy Templates and Enable Spec Discovery

- **Release ID**: `v0.1.7-purge-legacy-templates-and-spec-discovery`
- **Target Version**: `v0.1.7`
- **Release Sign-Off Date**: 2026-10-21
- **Risk Tier**: **Tier 3 (Critical / Core Templates, CLI Surface & Installer Lifecycle)**
- **Gate 1 Status**: APPROVED
- **Gate 2 QA Status**: APPROVED (`04367a6b7473a6e64c0c13e32d8eaccdf09ea603`)
- **Gate 3 Verdict**: **APPROVED (Ready for Promotion)**

---

## 1. 릴리즈 성과 요약

1. **레거시 템플릿 5종 영구 삭제**:
   - `src/forgeflow/templates/` 최상위에서 2026-10-20 이전 과거 산출물(`PRD.md`, `DESIGN.md`, `ROADMAP.md`, `GOVERNANCE.md`, `RELEASE_NOTES.md`)을 완전히 삭제하여 Date-Based Amnesia 정책을 철저히 관철.
   - `scaffold.py`에 `LEGACY_TEMPLATES` 모듈 분리 및 안전한 fallback을 제공하여 기존 단위 테스트 하위 호환성을 100% 보존.
2. **배포판 템플릿 정화 로직 탑재 (`install.sh`)**:
   - 인스톨러 배포 시 대상 라이브러리 디렉토리(`$PKG_LIB_DIR/templates/`)에서 구버전 레거시 파일들을 자동으로 정리(Purge)하도록 개선.
3. **사양서 발견성(Spec Discovery) 아키텍처 완비**:
   - `.specify/memory/constitution.md` 및 `scaffold.py` 내장 헌법에 7대 공식 사양서 단일 진실 공급원(SSOT) 참조 경로를 주입.
   - `scripts/install-skills.sh`, `setup-forgeflow`, `update-forgeflow` 스킬 문서에 사양서 참조 지침을 완전 동기화.
4. **비파괴적 세션 진입점 앵커 주입 (`bind_boot_anchor`)**:
   - 고유 식별 마커(`<!-- forgeflow:boot-anchor:start -->` / `end`)를 통해 `AGENTS.md` / `CLAUDE.md`의 기존 사용자 고유 지침을 100% 보존하면서 부팅 시퀀스 앵커를 인플레이스 갱신 및 안전하게 주입/해제하는 엔진 구현 (`test_boot_anchor.py` 7개 테스트 100% Pass).
5. **`forgeflow doc` (및 호환 별칭 `spec`) CLI 서브커맨드 구현**:
   - 터미널에서 7대 공식 사양서를 손쉽게 열람할 수 있는 목록 조회(`doc list`) 및 개별 사양 출력(`doc show <spec>`) 인터페이스 제공. 기계 가독형 `--json` 및 커스텀 경로 `--path` 완비 (`test_doc_cli.py` 11개 테스트 100% Pass).
6. **테스트 및 거버넌스 무결성**:
   - 총 282개 테스트 100% Pass, 7개 릴리즈 전수 하네스 감사 `forgeflow check --all --strict` 🟢 ALL PASSED.
   - 프레임워크 자체 버전 `ForgeFlow v0.1.7` 승격 완료.

---

## 2. 최종 릴리즈 승인 서명 (Gate 3 Sign-Off)

- **Release Status**: **SEALED & PROMOTED**
- **Approved by**: AI Agent (Antigravity) & User Explicit Approval
