# Architecture & Implementation Plan: Legacy Cleanup & SHA Specification

- **Release ID**: `v0.1.6-cleanup-legacy-spec-and-sha`
- **Target Version**: `v0.1.6`
- **Status**: READY FOR TASK BREAKDOWN

---

## 1. 아키텍처 원칙 및 변경 범위 (Scope & Principles)

1. **단일 진실 공급원(SSOT) 및 불변식 보존**:
   - `docs/spec/` 파일들과 `src/forgeflow/templates/spec/` 파일들은 100% 동일한 내용을 유지해야 함.
   - 불필요한 해시 바인딩(`Spec SHA256`)은 완전히 제거하고 `APPROVED` 승인 증적 중심의 거버넌스를 확립.
2. **원자적 루프 정의 현대화**:
   - 자가 치유(Loop 2)는 로컬 작업 트리에서 `원인 분석 ➔ 코드 수정 ➔ 테스트 검증`을 반복하며, 성공 시 단 1회의 원자적 커밋을 생성.
3. **용어 및 단계 번호 단일화**:
   - `사전 심사` ➔ `Gate 1: 명세 승인 (Spec Sign-Off)`
   - `Stage 4` ➔ `Stage 3: 격리 구현 & 자가 치유`

---

## 2. 파일별 변경 상세 (Detailed File Edits)

### A. 사양 문서 그룹 (`docs/spec/` 및 `src/forgeflow/templates/spec/`)
1. **`FLOW_SPEC.md`**:
   - 제1장: `사전 심사(Gate 1)` ➔ `Gate 1: 명세 승인`
   - 제2장: `v0.5.0-cache-engine/`, `v0.4.1-query-engine/` ➔ `v0.1.0-sample/` 등 v0.1.x 예시, `"forgeflow_version": "0.1.0"`으로 수정.
   - 제2.3장 헌법 제3조: 루프 내 `git commit (새 SHA 발행)` 문구 제거 및 완료 시 원자적 커밋 생성으로 정정.
   - 제6.1장 스키마: `- Spec SHA256: <hash-of-spec.md>` 삭제.
2. **`GATES_AND_LOOPS.md`**:
   - 서문: `사전 심사` ➔ `명세 승인`
   - 4.1절 / 4.3절: `Stage 4` ➔ `Stage 3`
   - 4.3절: `Gate 1 재심사(GATE1_REVIEW.md 갱신 및 해시 재바인딩)` ➔ `Gate 1 재승인(GATE1_REVIEW.md 갱신)`
3. **`DISTRIBUTION_SPEC.md`**:
   - 제4장: `upgrade`(전역)와 `update`(로컬), `/update-forgeflow`의 역할 분리 기술.
4. **`PHILOSOPHY_AND_COMPASS.md`**:
   - 3.3절: `엄격한 사전 심사` ➔ `엄격한 명세 승인(Gate 1)`
5. **`REFACTORING_GUIDE.md`**:
   - 제4장 제목: `Stage 4 구현 및 자가 치유` ➔ `Stage 3 구현 및 자가 치유`
6. **`CHANGELOG.md`**:
   - v0.1.2 ~ v0.1.5 이력 추가 및 v0.1.6 항목 등록.

### B. 헌법 및 템플릿 그룹
1. **`.specify/memory/constitution.md`**:
   - 제3조: 루프 중 `git commit (새 SHA 발행)` 제거 및 구현 완료 시 원자적 커밋 생성으로 교정.
2. **`src/forgeflow/scaffold.py`**:
   - 내장 헌법 텍스트 제3조 동기화.
3. **`scripts/install-skills.sh`**:
   - 헌법 지침 제3조 동기화.
4. **`src/forgeflow/templates/GOVERNANCE.md`**:
   - 과거 버전 번호(v0.22/v0.21)를 v0.1.0 기준으로 교정.
5. **`README.md`**:
   - Gate 1 설명 중 `spec.md SHA-256 불변 바인딩` 및 `사전 심사` 삭제, 완료 시 커밋 생성으로 정정.

### C. 버전 갱신
- `src/forgeflow/_version.py`를 `0.1.6`으로 판올림.
