# Architecture Plan: Gate Clarity & Removal of Spec Hash Binding

- **Release ID**: `v0.1.2-clarify-gates-and-remove-spec-hash`
- **Status**: APPROVED ARCHITECTURE
- **Risk Tier**: Tier 3 (Critical)

---

## 1. 아키텍처 및 설계 변경 (Architecture Overview)

### 1.1 게이트키퍼 검증기 (`cli.py` & `validator.py`)
- **`verify_stage2_gatekeeper` 함수**:
  - `tasks/in-progress/<pkg>/GATE1_REVIEW.md` 파일 존재 여부 확인.
  - 대소문자 무관 `APPROVED` 문자열 포함 여부 확인.
  - 기존의 `spec.md` SHA-256 해시 추출 및 비교 반복문 삭제.
  - 미승인 시 에러 메시지: `Please complete Stage 1 specification and obtain Gate 1 approval (GATE1_REVIEW.md with APPROVED verdict).` 로 정비.
- **`validate_hybrid_doc` 함수 in `validator.py`**:
  - `filename == "GATE1_REVIEW.md"` 분기에서 `has_sha` 조건 검증 삭제:
    ```python
    elif filename == "GATE1_REVIEW.md":
        has_approved = "APPROVED" in content.upper()
        status.passed = has_approved
        status.details = {"has_approved": has_approved}
        if not has_approved:
            status.errors.append("GATE1_REVIEW.md에 APPROVED 승인 명시가 없습니다.")
    ```

### 1.2 Stage와 Gate의 개념 모델 재정립
- **Stage (작업 수행 단계)**:
  - Stage 1: 기획 & 명세 작성 (`spec.md`)
  - Stage 2: 기술 설계 & 태스크 분해 (`plan.md`, `tasks.md`)
  - Stage 3: 격리 구현 & 테스트 (`src/`, `tests/`)
- **Gate (승인 및 사인오프 관문)**:
  - Gate 1: 명세 승인 (Spec Sign-Off) — Stage 1 종료 후, Stage 2/3 착수 전. `GATE1_REVIEW.md`에 승인 기록.
  - Gate 2: QA 품질 승인 (QA Sign-Off) — Stage 3 구현 완료 후, 릴리즈 승격 전. `QA_SIGNOFF.md`에 승인 및 커밋 SHA 기록.
  - Gate 3: 릴리즈 승인 및 패키지 밀봉 (Release Sign-Off) — 배포 및 밀봉 직전. `RELEASE_SIGNOFF.md`에 승인 기록 및 `tasks/completed/`로 원자적 이동.

### 1.3 문서화 및 CLI 매핑 테이블
- [README.md](../../README.md) 및 사양 문서의 워크플로우 섹션을 위의 Stage & Gate 모델로 개편.
- CLI 매핑:
  - Gate 1 검증: `forgeflow check --stage 2` (before_implement 훅 자동 실행)
  - Gate 2 QA 검증: `forgeflow review --strict`, 단위/통합 테스트, `forgeflow lifecycle package-review <qa-sha>`
  - Gate 3 릴리즈: `forgeflow lifecycle seal <rc-sha>` 및 `forgeflow lifecycle complete <release-id>`

---

## 2. 데이터 흐름 및 상태 전이 (State Transitions)

```text
[Stage 1: 기획/명세] ➔ spec.md
       │
  (Gate 1 승인: GATE1_REVIEW.md APPROVED)
       │
       ▼
[Stage 2: 기술 설계] ➔ plan.md, tasks.md
       │
[Stage 3: 격리 구현] ➔ code, tests (before_implement hook: check --stage 2)
       │
  (Gate 2 승인: QA_SIGNOFF.md APPROVED + QA SHA)
       │
       ▼
  (Gate 3 승인: RELEASE_SIGNOFF.md APPROVED)
       │
[밀봉 및 종료] ➔ tasks/completed/ 이동, 브랜치 정리
```
