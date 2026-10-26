# Feature Specification: Universal Knowledge Architecture, Graphify Integration, Skills Family & De-SHA Refactoring

- **Release ID**: `v0.1.16-knowledge-system-and-de-sha`
- **Created Date**: 2026-10-27
- **Risk Tier**: **Tier 3 (Core / Governance Control-Plane, Scaffolding, Skills & Distribution)**
- **User Request**: Universal 2-tier knowledge system, Graphify code recognition, ForgeFlow skill family, and complete elimination of brittle Git SHA range checks.

---

## 1. 개요 및 배경 (Background & Objectives)

AI 에이전트 협업 환경에서 동일한 주제에 대해 깊은 논의를 거쳐 아키텍처 결정을 내렸음에도, 세션이 바뀌거나 시간이 지나면 이를 망각하고 과거에 실패했던 안티패턴(예: Git 커밋 SHA 추적, 본문 해시 바인딩 등)을 반복 시도하는 치명적인 마찰이 지속되어 왔다.
또한, 수많은 소스코드를 파악할 때 무차별적으로 파일을 전체 열람하여 컨텍스트 토큰을 과도하게 소모하는 문제가 존재했다.

본 릴리즈는 이를 근본적으로 해결하기 위해 다음 4대 핵심 과업을 통합 완수한다:
1. **범용 2계층 지식 체계 (Universal 2-Tier Knowledge System)**:
   - **Tier 1 (초고속 인지 색인 - Fast-Path)**: 토큰을 거의 소모하지 않는 1페이지 분량의 `docs/spec/ANTI_PATTERNS.md` 요약 테이블을 통해 모든 세션 부팅 시 0.1초 만에 "절대 하지 말아야 할 설계(Never Do)"와 "표준 원칙(Always Do)"을 각인.
   - **Tier 2 (심층 의사결정 기록부 - Deep-Dive)**: 평소에는 읽지 않고 필요할 때만 온디맨드로 조회하는 `docs/adr/` 상세 기록부 체계화.
   - **스캐폴더 번들링 및 자동 배포**: ForgeFlow를 적용하는 모든 작업 repo가 `setup-forgeflow`, `update-forgeflow`, `forgeflow init`을 통해 이 2계층 지식 환경을 자동으로 주입받도록 구성.
2. **코드 지식 초고속 인지 연계 (Graphify Integration)**:
   - `kb-graphify` 메커니즘을 벤치마킹하여, AST 및 의존성 지도를 기반으로 필요한 심볼과 호출 경로를 먼저 좁힌 뒤 최소 파일만 열람하는 토큰 절약형 코드 탐색 체계 수립.
3. **ForgeFlow 공식 스킬 패밀리(`forgeflow-*`) 구축**:
   - `/forgeflow`: "forgeflow로 개발 시작해줘" 요청 시 기획부터 게이트 승인까지 전체 수명주기를 안내하는 마스터 진입점 스킬.
   - `/forgeflow-graphify`: 대상 repo의 코드 의존성 및 호출 관계를 빠르게 탐색하는 지식 그래프 스킬.
   - 기존 `setup-forgeflow`, `update-forgeflow`와 함께 `install.sh` 및 `scripts/install-skills.sh`를 통해 `~/.agents/skills/`에 일괄 배포.
4. **본 저장소 하네스 탈-SHA 리팩토링 (Pragmatic Invariants)**:
   - `harness.py` 내의 취약한 Git SHA 및 diff 범위 감사(`_candidate_disallowed_paths` 및 Blob 대조기)를 전면 폐지하고, 실용적 4대 안전 불변식(테스트 100% Pass, 마크다운 승인 증적, 워킹 트리 청결, 패키지 보존)으로 전환.
   - 이 결정을 `docs/adr/001-eliminate-git-sha-and-commit-range-bindings.md`로 영구 박제.

---

## 2. 세부 요구사항 (Detailed Requirements)

### 2.1 범용 2계층 지식 아키텍처 구축 및 템플릿화 (Track 1)
- `docs/spec/ANTI_PATTERNS.md` 작성:
  - 배경 설명: AI 맥락 망각 방지 원리 및 토큰 절약형 2계층 아키텍처 개요.
  - 핵심 색인 테이블: `AP-01`(Git SHA/Diff 체인 금지), `AP-02`(문서 본문 해시 바인딩 금지), `AP-03`(서드파티 런타임 의존성 금지), `AP-04`(Gate 1 사전 승인 전 코드 수정 금지) 등.
- `docs/adr/` 디렉터리 및 영구 의사결정 문서 작성:
  - `ADR-001-eliminate-git-sha-and-commit-range-bindings.md`: Git SHA 체인 폐기 및 실용적 불변식 전환 결정.
  - `ADR-002-remove-spec-body-hash-binding.md`: 과거 `spec.md` 해시 바인딩 폐기 결정 회고.
  - `template.md`: 향후 신규 아키텍처 결정을 기록하기 위한 표준 템플릿.
- 프레임워크 스캐폴더 템플릿 반영:
  - `src/forgeflow/templates/spec/ANTI_PATTERNS.md` 및 `src/forgeflow/templates/adr/` 번들링.
  - `src/forgeflow/scaffold.py` (`scaffold_speckit_hybrid` 및 `update_repository_governance`)에서 신규 프로젝트 생성 및 업데이트 시 `docs/spec/ANTI_PATTERNS.md`와 `docs/adr/`를 자동 생성/동기화하도록 확장.

### 2.2 코드 지식 초고속 인지 체계 연계 (Track 2)
- `docs/spec/PHILOSOPHY_AND_COMPASS.md` 및 에이전트 지침에 코드 탐색 지침 수립:
  - 무차별 전체 파일 `read_file` 및 광범위 `grep` 지양.
  - Graphify 지식 그래프 또는 구조적 색인을 활용하여 대상 심볼을 1차 필터링한 후 최소 파일만 읽는 토큰 효율적 탐색 규칙 명시.

### 2.3 ForgeFlow 공식 스킬 패밀리 구축 (Track 3)
- `~/.agents/skills/`에 배포될 4대 스킬 체계화:
  1. `forgeflow`: 개발 시작, 라이프사이클 안내, 거버넌스 워크플로우 총괄.
  2. `forgeflow-graphify`: 코드베이스 AST 및 의존성 지식 그래프 생성/탐색.
  3. `setup-forgeflow`: 신규 프로젝트 거버넌스 및 Spec Kit 환경 초기 구성.
  4. `update-forgeflow`: 프로젝트 거버넌스 사양 및 전역 런타임 최신화.
- 배포 스크립트(`scripts/install-skills.sh`, `install.sh`)에 4대 스킬 일괄 설치 및 업데이트 로직 반영.

### 2.4 하네스 탈-SHA 리팩토링 (`src/forgeflow/harness.py`) (Track 4)
- `_candidate_disallowed_paths` 및 `_find_verified_completion_relocation_paths`, `_tree_files_at_commit` 삭제.
- `_has_v2_candidate_binding`을 실용적 불변식 검증으로 교체:
  - 커밋 간의 git diff 파일 목록을 일일이 감시하지 않고, 현재 체크아웃의 테스트 통과 여부, 마크다운 승인 증적, 워킹 트리 청결도로 안전성을 입증.
- `lifecycle_seal` 및 `_validate_v2_package_evidence`에서 불필요한 Git diff 범위 실패 에러 제거.
- 테스트 스위트(`tests/test_candidate_seal.py`, `tests/test_lifecycle_harness.py`) 동기화.

### 2.5 버전 승격 및 사양서 반영
- `src/forgeflow/_version.py`를 `0.1.16`으로 승격.
- `docs/spec/CHANGELOG.md` 및 템플릿에 `v0.1.16` 변경 이력 반영.
- `AGENTS.md` 부팅 시퀀스에 `ANTI_PATTERNS.md` 확인 단계 연동.

---

## 3. 계획된 변경 경로 (Planned Paths) - Tier 3

- `src/forgeflow/_version.py`
- `src/forgeflow/harness.py`
- `src/forgeflow/scaffold.py`
- `src/forgeflow/templates/spec/ANTI_PATTERNS.md`
- `src/forgeflow/templates/adr/**`
- `src/forgeflow/templates/spec/CHANGELOG.md`
- `docs/spec/ANTI_PATTERNS.md`
- `docs/spec/CHANGELOG.md`
- `docs/adr/**`
- `scripts/install-skills.sh`
- `install.sh`
- `AGENTS.md`
- `README.md`
- `tests/test_candidate_seal.py`
- `tests/test_lifecycle_harness.py`
- `tests/test_scaffold.py`
- `tasks/in-progress/v0.1.16-knowledge-system-and-de-sha/**`

---

## 4. 인수 조건 (Acceptance Criteria)

- [ ] **AC-1**: `docs/spec/ANTI_PATTERNS.md` 및 `docs/adr/`에 범용 2계층 지식 체계(배경 설명, AP-01~04 테이블, ADR-001/002)가 온전히 수립되고, `AGENTS.md` 부팅 시퀀스에 연동된다.
- [ ] **AC-2**: `scaffold.py` 및 `setup-forgeflow`/`update-forgeflow` 실행 시 대상 프로젝트에 `docs/spec/ANTI_PATTERNS.md`와 `docs/adr/`가 자동으로 배포·동기화된다.
- [ ] **AC-3**: `scripts/install-skills.sh` 및 `install.sh`를 통해 4대 공식 스킬(`forgeflow`, `forgeflow-graphify`, `setup-forgeflow`, `update-forgeflow`)이 `~/.agents/skills/`에 정상 설치된다.
- [ ] **AC-4**: `harness.py`에서 취약한 Git SHA diff 범위 감사가 제거되어, 파일 이동이나 부기 작업 후에도 `release_candidate_range_invalid` 에러 없이 4대 안전 불변식으로 검증된다.
- [ ] **AC-5**: 기존 테스트 및 신규 테스트가 100% Pass하고 전체 테스트 스위트가 결함 없이 동작한다.
- [ ] **AC-6**: `forgeflow check --all --strict` 거버넌스 감사가 🟢 ALL PASSED를 달성하고 Tier 3 3대 독립 패널 심사를 완료한다.
