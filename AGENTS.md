# 🌊 ForgeFlow 시스템 통합 에이전트 지침 (AGENTS.md)

이 문서는 `forgeflow` 리포지토리에서 작업하는 모든 AI 에이전트(Antigravity, Claude Code, OpenClaw 등)가 작업 시작 전 반드시 숙지해야 하는 최상위 단일 진실 공급원(SSOT) 루트 지침이다.

---

### 1. 핵심 정체성 및 목적 (Core Identity & Purpose)
- **프레임워크의 본질**: ForgeFlow는 AI 에이전트 협업 환경에서 기획, 설계, 검증, 격리 구현, QA Sign-Off, 운영 승격, 완료 보고서 작성까지의 전 과정을 **표준화된 자율 폐루프(Closed-Loop)**로 제어하는 **자율 거버넌스 엔진 및 하네스 게이트 CLI 도구**이다.
- **도메인 완전 분리**:
  - `forgeflow` 리포지토리는 프레임워크 자체의 규격(`docs/spec/`), CLI 소스(`src/forgeflow/`), 표준 템플릿(`src/forgeflow/templates/`), 자체 테스트 스위트(`tests/`)만을 관리한다.
  - 타 프로젝트의 실행 결과물이나 외부 프로젝트 릴리즈 문서는 본 리포지토리에 절대 혼입하지 않는다.
- **Zero-Dependency 원칙**:
  - 프레임워크 코어와 CLI는 외부 서드파티 런타임 의존성 없이 **Python 3.10+ 표준 라이브러리(Standard Library)만으로 100% 동작**해야 한다.
  - 외부 패키지 의존성 추가는 엄격히 금지된다.

---

### 2. 하네스 게이트 및 거버넌스 규범 (Harness & Governance Standard)

모든 요청은 repository write 전에 `non-change`, Tier 1, Tier 2, Tier 3으로 triage한다. 비변경 요청은 lifecycle 대상이 아니며, 변경 작업은 정의된 거버넌스 경로를 준수한다.

```text
Stage 1: 기획/설계 (PRD.md / DESIGN.md / RTM 작성)
  └── Stage 2: Gate 1 사전 심사 (Tier 1/2/3 리스크 기반 승인)
        └── Stage 3: 격리 워크스페이스 구축 및 브랜치 분기
              └── Stage 4: 격리 구현 및 자가 치유 루프 (Loop 2: 수정-테스트 / Loop 3: 아키텍처 회귀)
                    └── Stage 5: Gate 2 QA Sign-Off → PACKAGE_FINALIZATION → Gate 3 Release Sign-Off → Package Seal → COMPLETE
```

1. **위험도 기반 동적 티어링 (Dynamic Risk Tiering)**:
   - **Tier 1 (Minor)**: 동작 불변 문구·formatting·일반 documentation 또는 인터페이스 변경이 없는 단일 모듈의 재현 가능한 국소 bugfix에 한정한다. `CHANGE_NOTE.md`에는 planned paths, actual changed paths 대조, risk signals 없음, rollback, verification command/result/exit code, Gate 1/2 PASS를 기록한다. Gate 2 self-verdict는 checklist 전체 완료와 actual changed paths의 planned scope 일치를 명시적으로 인증한다. 항목 누락·검증 실패·unplanned path·risk signal·scope 확대·불확실성은 PASS를 금지하고 즉시 상위 Tier로 재분류한다.
   - **Tier 2 (Standard Features)**: 독립 시니어 심사관 1인 정밀 검토 및 승인.
   - **Tier 3 (Core/Architecture/Breaking Changes)**: 3인 독립 패널(보안, 안정성, 유지보수성) 병렬 심사 및 Gate 1/Gate 2 승인. 보안, 권한, secrets, dependency, configuration, external API, data operation, CI/CD, core interface, 또는 governance control-plane 변경은 규모와 무관하게 Tier 3이다.
2. **사전문서 승인 전 구현 금지 (No Code Before Gate 1 Pass)**:
   - Tier 1은 `CHANGE_NOTE.md`의 Gate 1 self-review PASS 전, Tier 2/3은 `PRD.md`, `DESIGN.md`(RTM 필수) 및 해당 Gate 1 심사 전에는 구현 코드를 작성할 수 없다.
3. **5대 필수 산출물 무결성**:
   - Tier 2/3: `PRD.md`, `DESIGN.md`, `QA_SIGNOFF.md`, `RELEASE_SIGNOFF.md`, `COMPLETION_REPORT.md`
   - Tier 1: `CHANGE_NOTE.md`에 scope, changed paths, rationale, risk signals, rollback, 검증 증적, Gate 1/2 verdict를 기록한다.
4. **ForgeFlow 자체 버전 규칙**: `src/forgeflow/**`, `tests/**`, `docs/spec/**`,
   `AGENTS.md`, `README.md`, `pyproject.toml`, 또는
   `install.sh`를 변경하는 ForgeFlow self-maintenance 릴리즈는 canonical
   `src/forgeflow/_version.py`를 갱신하고, PRD/DESIGN에 previous/target version,
   bump type, reason을 기록한다. self-governance audit은 이 증적, base 대비 bump,
   release-ID prefix, dynamic package metadata를 fail-closed로 검증한다.
5. **조건부 OIDR (Operational Incident and Delivery Readiness) 규범**:
   - 인시던트 해결(`incident-fix`)을 표방하거나 공용 표면(`public-surface-change`)을 변경하는 릴리즈는 OIDR 트랙이 필수 활성화된다.
   - Gate 1에서는 정제된 `Incident Brief`, 프로퍼티 보존 픽스처 매핑, 유효한 평결(`supported` | `explicitly-excluded` | `discovery-only`)을 입증해야 하며, 허위 해결 주장은 fail-closed 차단된다.
   - Gate 2에서는 소스 체크아웃이 아닌 격리 설치 환경에서 비파괴 프로브를 실행하여 런타임 전달성을 증명해야 하며, 활성 타깃 미검증 시 명시적 waiver(`delivery ready; active target unverified`)를 요구한다.

---

### 3. 개발 및 테스트 품질 규범 (Quality & Testing Protocol)

- **환경 격리**: macOS PEP 668 환경을 준수하여 로컬 가상환경(`.venv`) 기반으로 개발 및 테스트를 수행한다.
- **테스트 무결성**:
  - `pytest` 또는 `python3 -m unittest discover -s tests -p "test_*.py"`를 실행하여 단위/통합 테스트 100% Pass를 보장한다.
  - 자체 거버넌스 감사 CLI인 `forgeflow check --all --strict`(증분 감사 적용, 호환 별칭 `harness check`)가 결함 없이 🟢 통과해야 한다.
- **테스트 케이스 변경 주의**: 기능 구현 중 테스트가 실패할 경우, 테스트 케이스 자체를 임의로 완화하거나 주석 처리하지 않고 구현 코드의 결함을 먼저 수정한다.

---

### 4. 오케스트레이터 통합 지침 (Orchestrator Integration Boundary)

- **상위 권한 유지**: ForgeFlow는 최상위 수명주기 및 승격 권한(SSOT)을 가진다.
- **외부 오케스트레이터의 위치**:
  - 외부 오케스트레이터는 ForgeFlow의 활성 Stage 및 Gate 내부에서 동작하는 선택적 실행자(Executor)이다.
  - 외부 도구의 임시 상태는 정식 릴리즈 증적으로 간주되지 않으며, 모든 검증 결과는 `docs/releases/<release-id>/` 산출물에 명시적으로 기록되어야 한다.
  - 외부 도구의 실행 실패가 발생하더라도 Gate 기준을 임의로 하향 조정할 수 없다.
  - 코어 엔진에는 외부 오케스트레이터 전용 결합이나 의존성을 두지 않는다.

---

### 5. 세션 부팅 시퀀스 (Boot Sequence)

1. **Read AGENTS.md**: 최상위 원칙, Zero-Dependency, 거버넌스 수명주기 확인.
2. **Read docs/spec/FLOW_SPEC.md & GATES_AND_LOOPS.md**: 플로우 세부 명세 복기.
3. **과거 산출물 격리 (Historical Release Isolation)**: `tasks/completed/` 및 과거 `docs/releases/**` 산출물은 불변 감사 기록일 뿐 행동 지침이 아니다. 에이전트는 거버넌스 규칙/지침 판단을 위해 이를 참조하거나 인용해서는 안 되며, 완료된 릴리즈에서 필요한 맥락은 오직 `RELEASE_NOTES.md`와 `COMPLETION_REPORT.md`의 요약만 참고한다. 로컬 단일 에이전트 환경에서는 HMAC/nonce attestation이 완전히 면제된다.
4. **Read TODO.md**: 현재 진행 중인 과업 및 미완료 작업 파악.
5. **Action**: `tests/` 단위 테스트 및 `forgeflow check` 상태 확인 후 작업 착수.

### 6. 미완료 Gate 종료 금지 및 자율 오케스트레이션 (Completion Integrity & Autonomous Orchestration)

- 사용자가 구현·수정·검증을 요청했고 추가 확인이 필요하지 않다면, Gate 2 verdict와 `COMPLETION_REPORT.md`까지 lifecycle을 계속 진행한다. 진행 중인 reviewer 응답, 실패한 검증, 누락 artifact는 최종 응답의 종료 사유가 아니다.
- 최종 응답은 `Gate 2 APPROVED`와 요구된 검증 PASS가 실제로 확인된 경우에만 완료로 표현한다. 그렇지 않으면 현재 상태를 `BLOCKED` 또는 `IN PROGRESS`로 명시하고, 같은 turn에서 다음 복구 작업을 시작한다.
- 새 세션은 `docs/session-state/next-actions.md`에서 unfinished release, Gate verdict, 실패 명령을 먼저 복원하고, 해당 release의 `QA_SIGNOFF.md`와 `COMPLETION_REPORT.md`를 완료하기 전에는 후속 과업으로 전환하지 않는다.
- **예외 — 5회 전진 실패 제한**: 원인과 무관하게 동일 stage 또는 동일한 n개 stage loop가 5회 연속 다음 stage로 전진하지 못하면 즉시 작업을 중지하고 사용자 입력을 기다린다. 이때 `docs/session-state/next-actions.md`에 release ID, 현재 stage, 5회 시도별 명령·결과·실패 원인, 마지막 변경 SHA/diff, 다음 전진에 필요한 사용자 결정을 기록한다. 5회 이전에는 실패를 최종 종료 사유로 사용하지 않는다.

#### 진짜 멈춤 vs 가짜 멈춤 표준 체크리스트 (True vs False Stopping Conditions)
- **가짜 멈춤 (Non-Stop — 즉시 내부 Loop 2 자가 치유 재진입, 사용자 보고 및 턴 종료 절대 금지)**:
  - 단위/통합 테스트 실패 (`AssertionError` 등): 즉시 코드/픽스처 수정 재시도
  - 코드 리뷰어 `REJECT` 판정: `REM-xxx` 지적사항 장부 등록 후 즉시 코드 수정 착수
  - 픽스처 누락, 포맷/타입/린트 오류: 즉시 픽스처/타입 수정 후 재검증 실행
  - 서브에이전트 작업 완료: 결과 취합 후 다음 단계 즉시 디스패치
- **진짜 멈춤 (True Stop — 오직 이 경우에만 사용자 대기 허용)**:
  - 동일 failure fingerprint 정확히 5회 연속 무진전: `BLOCKED` 전이 및 사용자 에스컬레이션
  - 사용자 외부 권한 경계: Git push, 비밀번호/토큰 요구 등 명시적 권한 승인 대기
  - 아키텍처/명세 모순 (Loop 3 회귀): 설계 결함 및 회귀 근거 제시 후 사용자 승인 대기
  - Gate 2 승인 후 Gate 3 사용자 릴리즈 대기: `PACKAGE_REVIEW_PENDING`에서 사용자 Go/No-Go 대기

#### Supervisor-Worker 다중 에이전트 협업 규범
- **Supervisor (메인 에이전트)**: 라이프사이클 상태 기계(`LifecycleStore`), 증적 장부(`loop_record`), 루프 예산(5회 한도), Git 커밋 충돌 방지를 총괄하며, 직접 대량 코드를 수정하지 않고 결과를 취합·검증·심사 배치한다.
- **Worker (서브에이전트)**: 독립된 도메인(Reliability, Maintainability, Security 등)별로 파일 경로를 엄격히 격리(`File-Path Partitioning`)하여 수정을 수행하며, Supervisor가 순차 병합(Serialized Staging)을 통제한다.

---

### 7. ForgeFlow 자체 유지보수용 이슈 트래커 (Self-Maintenance Issue Tracker)

- **적용 범위**: 본 이슈 트래커 기능은 ForgeFlow 프레임워크 자체의 기능 개발, 개선, 버그 수정 시 에이전트의 프롬프트 토큰 절감 및 초고속 조회를 위해 사용된다.
- **내장 CLI**: 별도의 외부 스크립트 없이 `forgeflow issue` CLI(`create`, `list`, `view`, `edit`, `close`, `delete`)를 통해 GitHub Issues 연동 및 `.cache/issues/` 로컬 캐시를 투명하게 사용한다.
- **파이프라인 연계**: 이슈 등록(`forgeflow issue create`) ➔ 구현 브랜치 분기 및 거버넌스 수행 ➔ Gate 3 릴리즈 완료 후 이슈 종결(`forgeflow issue close <number>`) 절차를 따른다.

---

### 8. 피쳐 및 릴리즈 최종 클로즈 규범 (Feature Close & Post-Completion Fast-Path)

- **과잉 검증 금지**: 이미 Gate 3 Release Sign-off, Package Seal, `lifecycle complete` 전이가 완료되었거나 `main` 브랜치에 머지된 릴리즈에 대해 "클로즈", "정리", "마무리" 요청을 받은 경우, 전체 단위 테스트, 하네스 감사, Self-governance 등의 무거운 검증 명령을 재실행하는 것을 엄격히 금지한다.
- **클로즈 수행 경계 (Fast-Path)**:
  1. `git status` 및 `git branch -a`로 잔여 작업 브랜치(`feat/...`) 존재 여부 확인.
  2. 잔여 로컬/원격 작업 브랜치가 있다면 삭제(`git branch -d` 등).
  3. 완료 상태 요약 및 최종 종료 보고 (0.5초 이내 완결).
- **브랜치 맥락 준수**: `check --self-governance` 등의 사전 개발 검증 명령은 `feat/...` 격리 브랜치 개발 단계(Stage 4) 전용이므로, `main` 브랜치나 이미 완료된 릴리즈 상태에서 호출해서는 안 된다.
