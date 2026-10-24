# Implementation Plan: Date-Based Amnesia Verification and Gate 3 Final Single-Binding

- **Release ID**: `v0.1.12-date-based-amnesia-and-gate3-binding`
- **Created Date**: 2026-10-24
- **Risk Tier**: **Tier 3 (Core / Governance Control-Plane - Harness & Diagnostics)**

---

## 1. 아키텍처 및 세부 설계 (Architecture & Design)

### 1.1 진단 엔진 Date-Based Amnesia 로직 고도화 (`src/forgeflow/diagnostics.py`)
- **기준일 설정**: 2026-10-20 00:00:00 (KST 기준)
  - `AMNESIA_EPOCH_TS = 1792422000` (또는 UTC 기준 타임스탬프)
- **교차 판별 규칙**:
  1. **구조적 규격 검사**:
     - `.specify/memory/constitution.md` 부재 시 레거시 환경으로 판단
     - `.forgeflow.json` 내 구버전 잔재 필드(`required_documents`, `default_tier`) 존재 시 레거시 환경으로 판단
  2. **과거 버전 리셋 판별**:
     - `v_tuple < (0, 1, 0)`: 레거시
     - `(0, 21, 0) <= v_tuple <= (0, 23, 99)`이면서 Spec Kit 하이브리드 필수 자산(`.specify/memory/constitution.md`)이 없는 경우: 2026-10-20 이전 과거 구버전으로 확정 판단
  3. **미래 버전 호환성 보장**:
     - 향후 버전이 정상적으로 `0.22.0+`에 도달하더라도, Spec Kit 하이브리드 표준 자산이 존재하고 레거시 필드가 없으면 최신 환경으로 정상 인정.

### 1.2 Gate 3 최종 단일 릴리즈 바인딩 및 사양 간소화
- **Gate 2 (QA Sign-Off)**:
  - 테스트 100% Pass 및 Strict 정적 분석 통과에 대한 기술적 합격 증명 체크포인트.
- **Gate 3 (Release Sign-Off & Seal)**:
  - 릴리즈 패키지 부기 문서(`RELEASE_NOTES.md`, `tasks.md`, `RELEASE_SIGNOFF.md`)가 모두 완비된 후, 사용자 최종 승인 하에 최종 커밋 SHA를 단일 바인딩하여 패키지 밀봉.
  - 중간 단계의 SHA 불일치 마찰을 원천 차단.

### 1.3 사양서 및 템플릿 명문화
- `docs/spec/FLOW_SPEC.md` 및 `docs/spec/GATES_AND_LOOPS.md`:
  - Date-Based Amnesia 2026-10-20 기준일 및 판정 규칙 명시.
  - Gate 2 기술 체크포인트와 Gate 3 최종 단일 릴리즈 바인딩 수명주기 명문화.

### 1.4 버전 승격
- `src/forgeflow/_version.py`를 `0.1.12`로 승격.

---

## 2. 변경 파일 목록 (Target Files)
1. `src/forgeflow/diagnostics.py`: Date-Based Amnesia 판별 로직 고도화
2. `src/forgeflow/_version.py`: 버전 `0.1.12` 승격
3. `docs/spec/FLOW_SPEC.md`, `docs/spec/GATES_AND_LOOPS.md`, `docs/spec/CHANGELOG.md`: 사양 및 변경 이력 동기화
4. `src/forgeflow/templates/spec/*`: 템플릿 동기화
5. `tests/test_diagnostics.py`: Date-Based Amnesia 판별 단위 테스트 추가

---

## 3. 검증 전략 (Verification Strategy)
- 단위 테스트 실행: `PYTHONPATH=src python3 -m unittest discover -s tests -p "test_*.py"`
- 하네스 거버넌스 감사: `forgeflow check --all --strict`
- Gate 2 QA 승인 및 Gate 3 릴리즈 승인 완료 후 밀봉
