# 📑 ForgeFlow의 Spec Kit 스킬 선별 및 Clarify 자율 실행 분석 보고서

- **작성 일자**: 2026-10-25
- **분석 대상**: GitHub Spec Kit 공식 7종 스킬 및 ForgeFlow 하이브리드 거버넌스 수명주기
- **관련 사양서**: [`FLOW_SPEC.md`](file:///Users/deepblue/work/repo/forgeflow/docs/spec/FLOW_SPEC.md), [`SPECKIT_HOOKS_AND_NORMS.md`](file:///Users/deepblue/work/repo/forgeflow/docs/spec/SPECKIT_HOOKS_AND_NORMS.md), [`GATES_AND_LOOPS.md`](file:///Users/deepblue/work/repo/forgeflow/docs/spec/GATES_AND_LOOPS.md), [`PHILOSOPHY_AND_COMPASS.md`](file:///Users/deepblue/work/repo/forgeflow/docs/spec/PHILOSOPHY_AND_COMPASS.md)

---

## 1. 개요 (Executive Summary)

ForgeFlow는 대화형 인터뷰와 원자적 TDD 구현을 주도하는 **GitHub Spec Kit (실행 엔진 / Worker)**과 단계별 게이트 심사 및 상태 격리를 주도하는 **ForgeFlow (거버넌스 엔진 / Supervisor)**을 결합한 하이브리드 구조로 동작합니다.

본 문서는 본 세션에서 확인된 다음 두 가지 핵심 아키텍처 의문과 결론을 영구 기록으로 정리합니다:
1. **Spec Kit 공식 7종 스킬 중 ForgeFlow에서 채택/배제한 스킬과 그 근거**
2. **Stage 1의 `clarify` (모호성 해소 인터뷰) 단계가 실전에서 거의 체감되지 않고 자율 진행된 이유**

---

## 2. Spec Kit 공식 7종 스킬 채택 및 배제 매트릭스

GitHub Spec Kit 공식 에이전트 스킬은 총 7종으로 구성되며, ForgeFlow는 이 중 **5종을 정식 채택**하고 **2종을 라이프사이클에서 배제**하였습니다.

| Spec Kit 공식 스킬 | 채택 여부 | ForgeFlow 매핑 단계 | 주관 역할 |
| :--- | :---: | :--- | :--- |
| `speckit-specify` (`/speckit.specify`) | ✅ **채택** | Stage 1: 기획 & 명세 | 자연어 의도 기반 `spec.md` 초안 생성 및 Triage |
| `speckit-clarify` (`/speckit.clarify`) | ✅ **채택** | Stage 1: 기획 & 명세 | 모호성 스캔 및 필요 시 대화형 인터뷰 수행 |
| `speckit-plan` (`/speckit.plan`) | ✅ **채택** | Stage 2: 기술 설계 & 분해 | 아키텍처, 데이터 모델, 모듈 인터페이스 수립 (`plan.md`) |
| `speckit-tasks` (`/speckit.tasks`) | ✅ **채택** | Stage 2: 기술 설계 & 분해 | TDD 순차 실행을 위한 원자적 체크리스트 도출 (`tasks.md`) |
| `speckit-implement` (`/speckit.implement`) | ✅ **채택** | Stage 3: 격리 구현 & 치유 | Gatekeeper 사전 훅 검증 후 순차 구현 및 Loop 2 자율 치유 |
| **`speckit-constitution`** (`/speckit.constitution`) | ❌ **배제** | - | *(ForgeFlow 불변 헌법 자동 주입으로 대체)* |
| **`speckit-analyze`** (`/speckit.analyze`) | ❌ **배제** | - | *(ForgeFlow 자체 Gate 1/2 및 CLI 감사로 대체)* |

---

### 2.1 `speckit-constitution`을 사용하지 않는 이유

1. **단일 진실 공급원(SSOT)에 의한 5대 불변 거버넌스 헌법 자동 주입**:
   - 순정 Spec Kit의 `speckit-constitution`은 사용자와 에이전트가 대화를 통해 프로젝트 헌법(`.specify/memory/constitution.md`)을 자유롭게 작성·수정하도록 유도합니다.
   - 하지만 ForgeFlow에서는 프레임워크의 핵심 통제 원칙으로서 **5대 불변 거버넌스 헌법**(① 무승인 구현 금지/No Code Before Gate 1, ② 가짜 멈춤 금지/No False Stopping, ③ 원자적 루프 정의, ④ 루프 예산 5회 및 진짜 멈춤, ⑤ 스펙 무단 하향 금지/No Spec Downgrade)을 고정 사양으로 가집니다.
   - 이 헌법은 `forgeflow init --speckit`, `setup-forgeflow`, `TemplateScaffolder`에 의해 프로젝트 초기화 시 기계적으로 주입 및 동기화되므로 대화형 생성 스킬이 불필요합니다.
2. **거버넌스 규범 임의 완화(Governance Downgrade) 방지**:
   - 에이전트나 작업자가 대화형 프롬프트를 통해 Gate 1 물리적 차단이나 Loop 2 자율 치유 한도 같은 핵심 거버넌스 장치를 임의로 삭제하거나 완화하는 위험을 원천 차단하기 위해 헌법을 프레임워크 배포 불변 영역으로 격리합니다.

---

### 2.2 `speckit-analyze`를 사용하지 않는 이유

1. **비구속적 조언(Advisory) 도구의 한계**:
   - 순정 Spec Kit의 `speckit-analyze`는 `spec.md`, `plan.md`, `tasks.md` 생성 후 구현 착수 전에 단순히 세 문서 간의 불일치를 LLM 프롬프트 수준에서 점검하여 텍스트 리포트를 출력하는 **읽기 전용 권고(Read-Only Advisory)** 도구입니다.
   - 강제적 차단 메커니즘이 없어 에이전트의 자의적 해석에 의존하는 취약점이 있습니다.
2. **ForgeFlow 자체 게이트(Gate 1/Gate 2) 및 CLI 감사 엔진으로 완전 대체**:
   - ForgeFlow는 프롬프트 레벨의 권고 대신, 기계적이고 엄격한 통제 관문인 **Gate 1 (명세 승인: `GATE1_REVIEW.md`)**과 **Gate 2 (QA 품질 승인: `QA_SIGNOFF.md`)**를 운영합니다.
   - **물리적 차단 (Fail-Closed Gatekeeper)**: Spec Kit 훅(`.specify/extensions.yml`)의 `before_implement`에 `forgeflow check --stage 2`가 연결되어 있어 Gate 1 승인 증적이 없으면 구현 진입 자체가 물리적으로 차단(`exit 1`)됩니다.
   - **기계적 품질 감사**: Gate 2에서는 정적 분석기(`reviewer.py`, `smell_detector.py`)를 통해 AST 기반 코드 스멜, 인지 복잡도(Cognitive Complexity ≤ 15), 함수 LOC 한도(≤ 50), 100% 테스트 통과 여부 및 커밋 SHA 바인딩을 기계적으로 검증합니다.
   - 따라서 중간에 단순 텍스트 검사를 수행하는 `speckit-analyze`는 ForgeFlow의 결정론적 하네스 게이트 시스템과 역할이 중복되며 불필요한 토큰과 절차를 소모하므로 수명주기에서 배제했습니다.

---

## 3. Stage 1 Clarify 단계의 자율 진행 및 체감 부재 원인 분석

실전 과업 수행 시 `/speckit.clarify` 인터뷰가 사용자에게 거의 노출되지 않고 자율 진행된 이유는 다음 3가지 메커니즘의 결합입니다:

### 3.1 AI 내부적 최적해 채택 및 자율 완결 규범
- `speckit-clarify` 스킬 명세는 모호성 질문을 생성할 때 항상 **`**Recommended:** Option A (권장 사유)`**를 AI가 먼저 도출하도록 규정하고 있습니다.
- 동시에 ForgeFlow 최상위 규칙([`AGENTS.md`](file:///Users/deepblue/work/repo/forgeflow/AGENTS.md#L125)) 제6조 **미완료 Gate 종료 금지 및 자율 오케스트레이션(Completion Integrity & Autonomous Orchestration)**에 따라:
  > *"사용자가 구현·수정·검증을 요청했고 추가 확인이 필요하지 않다면, Gate 2 QA Sign-off와 Gate 3까지 lifecycle을 계속 진행한다."*
- 따라서 내부 함수 설계, 에러 코드 분기, CLI 옵션 명칭 같은 기술적 세부사항은 사용자를 멈춰 세워 묻지 않고, **AI가 시스템 불변식(Zero-Dependency, Clean Green 등)에 부합하는 권장 선택지를 스스로 채택하여 `spec.md`에 바로 반영**하고 다음 단계로 전진합니다.

### 3.2 `speckit-clarify` 자체의 조기 종료(Early Exit) 규칙
- `speckit-clarify` 스킬 명세([`SKILL.md`](file:///Users/deepblue/.agents/skills/speckit-clarify/SKILL.md#L241))에 명시된 규칙:
  > *"If no meaningful ambiguities found (or all potential questions would be low-impact), respond: **'No critical ambiguities detected worth formal clarification.'** and suggest proceeding."*
- 실전에서 전달되는 사용자 요청이나 버그 리포트는 이미 해결해야 할 문제와 타깃이 구체적인 경우가 대부분입니다. AI가 요구사항을 스캔했을 때 구조를 흔들 만한 중대한 모호성이 없다고 판정되면 형식적인 질문을 만들지 않고 즉시 조기 종료(Skip)됩니다.

### 3.3 실용적 적응형 거버넌스 ("배보다 배꼽이 큰 관료주의 타파")
- ForgeFlow 최상위 철학인 [엔지니어링 나침반(`PHILOSOPHY_AND_COMPASS.md`)](file:///Users/deepblue/work/repo/forgeflow/docs/spec/PHILOSOPHY_AND_COMPASS.md#L39-L56)에 따라:
  - **가역적 결정 (Type 2 Door)**: 국소 버그 수정, 단일 모듈 리팩토링, 일반 기능 추가 등 실패해도 롤백이 쉬운 작업(Tier 1 ~ Tier 2)은 질답 인터뷰로 사용자의 턴을 낭비하지 않고 신속하게 Self-Review / Gate 1 승인으로 통과시킵니다.
  - **비가역적 결정 (Type 1 Door)**: 코어 아키텍처 전면 개편, 파괴적 인터페이스 변경, 보안 권한 변경 등 극히 위험한 경우에만 작업을 진짜 멈추고(**True Stop**) 사용자에게 구두 승인과 인터뷰를 요청합니다.

### 3.4 실전 증적 전수 조사 결과
- 리포지토리의 완료된 릴리즈 패키지([`tasks/completed/*/spec.md`](file:///Users/deepblue/work/repo/forgeflow/tasks/completed/v0.1.1-fix-speckit-prerequisites/spec.md)) 전수 조사 결과:
- 총 14개 릴리즈(`v0.1.1` ~ `v0.1.14`) 전체에서 `## Clarifications` 섹션이 생성된 이력이 0건으로 확인되었습니다.
- 이는 모든 과업이 사전에 명확한 인시던트 브리프와 요구사항을 갖추었거나, AI가 최적해를 자율 반영하여 신속히 Gate 1 승인으로 직행했음을 증명합니다.

---

## 4. 결론 및 시사점

1. **완벽한 역할 분리**:
   - **Spec Kit (Worker)**: 대화형 기획(`specify`), 모호성 해소(`clarify`), 아키텍처 설계(`plan`), 태스크 분해(`tasks`), TDD 구현(`implement`)의 **실행 전담**.
   - **ForgeFlow (Supervisor)**: 헌법 배포(`constitution`), 품질/정합성 감사(`analyze`), 3단계 게이트 승인(Gate 1/2/3)의 **통제 및 감사 독점 전담**.
2. **생산성과 거버넌스의 양립**:
   - 불필요한 형식적 인터뷰와 조언형 스킬을 배제함으로써 토큰 소모와 세션 마찰을 최소화하고, Fail-Closed 물리적 차단 및 AST 정적 분석을 통해 엔터프라이즈급 신뢰성을 유지합니다.
