# ForgeFlow Current System State

- **종료 상태 (Exit Status)**: 🟢 정상 종료 (Graceful Exit, 2026-11-01 20:08 KST)
- **현재 버전**: `v0.1.23` (Delta-Zero Non-Increasing Warning Allowance in Baseline Review)
- **상태 판정**: 🟢 HEALTHY (모든 테스트 및 거버넌스 검증 통과)
- **배포 상태**: 사용자 계정 로컬(`~/.local/share/forgeflow`, `~/.local/bin`) `v0.1.23` 설치 완료
- **원격 동기화**: `main` == `origin/main` (`eece5a5`), ahead/behind 0/0, 태그 및 패키지 밀봉 완료
- **진행 중 릴리즈**: 없음 (`tasks/in-progress/` 비어 있음)
- **오픈 이슈**: 0건 (GitHub Issue #7 공식 종결 완료)

---

## 검증 및 정비 요약

- **단위/통합 테스트**: 343개 전원 통과 (`Ran 343 tests in 16.07s`, OK)
- **하네스 게이트 감사**: `forgeflow check --all --strict` 22개 릴리즈 전수 🟢 ALL PASSED
- **코드 스멜 검사**: `forgeflow review --strict` 🟢 PASSED
- **최신 밀봉 패키지**: `tasks/completed/v0.1.23-delta-zero-baseline-review/`

---

## 핵심 완수 기능 (v0.1.22 ~ v0.1.23, Issue #7)

1. **Delta-Zero 기존 Warning 비증가 허용 (v0.1.23)**:
   - `collections.Counter` 다중 집합 슬롯 매칭을 도입하여, 수정된 함수 스코프 내의 기존 Warning이라도 수량이 증가하지 않는다면 Gate 2 통과 허용 (`modified_scope_unchanged_warnings`로 분류 및 리포트에 잔존 주의 표기).
   - 사소한 1줄 패치나 국소 변경 시 기존 경고 해소를 위한 불필요한 과도 리팩토링 마찰 해소.
   - 함수 내에서 동일/신규 경고가 추가되거나 기존 수량을 초과하면 신규 경고(`new_warnings`)로 즉시 차단(Fail-Closed).
2. **`--findings-baseline <ref>` 기준선 비교 모드 (v0.1.22)**:
   - `forgeflow review`에 `--findings-baseline <ref>` 옵션을 제공하여, 지정된 git revision 대비 새로 생기거나 재발한 Warning 및 수정된 함수 스코프 내의 Warning만 strict 차단(Fail-Closed).
   - 기존의 `--strict` 전체 Warning 0건 동작은 100% 하위 호환 보존.
   - 수정되지 않은 함수에 위치한 기존 Warning은 Gate 2 차단에서 면제하되, 결과 리포트에 계속 투명하게 보존.
3. **구조적 Finding 식별 (Structural Fingerprinting) 및 스코프 추적**:
   - `CodeSmell`에 `scope` 필드를 추가하고 AST 방문 중 클래스/함수 스택을 추적하여 기록.
   - 줄 번호(`line_no`) 변동에 영향받지 않는 함수 스코프 및 식별자 기반 매칭 엔진을 도입하여 코드 추가/삭제로 인한 라인 이동 시 기존 Warning이 신규 경고로 오탐되는 문제 방지.
4. **스멜 검사기 오탐 교정**:
   - `SmellDetector`의 `Unused Import` 검사기에서 파이썬 컴파일러 지시자인 `from __future__ import annotations`를 런타임 미사용 식별자 경고 대상에서 제외하도록 교정.

---

## 누적 기반 기능 (v0.1.0 ~ v0.1.21)

- **배포본 XDG 표준화 및 사양서 디렉토리 격리/최적화 (v0.1.21)**: 배포 경로 `~/.local/share/forgeflow` 표준화, 사양서 `src/forgeflow/spec/` 분리 및 상황별 라우터(`spec/README.md`) 구축, 버전 스탬프(`spec/VERSION`) 및 Amnesia 지침 도입.
- **설정 파일 표준 경로 이전 (v0.1.20)**: `.forgeflow/config.json` 표준화 및 `forgeflow update` 시 구버전 자동 마이그레이션.
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
- **변경 이력**: [`docs/CHANGELOG.md`](file:///Users/deepblue/work/repo/forgeflow/docs/CHANGELOG.md)
- **사용자 매뉴얼**: [`README.md`](file:///Users/deepblue/work/repo/forgeflow/README.md)
- **루트 에이전트 지침**: [`AGENTS.md`](file:///Users/deepblue/work/repo/forgeflow/AGENTS.md)
