# Tasks: Purge Legacy Templates and Enable Spec Discovery

- **Release ID**: `v0.1.7-purge-legacy-templates-and-spec-discovery`
- **Risk Tier**: Tier 3 (Critical)
- **Status**: READY FOR IMPLEMENTATION

---

## Task Checklist

### Phase 1: Purge Legacy Templates & Scaffolder Modernization (Cleanup)
- [ ] Task 1.1: `src/forgeflow/templates/`에서 레거시 템플릿 5종(`PRD.md`, `DESIGN.md`, `ROADMAP.md`, `GOVERNANCE.md`, `RELEASE_NOTES.md`) 영구 삭제
- [ ] Task 1.2: `src/forgeflow/scaffold.py` 및 `tests/test_scaffold.py`에서 레거시 파일 의존성 제거 및 최신 스펙 템플릿 검증으로 갱신
- [ ] Task 1.3: `install.sh` 내 배포판 템플릿 정화(Purge) 스텝 추가

### Phase 2: Spec Discovery & Non-Destructive Boot Anchor (Documentation & Anchoring)
- [ ] Task 2.1: `.specify/memory/constitution.md` 및 `src/forgeflow/scaffold.py` 내장 헌법에 공식 사양서 참조 경로 주입
- [ ] Task 2.2: `scripts/install-skills.sh`, `~/.agents/skills/setup-forgeflow/SKILL.md`, `~/.agents/skills/update-forgeflow/SKILL.md`에 사양서 참조 안내 동기화
- [ ] Task 2.3: `src/forgeflow/scaffold.py`에 비파괴적 주석 마커 기반 세션 진입점 앵커 주입/갱신(`bind_boot_anchor`) 구현, `init`/`update` 연동 및 `tests/test_boot_anchor.py` 단위 테스트 검증

### Phase 3: Core Implementation of `forgeflow doc` CLI (CLI & Tests)
- [ ] Task 3.1: `src/forgeflow/cli.py`에 `doc` 서브커맨드 파서 및 `handle_doc` 핸들러 구현
- [ ] Task 3.2: `tests/test_doc_cli.py` 작성 및 단위 테스트 검증
- [ ] Task 3.3: `src/forgeflow/_version.py`를 `0.1.7`로 판올림 및 `pip install -e .` 실행

### Phase 4: Full Suite Verification & Governance Sign-Off (Audit & Seal)
- [ ] Task 4.1: 전체 단위/통합 테스트 전수 실행 (`pytest`)
- [ ] Task 4.2: 하네스 거버넌스 감사 `forgeflow check --stage 2` 및 `forgeflow check --all --strict` 실행
- [ ] Task 4.3: Gate 2 `QA_SIGNOFF.md` 작성 및 승인
- [ ] Task 4.4: Gate 3 `RELEASE_SIGNOFF.md` 작성 및 릴리즈 패키지 밀봉
- [ ] Task 4.5: `main` 머지 및 피쳐 브랜치 정리 (Fast-Path Close)
