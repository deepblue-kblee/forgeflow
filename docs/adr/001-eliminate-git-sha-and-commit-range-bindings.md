# [ADR-001] Git 커밋/Blob SHA 바인딩 및 범위 감사 영구 폐기

- **상태 (Status)**: 승인됨 (Accepted)
- **결정 일자 (Date)**: 2026-10-27
- **결정자 (Deciders)**: User & Antigravity Autonomous Engineering Panel
- **관련 안티패턴 ID**: AP-01

---

## 1. 맥락 및 배경 (Context & Problem Statement)

과거 ForgeFlow는 게이트 승인 시점의 코드 불변성을 통제하기 위해 다음과 같은 Git SHA 기반의 엄격한 바인딩 메커니즘을 도입했습니다:
1. `QA-SHA`: Gate 2 통과 시점의 커밋 SHA를 `QA_SIGNOFF.md`에 고정.
2. `Candidate-SHA`: Gate 3 패키지 밀봉 시점의 커밋 SHA를 바인딩.
3. `_candidate_disallowed_paths`: `git diff QA-SHA..Candidate-SHA` 및 `Candidate-SHA..HEAD` 범위를 실행하여 허용되지 않은 파일 변경이 있는지 감사.

### 겪었던 반복적 실패와 인시던트
- **Issue #3**: Gate 2 통과 후 사소한 부기 작업(예: `tasks.md` 완료 체크, 릴리즈 노트 작성)으로 커밋이 생기자, 커밋 SHA가 달라졌다며 300개 테스트 재실행과 3인 패널 재심사를 강제하는 마찰 발생.
- **Issue #5**: 정상 완료 후 `tasks/in-progress/` ➔ `tasks/completed/`로 디렉터리를 이동하여 커밋했더니, post-candidate diff에서 삭제 및 추가로 잡혀 `release_candidate_range_invalid` 에러로 정상 릴리즈가 차단됨.
- **땜질의 악순환**: 문제 해결을 위해 `git ls-tree`로 Blob SHA를 대조하는 로직을 덧붙였으나, 이는 Git SHA 강박을 더욱 악화시키는 취약한 오버엔지니어링(Brittle Testing)이었음.

Git은 본질적으로 리베이스, 커밋 분할/합치기, 파일 이동, 커밋 메시지 수정이 가능한 유연한 버전 관리 시스템입니다. 거버넌스 승인 상태를 특정 Git 커밋 SHA와 1:1로 결속하려는 시도는 필연적으로 수많은 거짓 양성(False Positive)을 낳았습니다.

---

## 2. 결정 사항 (Decision)

ForgeFlow 거버넌스 제어 평면에서 **Git 커밋/Blob SHA 추적과 diff 범위 감사를 전면 영구 폐기**한다.

1. **폐기 대상**:
   - `_candidate_disallowed_paths`의 Git diff 범위 감사 로직 전면 삭제.
   - `_tree_files_at_commit` 및 `_find_verified_completion_relocation_paths` 삭제.
   - `release_candidate_range_invalid` 에러 폐지.
2. **대체 안전 불변식 (실용적 4대 불변식)**:
   - **불변식 1 (게이트 승인 증적)**: `GATE1_REVIEW.md`, `QA_SIGNOFF.md`, `RELEASE_SIGNOFF.md`에 유효한 APPROVED 판정이 마크다운에 영구 보존되어 있는가?
   - **불변식 2 (런타임 테스트 100% Pass)**: 하네스 감사 시점에 실제 전체 단위/통합 테스트가 100% 통과하는가? (코드가 몰래 바뀌었다면 테스트 러너가 물리적으로 감지)
   - **불변식 3 (작업 트리 무결성)**: 릴리즈 닫기/검사 시점에 `git status` 상에 커밋되지 않은 지저분한 파일(Dirty State)이 없는가?
   - **불변식 4 (패키지 보존)**: 릴리즈 필수 문서들이 `tasks/completed/`에 온전히 존재하는가?

---

## 3. 고려했던 대안들 (Considered Alternatives)

- **대안 1: Git Blob SHA 1:1 대조 엔진 (v0.1.15 임시 적용)**:
  - 기각 사유: Git 커밋 SHA의 취약성을 Git Blob SHA로 치환했을 뿐, 파일명 변경이나 Git의 내부 오브젝트 구조에 여전히 의존하여 새로운 마찰을 양산하는 전형적인 오버엔지니어링.
- **대안 2: 화이트리스트 계속 확장**:
  - 기각 사유: 예외 케이스(부기 문서, 세션 상태, 파일 이동 등)가 나올 때마다 하네스 코드를 영구적으로 땜질해야 하므로 유지보수 불가능.

---

## 4. 결과 및 영향 (Consequences)

- **긍정적 효과**:
  - 파일 이동, 체크리스트 체크, 리베이스 등 정상적인 Git 작업으로 인해 하네스 감사가 헛돌거나 차단되는 현상 100% 영구 소멸.
  - 하네스 제어 평면 코드 약 100줄 이상 슬림화 및 단순화.
  - 에이전트와 사용자의 불필요한 QA Rebind 반복 비용 제거.
- **트레이드오프 및 보완**:
  - 커밋 SHA를 엄격히 묶지 않는 대신, **"실제 테스트 러너의 100% 통과"**와 **"마크다운 게이트 서명 검증"**을 철저히 강화하여 런타임 품질을 빈틈없이 수호함.
