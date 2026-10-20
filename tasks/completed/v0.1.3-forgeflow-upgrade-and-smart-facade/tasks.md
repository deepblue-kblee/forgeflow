# Tasks: ForgeFlow CLI Upgrade & Smart Facade Skill

- **Release ID**: `v0.1.3-forgeflow-upgrade-and-smart-facade`
- **Risk Tier**: Tier 3 (Critical)
- **Status**: READY FOR IMPLEMENTATION

---

## Task Checklist

### Phase 1: Core CLI Upgrade Implementation (Core)
- [x] Task 1.1: `src/forgeflow/cli.py`에 `upgrade` 서브커맨드 정의 및 `handle_upgrade` 로직 구현
- [x] Task 1.2: 버전 비교 및 네트워크 예외 처리, JSON 출력 지원

### Phase 2: Testing & Verification (Tests)
- [x] Task 2.1: `tests/test_upgrade_cli.py` 작성 및 모킹 기반 단위 테스트 검증
- [x] Task 2.2: 전체 테스트 스위트 전수 실행 (`pytest`)

### Phase 3: Skills & Documentation (Skills & Docs)
- [x] Task 3.1: `scripts/install-skills.sh` 내 `update-forgeflow` 스킬 지침 갱신
- [x] Task 3.2: `~/.agents/skills/update-forgeflow/SKILL.md` 동기화
- [x] Task 3.3: `README.md` 및 `docs/spec/FLOW_SPEC.md`에 `upgrade` 명령어 및 스마트 파사드 안내 반영

### Phase 4: Version Bump & Governance Audit (Sign-Off & Seal)
- [x] Task 4.1: `src/forgeflow/_version.py`를 `0.1.3`으로 판올림
- [x] Task 4.2: 하네스 거버넌스 감사 `forgeflow check --stage 2` 및 `forgeflow check --all --strict` 실행
- [ ] Task 4.3: Gate 2 `QA_SIGNOFF.md` 작성 및 승인
- [ ] Task 4.4: Gate 3 `RELEASE_SIGNOFF.md` 작성 및 릴리즈 패키지 밀봉
