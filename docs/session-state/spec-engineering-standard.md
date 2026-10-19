# 📐 엔지니어링 설계서 작성 표준 가이드 (Specification Engineering Standard)

> 본 문서는 차후 과업(이슈 #20: OIDR 트랙 등) 및 향후 시스템 설계 시 단번에 결함 없이 목적을 100% 달성하기 위한 실전 사양서 표준 규격서입니다.  
> 빅테크 최고 엔지니어링 조직(Amazon, Google, Stripe, Rust, NASA/FoundationDB)의 시스템 설계론과 최신 자율 코딩 에이전트(SWE-bench 상위 솔버, Devin, Claude Code)의 AI-Native 계약 명세 기법을 결합하여 정립되었습니다.

---

## 1. 문제 발견 및 도메인 경계 (Problem Framing & Boundaries)

### 1.1 4단계 요구사항 분해 프로토콜 (4-Layer Disentanglement Protocol)
사용자나 기획자가 요청한 "솔루션 선호(Stated Demand)"를 시스템 요구사항으로 오인하지 않고, 다음 4계층으로 엄격히 분해하여 근본 문제를 도출합니다.

1. **관측된 현상 (Observed Incident & Pain Point)**:
   - 인터페이스나 운영 로그에서 정량적으로 측정된 결함이나 비효율.
   - 예: 결제 재시도 시 4.2%의 요청에서 타임아웃 발생, 특정 복구 경로 통과 후 중첩된 예약 경계로 인해 문서 파싱 실패.
2. **표면적 요구 (Stated Demand)**:
   - 요청자가 제시한 특정 구현 방식 및 솔루션 선호 (Feature Request).
   - 예: "HTTP 타임아웃을 30초로 늘려달라", "단일 예약 경계만 남기도록 파일 재작성 명령 추가".
3. **근본 제약 및 원인 (Root Cause & Systemic Constraint)**:
   - 시스템 내부 상태 및 의존성 분석을 통해 밝혀진 병목.
   - 예: 외부 대행사 지연 시 DB 커넥션 풀 고갈, 기존 복구 로직이 중첩 블록을 단일 블록으로 인식하지 못하고 no-write 거절.
4. **본질적 과업 (Job-To-Be-Done, JTBD)**:
   - 시스템이 보장해야 하는 상태 전이 목표.
   - 예: 네트워크 지연 속에서도 이중 과금 없이 멱등하게 1회 완료되거나 안전하게 거절되는 상태 보장.

### 1.2 도메인 책임 경계 (System Domain Boundaries)
- **상태 소유권 원칙 (State Ownership Boundary)**: 자신이 라이프사이클과 영속성의 단일 진실 공급원(SSOT)인 엔티티만 경계 내부에 포함. 외부 상태는 읽기 전용 캐시나 비동기 이벤트로 격리.
- **장애 반경 최소화 (Blast Radius Isolation)**: 외부 컴포넌트의 실패(Crash, Hang)가 전파되지 않도록 엄격한 타임아웃과 서킷 브레이커 설정.
- **트랜잭션 경계 국소화 (Minimal Transaction Boundary)**: 분산 환경에서 2PC를 지양하고, 원자적 단일 로컬 트랜잭션 또는 사가(Saga) 패턴 적용.

### 1.3 비목표(Non-Goals) 3요소 공식
비목표는 구현자의 불필요한 추측과 스코프 확장을 차단하는 핵심 장치입니다.
`[배제 대상] + [기술적/이론적 배제 근거(Rationale)] + [대안 및 완화책(Mitigation)]`
- 예시:
  - 배제 대상: 크로스 리전 분산 트랜잭션 동기화 제외.
  - 배제 근거: CAP 정리에 따라 동기 복제 시 지연시간(p99 > 500ms)이 SLA(200ms)를 위반함.
  - 완화책: 카프카 기반 비동기 이벤트 복제와 배치 대사(Reconciliation)로 최종 일관성 위임.

---

## 2. 시스템 불변식 및 심층 방어 (Invariants & Defense)

### 2.1 3대 시스템 불변식 (Lamport TLA+ 원칙)
1. **상태 불변식 (Safety Property)**:
   - 시스템의 모든 도달 가능한 상태에서 항상 참이어야 하는 조건 ("나쁜 일은 결코 일어나지 않는다").
   - 예: `계좌 잔고 >= 0`, `아티팩트 해시는 고유함`, `비인증 요청에 대해 민감 데이터 유출 금지`.
2. **전이 불변식 (Transition Property)**:
   - 상태 $S_t \to S_{t+1}$ 전이 시 만족해야 하는 단조성 및 방향성 조건.
   - 예: `SEALED` 이후 `IN_PROGRESS`로의 역행 금지, 버전 번호 단조 증가.
3. **활성 불변식 (Liveness Property)**:
   - 유한 시간 내에 시스템이 반드시 바람직한 상태에 도달함을 보장 ("좋은 일은 반드시 완료된다").
   - 예: 큐에 유입된 작업은 타임아웃 내에 `SUCCESS` 또는 `FAILED`로 완결.

### 2.2 실패 모드 및 심층 방어 매트릭스 (Failure Modes & Defense Matrix)
- **네트워크 실패**: Stripe 방식의 멱등키(`Idempotency-Key`)와 페이로드 해시를 저장하여, 동일 키 재요청 시 이전 응답을 재생(Tape Recorder 패턴).
- **스토리지 실패**: Torn Write 방지를 위한 Atomic File Replacement (임시 파일 쓰기 후 fsync 완료 후 원자적 `rename`).
- **동시성 경합**: 조건부 쓰기(CAS) 및 TTL 기반 뮤텍스, 재시도 시 지터(Full Jitter)가 포함된 지수 백오프.

---

## 3. 결정론적 검증 오라클 (Deterministic Verification Oracle)

- **"테스트 통과"의 모호함 탈피**: 환경 변수, 시스템 시계, 스케줄링 순서에 의존하는 Flaky 테스트를 원천 배제.
- **정규화된 상태 다이제스트 (Canonical State Digest)**: 정규화 직렬화 후 SHA-256 해시를 산출하여 기대 골든 다이제스트와 바이트 단위 대조.
- **기계 판독 표준 종료 코드 (Exit Codes)**:
  - Exit Code 0: 완벽 성공
  - Exit Code 10: 입력 유효성 검증 실패 (안전 거부, 상태 변화 없음)
  - Exit Code 11: 멱등성 충돌
  - Exit Code 20: 선행 조건(Precondition) 미충족
  - Exit Code 99: 시스템 불변식 위반 (Fail-Closed 긴급 중단)

---

## 4. AI-Native 머신 리더블 실행 규범 (Agentic State Contract)

1. **폐쇄 세계 가정 (Closed-World Assumption)**:
   - 사양서에 명시되지 않은 외부 라이브러리 추가, 임의의 인터페이스 확장, 스캐폴딩(`TODO`, `pass`)을 전면 금지.
2. **유한 상태 전이표 (State Transition Matrix)**:
   - 자연어 기능 설명 대신 FSM 전이표를 작성하여 현재 상태, 이벤트, 사전 조건(Pre), 수행 동작, 전이 후 상태, 사후 조건(Post) 명시.
3. **RTM과 골든 픽스처(Fixture)의 1:1 결정론적 결속**:
   - `REQ-ID`와 테스트 함수, 고정된 입력 픽스처(Golden JSON)를 1:1로 결속하여 에이전트의 경계 조건 회피 차단.
4. **결함 지문(Failure Fingerprint)과 서킷 브레이커**:
   - `SHA256(test_name + exception_class + normalized_stack_trace)` 해시를 계산하여 동일 지문 5회 반복 시 교착(Cognitive Deadlock) 감지 및 즉시 에스컬레이션.
5. **테스트 코드 불변 잠금 (Test Immutability Lock)**:
   - 에이전트가 테스트 통과를 위해 테스트 코드를 수정/완화하는 행위(Reward Hacking)를 검증 게이트에서 엄격히 차단.

---

## 5. 10대 통합 엔지니어링 스펙 뼈대 (Standard Template)

```markdown
# [SPEC-ID] 시스템/기능 정밀 설계 명세서: [과업명]

## 1. 메타데이터 및 거버넌스 블록 (Document Metadata & Control)
- 문서 식별자: SPEC-YYYYMMDD-XXX
- 위험도 티어: Tier 1 | Tier 2 | Tier 3
- 대상 버전: Previous: vX.Y.Z -> Target: vA.B.C
- 상태: DRAFT | IN_REVIEW | APPROVED

## 2. 문제 정의 및 본질적 과업 (Problem Framing & JTBD)
- 2.1 관측된 현상 및 인시던트 데이터 (Observed Incident)
- 2.2 표면적 요구 vs 근본 원인 분석 (5-Whys)
- 2.3 본질적 과업 (Job-To-Be-Done)
- 2.4 도메인 책임 경계 (System Boundary Definition)

## 3. 목표, 시스템 불변식 및 비목표 (Goals, Invariants & Non-Goals)
- 3.1 정량적 목표 (Measurable Goals)
- 3.2 시스템 절대 불변식 (INV-01 Safety, INV-02 Transition, INV-03 Liveness)
- 3.3 비목표 (Non-Goals: 배제 대상 + 배제 근거 + 완화책)

## 4. 가이드 레벨 설명 (Guide-Level Specification / Mental Model)
- 사용자 멘탈 모델 및 구체적 CLI/API 실행 예제

## 5. 레퍼런스 레벨 기술 명세 (Reference-Level Technical Specification)
- 컴포넌트 토폴로지, FSM 상태 전이표, 엄격한 I/O 스키마

## 6. 실패 모드 및 심층 방어 (Failure Modes & Defense Matrix)
- 네트워크, 스토리지, 동시성 장애 모드별 방어 매트릭스

## 7. 결정론적 검증 오라클 (Deterministic Verification Oracle)
- 기계 판독 종료 코드, SHA-256 상태 다이제스트, 불변식 어설션 스위트

## 8. 대안 분석 및 트레이드오프 (Alternatives Considered)
- 검토 대안 Option A/B/C와 기각 사유, 도입 부채(Drawbacks)

## 9. 롤아웃, 호환성 및 마이그레이션 (Rollout & Migration Plan)
- 역호환성 보장 전략 및 원자적 롤백 절차

## 10. 내부 하드 FAQ 및 프리모템 (Internal Hard FAQ & Pre-Mortem)
- 혹독한 엔지니어링 질의응답 및 1년 후 가상 파국 시나리오 분석
```
