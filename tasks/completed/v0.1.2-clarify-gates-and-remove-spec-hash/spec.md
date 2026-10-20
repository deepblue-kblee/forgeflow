# Specification: Gate Clarity and Removal of Spec Hash Binding

- **Release ID**: `v0.1.2-clarify-gates-and-remove-spec-hash`
- **Created**: 2026-10-20
- **Risk Tier**: **Tier 3 (Critical / Governance Control-Plane / Public Documentation)**
- **Status**: DRAFT (Stage 1 Specification)

---

## 1. 배경 및 문제 정의 (Background & Problem)

1. **Gate 1/2/3 위치 및 승인 주체의 모호성 (GitHub Issue #2)**:
   - "Stage 2: Gate 1 사전 심사"라는 표현으로 인해, 이것이 심사 단계인지 승인 단계인지, 그리고 사용자의 sign-off는 어디서 이루어지는지 구분이 불분명했습니다.
   - Stage(작업 수행 단계)와 Gate(품질 및 스펙 승인 관문)가 명확히 분리되지 않아 사용자 및 에이전트의 오케스트레이션에 혼선이 발생했습니다.
   - [README.md](../../README.md) 및 사양 문서에 `forgeflow gate1 review`, `forgeflow gate2 signoff`, `forgeflow release`와 같이 실제 CLI에 존재하지 않는 명령어가 안내되어 있었습니다.

2. **`spec.md` 해시 바인딩(Spec SHA256)의 에이전트 루프 유발 부작용**:
   - `GATE1_REVIEW.md`에 `spec.md`의 바이트 단위 SHA-256 해시를 강제 결속함으로써, 사소한 띄어쓰기, 줄바꿈(LF/CRLF), 마크다운 서식 정비, 오타 수정만으로도 해시가 불일치하여 Gatekeeper(`forgeflow check --stage 2`)가 실행을 Fail-Closed 차단했습니다.
   - 이는 에이전트가 "스펙 변조 ➔ Loop 3 회귀 ➔ Gate 1 재작성"의 불필요한 헛도는 무한 루프를 겪게 하는 핵심 원인이었습니다.
   - Git 자체가 이미 커밋 트리와 변경 이력을 완벽히 추적하고 있고 Gate 2에서 Acceptance Criteria 전수 검증을 수행하므로, 바이트 단위 암호학적 해시는 불필요한 마찰 요소입니다.

---

## 2. 요구사항 (Requirements)

- **REQ-1 (해시 바인딩 완전 제거)**:
  - `src/forgeflow/cli.py`의 `verify_stage2_gatekeeper`에서 `spec.md`의 SHA-256 해시 비교 로직을 삭제한다.
  - `src/forgeflow/validator.py`의 `validate_hybrid_doc`에서 `GATE1_REVIEW.md`의 `has_sha` 검사 요건 및 에러를 제거한다.
  - `GATE1_REVIEW.md`에 `Gate 1 Verdict: APPROVED`가 존재하면 해시 기재 여부와 무관하게 Gate 1 통과로 판정한다.
  - 게이트키퍼 실패 안내 문구에서 존재하지 않는 `forgeflow gate1 review` 권고를 제거한다.

- **REQ-2 (Stage와 Gate의 명확한 분리 및 Sign-Off 위치 확정)**:
  - 작업 단계(Stage)와 승인 관문(Gate)을 1:1 대응 분리하여 표기한다:
    - **Stage 1 (기획 & 명세 작성)**: `/speckit.specify` ➔ `/speckit.clarify` ➔ `spec.md` 작성
    - **Gate 1 (명세 승인 / Spec Sign-Off)**: `GATE1_REVIEW.md` 발행 및 승인. (Tier 1: AI 자체 승인, Tier 2: 독립 에이전트 검토, Tier 3: 3대 패널 심사 후 사용자 대화 승인). 통과 시 기술 설계 및 구현 잠금 해제.
    - **Stage 2 (기술 설계 & 태스크 분해)**: `/speckit.plan` ➔ `plan.md`, `/speckit.tasks` ➔ `tasks.md`
    - **Stage 3 (격리 구현 & 자가 치유)**: `/speckit.implement` (Gate 1 검증 가드 통과 후 TDD 구현, Loop 2 치유)
    - **Gate 2 (QA 품질 승인 / QA Sign-Off)**: `QA_SIGNOFF.md` 발행 (단위/통합 테스트 100% Pass, `forgeflow review --strict` 무결점, 커밋 SHA 바인딩). 통과 시 릴리즈 승격 허용.
    - **Gate 3 (릴리즈 승인 및 패키지 밀봉 / Release Sign-Off)**: `RELEASE_SIGNOFF.md` 발행 (사용자 Go/No-Go 최종 승인) ➔ `tasks/completed/`로 원자적 이동(Package Seal).

- **REQ-3 (문서 내 허위/미구현 CLI 명령 전면 교정)**:
  - `README.md`, `docs/spec/FLOW_SPEC.md`, `docs/spec/GATES_AND_LOOPS.md` 및 프레임워크 템플릿 파일들에서 `forgeflow gate1 review`, `forgeflow gate2 signoff`, `forgeflow release` 표기를 제거한다.
  - 실제 동작 명령어(`forgeflow check --stage 2`, `forgeflow review --strict`, `forgeflow lifecycle package-review`, `forgeflow lifecycle seal`, `forgeflow lifecycle complete`)로 매핑하여 6대 항목(Before, Run, Creates, User action, Done when, Unlocks) 요약 표를 제공한다.

- **REQ-4 (자체 버전 갱신)**:
  - `src/forgeflow/_version.py` 및 `pyproject.toml`을 `0.1.2`로 판올림한다.

---

## 3. 인수 조건 (Acceptance Criteria)

- **AC-1**: `forgeflow check --stage 2` 실행 시 `GATE1_REVIEW.md`에 `Gate 1 Verdict: APPROVED`가 있으면 `spec.md`의 해시 기재 여부나 내용 변경에 구애받지 않고 `exit 0`으로 성공 통과한다.
- **AC-2**: `GATE1_REVIEW.md`에 `APPROVED`가 없거나 파일이 부재한 경우 `exit 1`로 물리적 차단되며, 에러 메시지에 존재하지 않는 `forgeflow gate1 review` 대신 올바른 게이트 승인 획득 안내가 출력된다.
- **AC-3**: `forgeflow check --all --strict` 및 `validator.py` 감사 시 `GATE1_REVIEW.md`에 SHA256 해시가 없어도 결함으로 보고하지 않고 정상 통과한다.
- **AC-4**: `README.md` 및 `docs/spec/` 문서에 Stage와 Gate가 명확히 분리 표기되고, 실제 사용 가능한 CLI 명령과 사용자 승인 방법이 표로 제공된다.
- **AC-5**: 기존 테스트 스위트(`pytest`) 269개 및 신규 수정 테스트가 100% PASS한다.
- **AC-6**: `src/forgeflow/_version.py` 버전이 `0.1.2`로 갱신된다.

---

## 4. 계획된 변경 범위 (Planned Scope)

- `src/forgeflow/cli.py` (`verify_stage2_gatekeeper` 해시 검사 제거 및 안내 메시지 교정)
- `src/forgeflow/validator.py` (`GATE1_REVIEW.md` 해시 필수 검사 로직 제거)
- `src/forgeflow/scaffold.py` (거버넌스 템플릿 문자열 정비)
- `src/forgeflow/_version.py` (0.1.2 판올림)
- `tests/test_stage2_gatekeeper.py` (해시 제거 반영 및 승인 단독 검증 테스트로 갱신)
- `README.md` (Stage/Gate 명확 분리 및 실제 CLI 명령어 매핑 테이블 반영)
- `docs/spec/FLOW_SPEC.md` & `docs/spec/GATES_AND_LOOPS.md` (명세 및 다이어그램 최신화)
- `src/forgeflow/templates/spec/*` (동일한 SSOT 템플릿 동기화)
