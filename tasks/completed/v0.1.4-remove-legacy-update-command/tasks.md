# Tasks: Removal of Legacy Update Command & Obsolete Catalogs

- **Release ID**: `v0.1.4-remove-legacy-update-command`
- **Risk Tier**: Tier 3 (Critical)
- **Status**: READY FOR IMPLEMENTATION

---

## Task Checklist

### Phase 1: CLI & Codebase Cleanup (Core)
- [x] Task 1.1: `src/forgeflow/cli.py`에서 `update` 관련 임포트, 서브파서, 디스패치 분기 삭제
- [x] Task 1.2: `src/forgeflow/update.py` 파일 삭제
- [x] Task 1.3: `src/forgeflow/bundle_catalog.py` 및 `src/forgeflow/catalog_oracles/` 디렉터리 삭제

### Phase 2: Test Suite Cleanup & Verification (Tests)
- [x] Task 2.1: `tests/test_update.py` 삭제 및 `tests/test_cli.py` 내 update 테스트 제거
- [x] Task 2.2: 전체 단위/통합 테스트 전수 실행 (`pytest`)

### Phase 3: Version Bump & Governance Audit (Sign-Off & Seal)
- [x] Task 3.1: `src/forgeflow/_version.py`를 `0.1.4`로 판올림
- [x] Task 3.2: 하네스 거버넌스 감사 `forgeflow check --stage 2` 및 `forgeflow check --all --strict` 실행
- [ ] Task 3.3: Gate 2 `QA_SIGNOFF.md` 작성 및 승인
- [ ] Task 3.4: Gate 3 `RELEASE_SIGNOFF.md` 작성 및 릴리즈 패키지 밀봉
