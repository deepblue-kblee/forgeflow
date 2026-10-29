# ForgeFlow Current System State

- **종료 상태 (Exit Status)**: 🟢 정상 종료 (Graceful Exit, 2026-10-30 KST)
- **현재 버전**: `v0.1.18` (Support Project-Level Regression Test Timeout)
- **상태 판정**: 🟢 HEALTHY (모든 테스트 및 거버넌스 검증 통과)
- **배포 상태**: 사용자 계정 로컬(`~/.local/forgeflow`, `~/.local/bin`) `v0.1.18` 설치 완료
- **원격 동기화**: `main` == `origin/main` (`e6cf60f`), ahead/behind 0/0
- **진행 중 릴리즈**: 없음 (`tasks/in-progress/` 비어 있음)

---

## 검증 및 정비 요약

- **단위/통합 테스트**: 318개 전원 통과 (`Ran 318 tests in 14.3s`, OK)
- **하네스 게이트 감사**: `forgeflow check --all --strict` 18개 릴리즈 전수 🟢 ALL PASSED
- **코드 스멜 검사**: `forgeflow review --strict` 🟢 PASSED
- **최신 밀봉 패키지**: `tasks/completed/v0.1.18-project-test-timeout/`
- **최근 분석 보고서**: [`docs/session-state/speckit_skills_and_clarify_analysis.md`](file:///Users/deepblue/work/repo/forgeflow/docs/session-state/speckit_skills_and_clarify_analysis.md)

---

## 핵심 완수 기능 (v0.1.18)

1. **프로젝트별 회귀 테스트 타임아웃 오버라이드 지원 (Issue #6)**:
   - `RuntimeTestRunner.resolve_test_timeout`을 통해 `.forgeflow.json`의 `governance.test_timeout_seconds`로 프로젝트별 테스트 타임아웃을 오버라이드.
   - 설정 누락 시 기존 60.0초 기본값을 유지하여 하위 호환성 보존.
   - `bool`, 비숫자, 비유한수(`inf`/`nan`), 0 이하 값은 암묵적 폴백 없이 `ValueError`로 fail-closed 차단.
2. **진단 엔진(`SystemDiagnostics`) 설정 검증 연동**:
   - `forgeflow doctor` 실행 시 `test_timeout_seconds`가 비정상 형식이면 `INVALID_TEST_TIMEOUT` 이상 징후로 검출하고 조치 가이드 제시.
3. **테스트 무결성**: `tests/test_runner.py` 신규 단위 테스트 12종 추가 (총 318개 테스트 100% 통과).

---

## 누적 기반 기능 (v0.1.0 ~ v0.1.17)

- **거버넌스 엔진**: Stage 1~4 흐름과 Gate 1~3 승인 체계, 자가 치유 루프(Loop 2/3), 라이프사이클 상태 기계(`LifecycleStore`).
- **Spec Kit 하이브리드 번들링**: 필수 bash 스크립트 6종 및 마크다운 템플릿 번들링, `scaffold_speckit_hybrid` 자동 스캐폴딩.
- **배포/갱신 대칭 구조**: 전역 런타임 `forgeflow upgrade` (대화형 확인, `--force`, CDN 캐시 우회, 실설치 버전 검증) ↔ 로컬 거버넌스 `forgeflow update` (CHANGELOG 프리뷰, 커스텀 설정 보존).
- **2계층 지식 체계**: Tier 1 `docs/spec/ANTI_PATTERNS.md`, Tier 2 `docs/adr/` (ADR 001 De-SHA, ADR 002 spec hash 제거).
- **사양서 발견성**: `forgeflow doc list|show` 기반 7대 공식 사양서 열람 인터페이스.
- **비파괴적 부팅 앵커**: `AGENTS.md` / `CLAUDE.md` 하단 재배치 방식의 멱등적 앵커 주입·해제.
- **이슈 트래커**: `forgeflow issue` CLI 기반 GitHub Issues 연동 및 `.cache/issues/` 로컬 캐시.

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
