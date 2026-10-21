# ForgeFlow Current System State

- **종료 상태 (Exit Status)**: 🟢 정상 종료 (Graceful Exit, 2026-10-21 16:18 KST)
- **현재 버전**: `v0.1.7` (Purge Legacy Templates & Spec Discovery)
- **상태 판정**: 🟢 HEALTHY (모든 테스트 및 거버넌스 검증 통과)
- **배포 상태**: 사용자 계정 로컬(`~/.local/forgeflow`, `~/.local/bin`) v0.1.7 배포 완료

---

## 검증 및 정비 요약

- **단위/통합 테스트**: 282개 전원 통과 (Failure = 0, Error = 0)
- **하네스 게이트 감사**: `forgeflow check --all --strict` 7개 릴리즈 전수 🟢 ALL PASSED
- **코드 스멜 검사**: `forgeflow review --strict` 🟢 PASSED (결함 0건)
- **최신 밀봉 패키지**: `tasks/completed/v0.1.7-purge-legacy-templates-and-spec-discovery/`

---

## 핵심 완수 기능 (v0.1.7)

1. **레거시 템플릿 5종 영구 삭제**:
   - `src/forgeflow/templates/` 최상위에서 2026-10-20 이전 산출물(`PRD.md`, `DESIGN.md`, `ROADMAP.md`, `GOVERNANCE.md`, `RELEASE_NOTES.md`) 완전 제거.
   - `src/forgeflow/legacy_templates.py` 및 인라인 fallback으로 테스트 호환성 보존.
2. **배포판 템플릿 정화 로직 탑재**:
   - `install.sh` 실행 시 전역 패키지 디렉토리(`$PKG_LIB_DIR/templates/`)의 과거 잔재 파일 자동 삭제.
3. **사양서 발견성(Spec Discovery) 아키텍처 주입**:
   - `.specify/memory/constitution.md` 및 `scaffold.py` 내장 헌법, 스킬 문서에 7대 공식 사양서 단일 진실 공급원(SSOT) 참조 경로 주입.
4. **비파괴적 세션 진입점 앵커 엔진**:
   - `scaffold.py`에 `bind_boot_anchor` 및 `unbind_boot_anchor` 구현 (`AGENTS.md` / `CLAUDE.md` 사용자 내용 100% 보존, 멱등 갱신).
5. **`forgeflow doc` (호환 별칭 `spec`) CLI 구현**:
   - 터미널에서 7대 사양서 목록 및 상세 내용 조회(`doc list`, `doc show <spec>`, `--json`, `--path`).

---

## 핵심 경로

- **공식 플로우 상세설계서**: [`docs/spec/FLOW_SPEC.md`](file:///Users/deepblue/work/repo/forgeflow/docs/spec/FLOW_SPEC.md)
- **게이트/루프 규범**: [`docs/spec/GATES_AND_LOOPS.md`](file:///Users/deepblue/work/repo/forgeflow/docs/spec/GATES_AND_LOOPS.md)
- **Spec Kit 주입 규범 및 훅 통합**: [`docs/spec/SPECKIT_HOOKS_AND_NORMS.md`](file:///Users/deepblue/work/repo/forgeflow/docs/spec/SPECKIT_HOOKS_AND_NORMS.md)
- **엔지니어링 철학 헌장**: [`docs/spec/PHILOSOPHY_AND_COMPASS.md`](file:///Users/deepblue/work/repo/forgeflow/docs/spec/PHILOSOPHY_AND_COMPASS.md)
- **배포 규격서**: [`docs/spec/DISTRIBUTION_SPEC.md`](file:///Users/deepblue/work/repo/forgeflow/docs/spec/DISTRIBUTION_SPEC.md)
- **리팩토링 가이드라인**: [`docs/spec/REFACTORING_GUIDE.md`](file:///Users/deepblue/work/repo/forgeflow/docs/spec/REFACTORING_GUIDE.md)
- **변경 이력**: [`docs/spec/CHANGELOG.md`](file:///Users/deepblue/work/repo/forgeflow/docs/spec/CHANGELOG.md)
- **사용자 매뉴얼**: [`README.md`](file:///Users/deepblue/work/repo/forgeflow/README.md)
- **루트 에이전트 지침**: [`AGENTS.md`](file:///Users/deepblue/work/repo/forgeflow/AGENTS.md)
