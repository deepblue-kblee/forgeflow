# 🚦 ForgeFlow 게이트 기준 및 순환 루프 규범 (GATES_AND_LOOPS.md)

이 문서는 ForgeFlow v0.1.0 하이브리드 아키텍처(GitHub Spec Kit + ForgeFlow) 환경에서 기능 기획, 명세 승인(Gate 1), 기술 설계, 격리 구현, QA Sign-Off, 릴리즈 승격까지의 전 수명주기를 통제하는 게이트 통과 기준과 자율 자가 치유 루프(Self-Healing Loop) 규범을 정의하는 단일 진실 공급원(SSOT) 표준 명세이다.

---

## 1. 이중 엔진 거버넌스 및 워크플로우 개요

ForgeFlow는 실행과 통제를 분리하는 이중 엔진 모델을 채택한다:
1. **실행 엔진 (Worker) — GitHub Spec Kit**: 대화형 인터뷰를 통한 요구사항 명세(`spec.md`), 아키텍처 계획(`plan.md`), 원자적 태스크 분해(`tasks.md`) 및 TDD 순차 구현 주도.
2. **거버넌스 엔진 (Supervisor) — ForgeFlow**: 릴리즈 패키지(`tasks/in-progress/<release-id>`)의 상태 기계 관리, 게이트 통과 심사(Gate 1/2/3), 증적 바인딩 및 물리적 코드 작성 차단(Fail-Closed Gatekeeper).

```text
[Stage 1: 기획 & 명세]       /speckit.specify ➔ /speckit.clarify (spec.md 생성)
        │
        ▼
[Gate 1: 명세 승인]          GATE1_REVIEW.md (티어링 판정, 승인 서명 APPROVED)
        │
        ├─► [Fail-Closed] before_implement 훅: Gate 1 미승인 시 코드 작성 물리적 차단 (exit 1)
        ▼
[Stage 2: 기술 설계 & 분해]   /speckit.plan (plan.md) ➔ /speckit.tasks (tasks.md)
        │
        ▼
[Stage 3: 격리 구현 & 치유]   /speckit.implement (TDD 순차 구현)
        │                   └── [Loop 2 자가 치유] 테스트 실패 시 자율 수정-검증 (최대 5회, 완료 시 커밋)
        ▼
[Gate 2: QA 품질 승인]       QA_SIGNOFF.md (review --strict 통과, 100% 테스트 통과, QA-SHA 결속)
        │
        ▼
[Gate 3: 릴리즈 승인 & 밀봉] RELEASE_SIGNOFF.md, COMPLETION_REPORT.md
                            └── 패키지 밀봉: tasks/in-progress/ ➔ tasks/completed/ 이동
```

---

## 2. 위험도 등급 체계 (Risk Tiering Matrix)

과업의 복잡도와 변경 위험도에 따라 심사 및 검증 강도를 3단계로 분기한다. 모든 과업은 첫 파일 작성 전에 등급을 판정해야 한다.

### 작업 분류 및 최우선 판정 규칙
- **비변경 (Non-Change)**: 코드베이스, 설정, 인프라를 수정하지 않는 단순 질의, 설명, 상태 조회 요청은 거버넌스 수명주기 대상이 아니다.
- **도메인 위험도 우선 원칙**: 코드 변경 라인 수보다 도메인 위험도와 불확실성이 항상 우선한다. 하나의 Tier 3 신호라도 감지되면 즉시 Tier 3으로 fail-closed 분류한다.

| 등급 | 정의 및 대상 범위 | 필수 산출물 및 Gate 1 요건 | Gate 2 QA Sign-Off 요건 |
| :--- | :--- | :--- | :--- |
| **Tier 1 (Minor)** | 동작 불변 문구, 포맷팅, 일반 문서 수정, 또는 인터페이스/보안 영향이 없는 단일 모듈의 국소 버그 수정 | `spec.md`, `GATE1_REVIEW.md` (Self-Review PASS, 계획된 변경 경로 명시) | 전체 테스트 통과, 계획된 경로와 실제 변경 경로 일치 인증 |
| **Tier 2 (Standard)** | 새로운 기능 추가, 복수 모듈 수정, 단위/통합 테스트 추가 및 일반적인 리팩토링 | `spec.md`, `GATE1_REVIEW.md` (독립 시니어 리뷰어 1인 검토 및 승인) | 100% 테스트 통과, 정적 분석 오류 0건, 커밋 SHA 바인딩 |
| **Tier 3 (Critical)** | 인증/인가, 보안, 암호화, 데이터베이스 마이그레이션, 공개 CLI/API 변경, 코어 거버넌스 규칙 수정 | `spec.md`, `GATE1_REVIEW.md` (Security, Reliability, Maintainability 3대 독립 패널 승인 + 사용자 승인) | 3대 패널 전원 코드/테스트 승인, 커밋 SHA 불변 바인딩, 비파괴 프로브 검증 |

---

## 3. 게이트 정의 및 통과 기준 (Gate Criteria)

### Gate 1: 명세 승인 게이트 (Specification Sign-Off Gate)
- **위치**: Stage 1(기획/명세) 종료 시점 (Stage 2 기술 설계 및 Stage 3 구현 착수 직전)
- **통과 요건**:
  1. `tasks/in-progress/<release-id>/spec.md` 명세서 작성 완료.
  2. 요구사항별 검증 가능한 인수 조건(Acceptance Criteria) 명시.
  3. 리스크 등급(Tier 1/2/3) 판정 및 심사 완료:
     - Tier 1: 셀프 리뷰 체크리스트 완료 및 계획된 경로 확정.
     - Tier 2: 독립 시니어 심사관 1인 자문 및 설계 보완.
     - Tier 3: 보안, 안정성, 유지보수성 3대 관점의 독립 패널 병렬 심사 및 사용자 구두 승인.
  4. `GATE1_REVIEW.md`에 `Gate 1 Verdict: APPROVED` 최종 판정 기록.
- **Fail-Closed Gatekeeper 강제 훅**:
  - Spec Kit의 `before_implement` 훅(`forgeflow check --stage 2`)이 실행되어 `GATE1_REVIEW.md` 부재 또는 미승인 시 물리적으로 코드 작성을 사전 차단(`exit 1`)한다.

### Gate 2: QA 품질 승인 게이트 (QA Sign-Off Gate)
- **위치**: Stage 3 구현 완료 후, Gate 3 릴리즈 승격 전
- **통과 요건**:
  1. `spec.md`에 명시된 모든 인수 조건 충족.
  2. 단위 및 통합 테스트 100% Pass (Fail = 0, Error = 0).
  3. Linter 및 정적 분석(`forgeflow review --strict`) 오류 0건 (인지 복잡도 ≤ 15, 함수 LOC ≤ 50).
  4. 테스트가 통과된 최종 커밋 SHA를 `QA_SIGNOFF.md`에 결속 및 서명 발급.
  5. Tier 3 변경의 경우 격리 환경에서의 비파괴 런타임 프로브(Non-mutating probe) 전달성 검증 완료.

### Gate 3: 릴리즈 승인 및 패키지 밀봉 게이트 (Release & Package Seal Gate)
- **위치**: 최종 배포 및 운영 승격 시점 (Stage 3 및 Gate 2 통과 후)
- **통과 요건**:
  1. `RELEASE_SIGNOFF.md` 및 `COMPLETION_REPORT.md` 작성.
  2. 사용자 최종 승인(Go/No-Go) 확인.
  3. `tasks/in-progress/<release-id>` 디렉토리를 `tasks/completed/<release-id>`로 원자적 이동(Atomic Move)하여 패키지 영구 밀봉.

---

## 4. 자율 순환 루프 및 자가 치유 규범 (Remediation Loops)

### 4.1 Loop 2: 테스트-수정 자가 치유 루프 (Inner Remediation Loop)
Stage 3 구현 도중 단위/통합 테스트 실패는 작업 중단 사유가 아니며, 에이전트는 아래 순환 루프를 자율 수행한다:
1. **결함 식별**: 테스트 실패 메시지 및 스택 트레이스 분석.
2. **코드 수정**: 실패 원인에 국한된 최소한의 소스 코드 수정 (테스트 케이스 자체 완화 금지).
3. **재검증**: 관련 테스트 및 전체 테스트 스위트 재실행.
4. **원자적 커밋**: 모든 테스트 통과 확인 후 최종 구현 커밋(`git commit`).

### 4.2 자율 실행 한도 및 중단 규칙 (Stopping Conditions)
- **5회 자율 회복 한도**: 동일한 실패 지문(Failure Fingerprint)이 5회 연속 반복되면 무한 루프 방지를 위해 즉시 작업을 중지(`BLOCKED`)하고 사용자 입력을 대기한다.
- **진짜 멈춤 vs 가짜 멈춤 규범**:
  - **가짜 멈춤 (Non-Stop — 사용자 턴 종료 절대 금지)**: 단순 테스트 실패, 린트 오류, 사소한 문법 오류, 서브에이전트 단독 작업 완료. (즉시 Loop 2 재진입)
  - **진짜 멈춤 (True Stop — 오직 이 경우에만 사용자 대기 허용)**:
    1. 동일 결함 5회 연속 회복 실패 시.
    2. 명시적 외부 권한 경계 (Git 원격 푸시, 외부 비공개 토큰 요구 등).
    3. 아키텍처/명세 모순 발생 시 (Loop 3 회귀).
    4. Gate 2 QA 통과 후 Gate 3 사용자 Go/No-Go 최종 승인 대기.

### 4.3 Loop 3: 아키텍처/명세 모순 회귀 (Architecture Regression Loop)
구현 도중 `spec.md`의 요구사항 간 상호 모순이나 설계 결함이 발견된 경우, 코드를 억지로 끼워 맞추지 않고 즉시 설계를 보완하는 Loop 3으로 전환한다:
1. 모순 원인 및 대안을 명시하여 사용자에게 보고.
2. `spec.md` 및 `plan.md` 수정.
3. Gate 1 재승인(`GATE1_REVIEW.md` 갱신) 후 Stage 3 재진입.
