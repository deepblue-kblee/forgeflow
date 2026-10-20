# Tasks: Comprehensive Cleanup of Legacy Documentation & SHA Mechanisms

- **Release ID**: `v0.1.6-cleanup-legacy-spec-and-sha`
- **Risk Tier**: Tier 3 (Critical)
- **Status**: READY FOR IMPLEMENTATION

---

## Task Checklist

### Phase 1: Core Specifications & Packaged Templates Update (Specs)
- [x] Task 1.1: `docs/spec/FLOW_SPEC.md` 및 `src/forgeflow/templates/spec/FLOW_SPEC.md` 수정 (루프 정의, 스키마 Spec SHA256 삭제, 과거 버전 교정, 사전 심사 ➔ 명세 승인)
- [x] Task 1.2: `docs/spec/GATES_AND_LOOPS.md` 및 `src/forgeflow/templates/spec/GATES_AND_LOOPS.md` 수정 (Stage 4 ➔ Stage 3, 해시 재바인딩 삭제)
- [x] Task 1.3: `docs/spec/DISTRIBUTION_SPEC.md` 및 `src/forgeflow/templates/spec/DISTRIBUTION_SPEC.md` 수정 (upgrade/update 역할 분리)
- [x] Task 1.4: `docs/spec/PHILOSOPHY_AND_COMPASS.md` 및 `src/forgeflow/templates/spec/PHILOSOPHY_AND_COMPASS.md` 수정
- [x] Task 1.5: `docs/spec/REFACTORING_GUIDE.md` 및 `src/forgeflow/templates/spec/REFACTORING_GUIDE.md` 수정 (Stage 3 표기)
- [x] Task 1.6: `docs/spec/CHANGELOG.md` 및 `src/forgeflow/templates/spec/CHANGELOG.md` 수정 (v0.1.2 ~ v0.1.6 이력 완비)

### Phase 2: Constitution, Scaffolder & Project Documentation (Constitution & Docs)
- [x] Task 2.1: `.specify/memory/constitution.md` 제3조 루프 정의 수정
- [x] Task 2.2: `src/forgeflow/scaffold.py` 내장 헌법 텍스트 제3조 수정
- [x] Task 2.3: `scripts/install-skills.sh` 헌법 텍스트 제3조 수정
- [x] Task 2.4: `src/forgeflow/templates/GOVERNANCE.md` 과거 버전 번호 교정
- [x] Task 2.5: `README.md` 개요 및 워크플로우 내 잔재 문구 교정

### Phase 3: Version Bump & Verification (Tests & Governance)
- [x] Task 3.1: `src/forgeflow/_version.py`를 `0.1.6`으로 판올림 및 `pip install -e .` 실행
- [x] Task 3.2: 단위/통합 테스트 전수 실행 (`pytest`) 및 `test_scaffold.py` 템플릿 일치 검증
- [x] Task 3.3: `forgeflow check --stage 2` 및 `forgeflow check --all --strict` 실행 (6개 릴리즈 전수 🟢 통과)

### Phase 4: Sign-Off, Package Seal & Dogfooding (Sign-Off & Promotion)
- [x] Task 4.1: Gate 2 `QA_SIGNOFF.md` 작성 및 승인
- [x] Task 4.2: Gate 3 `RELEASE_SIGNOFF.md` 작성 및 릴리즈 패키지 밀봉
- [ ] Task 4.3: `main` 브랜치 머지 및 피쳐 브랜치 정리 (Fast-Path Close)
- [ ] Task 4.4: 세션 상태 문서 최신화
