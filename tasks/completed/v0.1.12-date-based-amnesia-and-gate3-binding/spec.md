# Specification: Date-Based Amnesia Verification and Gate 3 Final Single-Binding

- **Release ID**: `v0.1.12-date-based-amnesia-and-gate3-binding`
- **Created Date**: 2026-10-24
- **Risk Tier**: **Tier 3 (Core / Governance Control-Plane - Harness & Diagnostics)**

---

## 1. 개요 및 목적 (Overview & Purpose)

본 릴리즈는 과거 2026-10-20 이전의 구버전 ForgeFlow(v0.4.4 ~ v0.23.0)와 v0.1.0 이후의 신규 프레임워크 환경을 시간적·구조적으로 완벽하게 구분하기 위해 **날짜 기반 기억상실 규범(Date-Based Amnesia Policy: 기준일 2026-10-20)**을 진단 엔진에 실질적으로 반영한다.
동시에 Gate 2 시점의 성급한 커밋 SHA 고정으로 인해 발생하던 중간 문서 작성 마찰을 원천 해소하기 위해, **Gate 3 최종 릴리즈 커밋에서의 단일 바인딩 구조**를 확립하고 사양서를 정비한다.

---

## 2. 세부 요구사항 (Detailed Requirements)

### 2.1 진단 엔진 날짜 및 구조 기반 Amnesia 판정 (`src/forgeflow/diagnostics.py`)
- **기준일**: **2026-10-20** (KST 기준 `2026-10-20 00:00:00`, timestamp `1792422000`)
- **판정 로직**:
  1. **구조적 규격 검사 (Structure Check)**:
     - 2026-10-20 v0.1.0 이후 공식 표준인 Spec Kit 하이브리드 필수 자산(`.specify/memory/constitution.md`)이 리포지토리에 존재하는지 검사.
     - `.forgeflow.json` 내에 구버전 잔재 필드(`required_documents`, `default_tier` 등)가 존재하는지 검사.
  2. **시간 및 버전 판정 (Date & Version Check)**:
     - 설정 파일(`.forgeflow.json`)의 `mtime`이 2026-10-20 이전인 경우 레거시로 감지.
     - 버전이 `0.1.0` 미만이거나, 과거 리셋 전 버전(예: `0.21.x`, `0.22.x`, `0.23.x`)이면서 신규 Spec Kit 구조가 없는 경우 레거시로 감지.
     - 미래에 자연스럽게 도달할 `0.22.0+` 신규 버전은 Spec Kit 구조와 2026-10-20 이후 날짜를 통해 정상 최신 환경으로 완벽히 판별.

### 2.2 Gate 3 최종 단일 릴리즈 바인딩 사양 확립 (`src/forgeflow/harness.py`)
- **Gate 2 (QA Sign-Off)**:
  - 역할: 테스트 100% Pass 및 Linter 통과에 대한 "기술적 품질 합격 증명" 체크포인트.
  - 에이전트/QA 엔지니어의 자율 서명.
- **Gate 3 (Release Sign-Off & Seal)**:
  - 역할: 모든 패키지 부기(Bookkeeping: `tasks.md` 완료 체크, `RELEASE_NOTES.md`, `RELEASE_SIGNOFF.md` 작성)가 완료된 후 사용자 최종 Go/No-Go 승인을 거쳐 최종 릴리즈 커밋 SHA로 단 1회 영구 바인딩 및 패키지 밀봉.
  - 이를 통해 Gate 2와 Gate 3 사이의 불필요한 중간 SHA 불일치 마찰을 원천 차단.

### 2.3 사양서 및 헌법 텍스트 동기화
- `docs/spec/FLOW_SPEC.md` 및 `docs/spec/GATES_AND_LOOPS.md`:
  - Gate 2 기술 체크포인트와 Gate 3 최종 단일 릴리즈 바인딩 워크플로우를 SSOT로 명시.
  - Date-Based Amnesia 판별 규칙을 거버넌스 사양서에 명시.

### 2.4 버전 승격
- `src/forgeflow/_version.py`를 `0.1.12`로 승격.

---

## 3. 인수 조건 (Acceptance Criteria)

- **AC-1**: `.forgeflow.json`이 2026-10-20 이전 구버전(`0.22.1` 등)이거나 구버전 필드를 포함하는 경우 `forgeflow doctor`에서 `LEGACY_CONFIG_DETECTED` 경고가 정확히 발생한다.
- **AC-2**: 2026-10-20 이후 생성된 Spec Kit 구조를 가진 최신 프로젝트(`0.1.0` ~ `0.23.0+`)에서는 `LEGACY_CONFIG_DETECTED` 오탐 없이 `🟢 HEALTHY`로 진단된다.
- **AC-3**: Gate 2 통과 후 Gate 3 최종 밀봉까지의 패키지 문서 정리가 중간 QA 바인딩 실패 없이 원활히 진행되고, 최종 릴리즈 커밋에서 패키지가 안전하게 밀봉된다.
- **AC-4**: 전체 단위 테스트(294개 이상)가 100% PASS하고 `forgeflow check --all --strict`가 🟢 ALL PASSED를 달성한다.
- **AC-5**: `src/forgeflow/_version.py`가 `0.1.12`로 승격된다.
