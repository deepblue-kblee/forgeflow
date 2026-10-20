# Tasks: Gate Clarity & Removal of Spec Hash Binding

- **Release ID**: `v0.1.2-clarify-gates-and-remove-spec-hash`
- **Risk Tier**: Tier 3 (Critical)
- **Status**: READY FOR IMPLEMENTATION

---

## Task Checklist

### Phase 1: Core Gatekeeper & Validator Update (Setup & Core)
- [x] Task 1.1: `src/forgeflow/cli.py`의 `verify_stage2_gatekeeper`에서 `spec.md` SHA256 해시 검사 로직 삭제 및 에러 메시지 갱신
- [x] Task 1.2: `src/forgeflow/validator.py`의 `validate_hybrid_doc`에서 `GATE1_REVIEW.md`의 `has_sha` 요구사항 및 에러 메시지 삭제
- [x] Task 1.3: `src/forgeflow/scaffold.py` 내의 해시 검증 관련 지침 문자열 정비

### Phase 2: Testing & Verification (Tests)
- [x] Task 2.1: `tests/test_stage2_gatekeeper.py`에서 `test_gatekeeper_sha_integrity`를 해시 유무와 무관한 승인 상태 검증 테스트로 개편
- [x] Task 2.2: 단위/통합 테스트 스위트 전수 실행 및 100% PASS 확인 (`pytest`)

### Phase 3: Documentation & SSOT Templates (Docs & Polish)
- [x] Task 3.1: `README.md`의 "엔드투엔드 개발 워크플로우" 섹션을 Stage(작업 단계)와 Gate(승인 관문) 분리 구조 및 실제 CLI 매핑 테이블로 개정
- [x] Task 3.2: `docs/spec/FLOW_SPEC.md` 및 `docs/spec/GATES_AND_LOOPS.md` 최신화
- [x] Task 3.3: `src/forgeflow/templates/spec/*` 템플릿 파일 동기화
- [x] Task 3.4: `AGENTS.md`의 수명주기 섹션 정비

### Phase 4: Version Bump & Governance Audit (Sign-Off & Seal)
- [x] Task 4.1: `src/forgeflow/_version.py` 및 `pyproject.toml`을 `0.1.2`로 판올림
- [x] Task 4.2: 하네스 거버넌스 감사 `forgeflow check --all --strict` 및 `check --stage 2` 실행 확인
- [ ] Task 4.3: Gate 2 `QA_SIGNOFF.md` 작성 및 최종 승인
- [ ] Task 4.4: Gate 3 `RELEASE_SIGNOFF.md` 작성 및 릴리즈 패키지 밀봉
