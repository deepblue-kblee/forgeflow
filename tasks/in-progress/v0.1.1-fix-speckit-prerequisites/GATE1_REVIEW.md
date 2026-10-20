# Gate 1 Pre-Implementation Review: Spec Kit Prerequisite Bundling

**Release ID**: `v0.1.1-fix-speckit-prerequisites`  
**Review Date**: 2026-10-20  
**Risk Tier**: **Tier 3 (Critical / Core / Governance Control-Plane)**  
**Target Specification**: [spec.md](spec.md)  
**Spec SHA256**: `4481e543b8d9e093d60ba5e6bd9d622cf1861c53f79d36b048e9cb24999d04d0`  
**Gate 1 Verdict**: **APPROVED**

---

## 1. 리스크 티어링 심사 (Risk Tiering Evaluation)

- **변경 도메인**: 거버넌스 제어 평면(Harness Control-Plane), 프로젝트 스캐폴딩 스키마, 외부 도구(Spec Kit) 실행 계약
- **판정 근거**: [AGENTS.md](file:///Users/deepblue/work/repo/forgeflow/AGENTS.md) 2조 및 [GATES_AND_LOOPS.md](file:///Users/deepblue/work/repo/forgeflow/docs/spec/GATES_AND_LOOPS.md) 2조에 따라 설정 스키마 및 거버넌스 제어 평면 수정은 규모와 무관하게 **Tier 3 (Critical)**에 해당함.
- **심사 절차**: 보안(Security), 안정성(Reliability), 유지보수성(Maintainability) 3대 독립 관점의 병렬 정밀 심사를 수행함.

---

## 2. 3대 패널 독립 심사 결과 (Independent Review Panel)

### 2.1 보안 관점 (Security Reviewer: PASS)
- **심사 의견**:
  1. 번들링되는 bash 스크립트(`check-prerequisites.sh`, `setup-plan.sh`, `setup-tasks.sh` 등)는 악의적 원격 스크립트 주입 없이 ForgeFlow 공식 패키지 리소스 내부에 안전하게 정적 파일로 포함되어 배포되어야 함.
  2. 스캐폴딩 경로 생성 시 `TemplateScaffolder`의 기존 심볼릭 링크 순회 방지(`_assert_safe_directory`, `_assert_no_symlink_creation_parent`) 가드를 100% 거쳐야 함.
  3. 스크립트 파일 실행 권한(`0o755`) 부여 시 소유자/그룹 권한을 최소화하여 로컬 권한 상승 위험이 없어야 함.
- **판정**: **PASS (조건부 보안 요구사항 충족 확인)**

### 2.2 안정성 관점 (Reliability Reviewer: PASS)
- **심사 의견**:
  1. 외부 서드파티 런타임 의존성 추가 없이 Python 3.10+ 표준 라이브러리(`importlib.resources`, `pathlib`, `shutil`)만으로 스캐폴딩이 완결되어야 함 (Zero-Dependency 원칙 준수).
  2. bash 스크립트 누락 시 Spec Kit 체인이 `exit 127`로 크래시되는 현상을 방지하기 위해, `forgeflow check` 및 `doctor`에 사전 감지 룰을 탑재하여 Fail-Closed로 결함을 즉시 보고할 수 있어야 함.
  3. 2026-10-20 이전 레거시 설정 제거 시 비가역적 파괴 방지를 위해 유효한 v0.1.0 표준 설정으로 원자적으로 대체되어야 함.
- **판정**: **PASS**

### 2.3 유지보수성 관점 (Maintainability Reviewer: PASS)
- **심사 의견**:
  1. 스펙 템플릿과 셸 스크립트의 버전 및 구조가 GitHub Spec Kit 공식 최신 규격과 정확히 일치하여야 함.
  2. `src/forgeflow/templates/speckit/` 하위에 일관되게 구조화하여 템플릿 탐색 복잡도를 낮추어야 함.
  3. `install.sh` 및 `scripts/install-skills.sh`가 항상 동일한 SSOT 스킬 명세를 배포하도록 일원화되어야 함.
- **판정**: **PASS**

---

## 3. 계획된 변경 경로 (Planned Scope of Changes)

- `src/forgeflow/templates/speckit/scripts/bash/*` (신규 번들 스크립트 6종)
- `src/forgeflow/templates/speckit/templates/*` (신규 번들 템플릿 4종)
- `src/forgeflow/scaffold.py` (`scaffold_speckit_hybrid`에 런타임 스크립트/템플릿 복사 및 권한 부여 추가)
- `src/forgeflow/diagnostics.py` (`doctor`에 Spec Kit 로컬 전제조건 검증 추가)
- `src/forgeflow/validator.py` (`check`에 하이브리드 검증 룰 추가)
- `tests/test_hybrid_scaffold.py` 및 관련 테스트 보강
- `scripts/install-skills.sh` (스킬 지침 동기화 유지)

---

## 4. 최종 게이트 승인 서명 (Final Sign-Off)

- **Gate 1 Status**: **APPROVED**
- **Next Stage**: Stage 3 (기술 설계 `/speckit.plan` ➔ `plan.md`) 및 Stage 4 격리 구현 착수 허용.
