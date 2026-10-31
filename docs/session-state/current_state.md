# ForgeFlow Current System State

- **종료 상태 (Exit Status)**: 🟢 정상 종료 (Graceful Exit, 2026-11-01 00:00 KST)
- **현재 버전**: `v0.1.20` (Relocate Configuration to .forgeflow/config.json with Update Migration)
- **상태 판정**: 🟢 HEALTHY (모든 테스트 및 거버넌스 검증 통과)
- **배포 상태**: 사용자 계정 로컬(`~/.local/forgeflow`, `~/.local/bin`) `v0.1.20` 설치 완료
- **원격 동기화**: `main` == `origin/main` (`98c5c57`), ahead/behind 0/0, 태그 `v0.1.20` 배포 완료
- **진행 중 릴리즈**: 없음 (`tasks/in-progress/` 비어 있음)

---

## 검증 및 정비 요약

- **단위/통합 테스트**: 325개 전원 통과 (`Ran 325 tests in 16.1s`, OK)
- **하네스 게이트 감사**: `forgeflow check --all --strict` 20개 릴리즈 전수 🟢 ALL PASSED
- **코드 스멜 검사**: `forgeflow review --strict` 🟢 PASSED
- **최신 밀봉 패키지**: `tasks/completed/v0.1.20-relocate-config-to-forgeflow-dir/`
- **최근 분석 보고서**: [`docs/session-state/speckit_skills_and_clarify_analysis.md`](file:///Users/deepblue/work/repo/forgeflow/docs/session-state/speckit_skills_and_clarify_analysis.md)

---

## 핵심 완수 기능 (v0.1.20)

1. **설정 파일 표준 경로 이전 (`.forgeflow/config.json`)**:
   - 프로젝트 루트 디렉터리의 정돈성을 위해, 기존 루트 `.forgeflow.json`을 `.forgeflow/config.json`으로 이전.
   - 신규 스캐폴딩(`forgeflow setup`, `scaffold_speckit_hybrid`, `init_project_governance` 등) 시 `.forgeflow/config.json`을 기본 생성.
2. **`forgeflow update` 하위 버전 자동 마이그레이션**:
   - 구버전 리포지토리(루트에 `.forgeflow.json`이 존재하는 프로젝트)에서 `forgeflow update` 실행 시, 기존 사용자 설정을 100% 보존하면서 `.forgeflow/config.json`으로 자동 마이그레이션 및 버전 승격.
   - 마이그레이션 완료 후 루트에 남아있던 구버전 `.forgeflow.json` 파일을 안전하게 삭제(unlink)하여 최신 프로젝트 레이아웃으로 일원화.
3. **투명한 하위 호환 폴백 (Graceful Fallback)**:
   - `ReleaseScanner`, `RuntimeTestRunner`, `SystemDiagnostics`, `resolve_auto_create_branch` 등 모든 설정 탐색 로직에서 `.forgeflow/config.json`을 우선 탐색하고, 구버전 프로젝트의 경우 루트 `.forgeflow.json`을 안전하게 폴백 조회하도록 보장.
4. **테스트 무결성**: 신규 단위 테스트 추가 (총 325개 테스트 100% 통과).

---

## 누적 기반 기능 (v0.1.0 ~ v0.1.19)

- **브랜치 자동 분기 제어 (v0.1.19)**: `.forgeflow/config.json`의 `governance.auto_create_branch` 옵션을 통한 격리 브랜치 생성 제어.
- **프로젝트별 테스트 타임아웃 지원 (v0.1.18)**: `governance.test_timeout_seconds`를 통한 타임아웃 오버라이드.
- **커스텀 설정 보존 (v0.1.17)**: `forgeflow update` 시 `.forgeflow/config.json` 커스텀 키 100% 보존.
- **2계층 지식 체계 (v0.1.16)**: Tier 1 `docs/spec/ANTI_PATTERNS.md`, Tier 2 `docs/adr/` (ADR 001 De-SHA, ADR 002 spec hash 제거).
- **거버넌스 엔진**: Stage 1~4 흐름과 Gate 1~3 승인 체계, 자가 치유 루프(Loop 2/3), 라이프사이클 상태 기계(`LifecycleStore`).
- **Spec Kit 하이브리드 번들링**: 필수 bash 스크립트 6종 및 마크다운 템플릿 번들링, `scaffold_speckit_hybrid` 자동 스캐폴딩.
- **배포/갱신 대칭 구조**: 전역 런타임 `forgeflow upgrade` (대화형 확인, `--force`, CDN 캐시 우회, 실설치 버전 검증) ↔ 로컬 거버넌스 `forgeflow update` (CHANGELOG 프리뷰, 커스텀 설정 보존).
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
