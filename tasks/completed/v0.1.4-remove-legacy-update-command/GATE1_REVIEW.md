# Gate 1 Specification Sign-Off: Removal of Legacy Update Command & Obsolete Catalogs

- **Release ID**: `v0.1.4-remove-legacy-update-command`
- **Review Date**: 2026-10-21
- **Risk Tier**: **Tier 3 (Critical / Core CLI Cleanup / Amnesia Policy Enforcement)**
- **Target Specification**: [spec.md](spec.md)
- **Gate 1 Verdict**: **APPROVED**

---

## 1. 리스크 티어링 심사 (Risk Tiering Evaluation)

- **도메인**: CLI 최상위 공개 인터페이스, 레거시 모듈 삭제, 날짜 기반 폐기 규범 강제
- **판정 근거**: 공개 CLI 서브커맨드(`update`)를 삭제하고 복수의 모듈을 정리하는 작업이므로 **Tier 3 (Critical)**로 분류하고 3대 패널 심사를 수행한다.

---

## 2. 3대 패널 독립 심사 결과 (Independent Review Panel)

### 2.1 보안 관점 (Security Reviewer: PASS)
- **심사 의견**:
  1. 2026-10-20 이전 구버전의 복잡한 바이트 해시 오라클(`catalog_oracles`)과 트랜잭션 저널 검증 코드를 제거함으로써 잠재적 공격 표면과 불필요한 파일 접근을 줄인다.
  2. 잔재 제거로 코드베이스의 신뢰 경계가 v0.1.0+ 표준으로 명확해진다.
- **판정**: **PASS**

### 2.2 안정성 관점 (Reliability Reviewer: PASS)
- **심사 의견**:
  1. `update`와 `upgrade`의 혼선으로 인해 사용자가 엉뚱한 레거시 번들 프리뷰 명령을 실행하는 위험을 완전히 방지한다.
  2. 현재 코어 거버넌스(Spec Kit 하이브리드)는 `update.py`를 전혀 참조하지 않으므로 삭제 후에도 시스템 안정성에 부작용이 없다.
- **판정**: **PASS**

### 2.3 유지보수성 관점 (Maintainability Reviewer: PASS)
- **심사 의견**:
  1. 약 400여 줄의 불필요한 레거시 코드와 더미 오라클 파일들이 청산되어 프레임워크의 유지보수성이 크게 향상된다.
  2. Date-Based Amnesia Policy의 취지에 완벽히 부합한다.
- **판정**: **PASS**

---

## 3. 계획된 변경 범위 (Planned Scope of Changes)

- `src/forgeflow/cli.py`
- `src/forgeflow/update.py` (삭제)
- `src/forgeflow/bundle_catalog.py` (삭제)
- `src/forgeflow/catalog_oracles/` (삭제)
- `tests/test_update.py` (삭제)
- `tests/test_cli.py`
- `src/forgeflow/_version.py`

---

## 4. 최종 게이트 승인 서명 (Final Sign-Off)

- **Gate 1 Status**: **APPROVED**
- **Approved by**: AI Agent Panel (Antigravity) & User Explicit Instruction ("맞다면 CLI에서 과거의 유산은 모두 없애줘.")
- **Next Stage**: Stage 2 (기술 설계 `plan.md`) 및 Stage 3 (원자적 태스크 분해 `tasks.md`) 착수 허용
