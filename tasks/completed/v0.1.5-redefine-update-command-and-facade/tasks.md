# Tasks: Redefining ForgeFlow Update Command & Facade Integration

- **Release ID**: `v0.1.5-redefine-update-command-and-facade`
- **Risk Tier**: Tier 3 (Critical)
- **Status**: READY FOR IMPLEMENTATION

---

## Task Checklist

### Phase 1: Core Scaffolder & CLI Update Implementation (Core)
- [x] Task 1.1: `src/forgeflow/scaffold.py`에 `TemplateScaffolder.update_repo_governance` 메서드 구현
- [x] Task 1.2: `src/forgeflow/cli.py`에 `update` 서브커맨드 및 `handle_update` 핸들러 구현

### Phase 2: Testing & Verification (Tests)
- [x] Task 2.1: `tests/test_update_cli.py` 작성 및 다양한 시나리오 단위 테스트 검증
- [x] Task 2.2: 전체 단위/통합 테스트 전수 실행 (`pytest`)

### Phase 3: Skills & Documentation (Skills & Docs)
- [x] Task 3.1: `scripts/install-skills.sh` 내 `update-forgeflow` 스킬 지침 갱신 (`forgeflow upgrade` ➔ `forgeflow update` 체인)
- [x] Task 3.2: `~/.agents/skills/update-forgeflow/SKILL.md` 동기화
- [x] Task 3.3: `README.md` 및 `docs/spec/FLOW_SPEC.md`에 `forgeflow update`와 `forgeflow upgrade` 설명 최신화

### Phase 4: Version Bump & Governance Audit (Sign-Off & Seal)
- [x] Task 4.1: `src/forgeflow/_version.py`를 `0.1.5`로 판올림
- [x] Task 4.2: 하네스 거버넌스 감사 `forgeflow check --stage 2` 및 `forgeflow check --all --strict` 실행
- [x] Task 4.3: Gate 2 `QA_SIGNOFF.md` 작성 및 승인
- [x] Task 4.4: Gate 3 `RELEASE_SIGNOFF.md` 작성 및 릴리즈 패키지 밀봉
