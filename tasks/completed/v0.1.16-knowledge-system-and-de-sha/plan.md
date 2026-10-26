# Implementation Plan: Universal Knowledge Architecture, Graphify Integration, Skills Family & De-SHA Refactoring

- **Release ID**: `v0.1.16-knowledge-system-and-de-sha`
- **Created Date**: 2026-10-27
- **Risk Tier**: **Tier 3 (Core / Governance Control-Plane, Scaffolding, Skills & Distribution)**

---

## 1. 아키텍처 및 세부 설계 (Architecture & Design)

### 1.1 범용 2계층 지식 아키텍처 (Track 1)
- **`docs/spec/ANTI_PATTERNS.md` (Tier 1: Fast-Path)**:
  - 목적: 모든 AI 에이전트가 세션 부팅 시 0.1초 만에 인지하여 기폐기된 설계를 재시도하지 않도록 방지하는 요약 색인.
  - 구조:
    1. 원리와 배경: 왜 이 문서가 필요한가? (토큰 절약형 2계층 지식 구조 설명).
    2. 4대 영구 금지 패턴(Never-Do) vs 채택된 표준 원칙(Always-Do) 표.
    3. 상세 ADR 참조 링크.
- **`docs/adr/` (Tier 2: Deep-Dive)**:
  - `template.md`: 표준 ADR 작성 양식 (Title, Status, Context, Decision, Consequences).
  - `001-eliminate-git-sha-and-commit-range-bindings.md`: Git SHA 체인 폐기 사유와 실용적 4대 불변식으로의 전환 상세 기록.
  - `002-remove-spec-body-hash-binding.md`: 과거 `spec.md` 해시 바인딩 폐기 및 텍스트 유연성 확보 기록.
- **스캐폴더(`scaffold.py`) 및 번들 템플릿 연동**:
  - `src/forgeflow/templates/spec/ANTI_PATTERNS.md` 및 `src/forgeflow/templates/adr/*`에 템플릿 파일 추가.
  - `scaffold_speckit_hybrid` 및 `update_repository_governance`에서 프로젝트 루트의 `docs/spec/ANTI_PATTERNS.md`와 `docs/adr/` 디렉터리를 자동 생성 및 갱신하도록 구현.

### 1.2 코드 지식 초고속 인지 체계 연계 (Track 2)
- `kb-graphify` 메커니즘을 벤치마킹하여 에이전트 지침 및 사양서에 코드 탐색 최적화 패턴 통합.
- 무차별 전체 파일 열람을 지양하고, 심볼 의존성 및 호출 관계를 먼저 파악한 뒤 최소한의 코드만 읽도록 안내.

### 1.3 ForgeFlow 공식 스킬 패밀리(`forgeflow-*`) 구축 (Track 3)
- `scripts/install-skills.sh`에 4대 스킬 번들링:
  1. `~/.agents/skills/forgeflow/SKILL.md`:
     - 트리거: `/forgeflow`, `forgeflow로 개발`, `forgeflow 시작`
     - 역할: ForgeFlow 하이브리드 파이프라인(Stage 1~3, Gate 1~3) 안내 및 착수 지원.
  2. `~/.agents/skills/forgeflow-graphify/SKILL.md`:
     - 트리거: `/forgeflow-graphify`, `forgeflow:graphify`, `코드 의존성 탐색`
     - 역할: 코드베이스 AST 지식 그래프를 활용한 모듈 간 의존성 및 호출 경로 초고속 탐색.
  3. `~/.agents/skills/setup-forgeflow/SKILL.md`:
     - 신규 프로젝트에 거버넌스, Spec Kit, 2계층 지식 환경 원스톱 구성.
  4. `~/.agents/skills/update-forgeflow/SKILL.md`:
     - 프로젝트 거버넌스 사양 및 지식 환경 최신화.
- `install.sh` 연동: `install.sh` 실행 시 위 4개 스킬이 `~/.agents/skills/`에 일괄 배포되도록 갱신.

### 1.4 하네스 탈-SHA 리팩토링 (Track 4)
- `src/forgeflow/harness.py`:
  - `_candidate_disallowed_paths` 제거.
  - `_tree_files_at_commit` 및 `_find_verified_completion_relocation_paths` 제거.
  - `_has_v2_candidate_binding` 단순화:
    - 커밋 간 git diff 경로를 일일이 추적하지 않고, 후보 커밋이 로컬 커밋인지 기본 검증하거나 실용적 불변식(테스트 통과, 게이트 문서 존재)을 충족하면 `True`를 반환하도록 간소화.
  - `lifecycle_seal`: `_candidate_disallowed_paths` 검사 제거 및 `release_candidate_range_invalid` 에러 발생 차단.
- `tests/test_candidate_seal.py` 및 `tests/test_lifecycle_harness.py`:
  - 탈-SHA 사양에 맞게 테스트 케이스 업데이트 및 4대 실용적 불변식 검증 테스트 보강.

### 1.5 버전 승격 및 사양서 동기화
- `src/forgeflow/_version.py`: `__version__ = "0.1.16"`
- `docs/spec/CHANGELOG.md` & `src/forgeflow/templates/spec/CHANGELOG.md`: `v0.1.16` 반영
- `AGENTS.md` 및 `README.md`: 부팅 시퀀스에 `ANTI_PATTERNS.md` 확인 추가 및 신규 스킬 안내

---

## 2. 변경 대상 파일 목록 (Target Files)
1. `docs/spec/ANTI_PATTERNS.md`: 범용 안티패턴 요약 색인
2. `docs/adr/template.md`: ADR 작성 템플릿
3. `docs/adr/001-eliminate-git-sha-and-commit-range-bindings.md`: 탈-SHA ADR
4. `docs/adr/002-remove-spec-body-hash-binding.md`: Spec 해시 제거 ADR
5. `src/forgeflow/templates/spec/ANTI_PATTERNS.md`: 번들 템플릿
6. `src/forgeflow/templates/adr/*`: 번들 ADR 템플릿
7. `src/forgeflow/scaffold.py`: 스캐폴더에 2계층 지식 환경 생성 로직 추가
8. `src/forgeflow/harness.py`: 탈-SHA 리팩토링
9. `scripts/install-skills.sh`: 4대 공식 스킬 생성 및 설치
10. `install.sh`: 4대 스킬 배포 연계
11. `src/forgeflow/_version.py`: 버전 0.1.16 판올림
12. `docs/spec/CHANGELOG.md` & `src/forgeflow/templates/spec/CHANGELOG.md`
13. `AGENTS.md` & `README.md`: 지침 및 문서 동기화
14. `tests/test_candidate_seal.py`, `tests/test_lifecycle_harness.py`, `tests/test_scaffold.py`
15. `tasks/in-progress/v0.1.16-knowledge-system-and-de-sha/**`

---

## 3. 검증 전략 (Verification Strategy)
- 게이트키퍼 검증: `forgeflow check --stage 2`
- 단위 테스트: `python3 -m unittest discover -s tests -p "test_*.py"`
- 하네스 거버넌스 감사: `forgeflow check --all --strict`
- 스킬 설치 검증: `scripts/install-skills.sh` 실행 및 `~/.agents/skills/` 확인
- Gate 2/3 승인 및 릴리즈 밀봉
