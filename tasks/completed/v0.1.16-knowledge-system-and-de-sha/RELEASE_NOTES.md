# Release Notes: v0.1.16

## 릴리즈 개요
`v0.1.16`은 AI 에이전트의 반복적인 아키텍처 망각과 과거 실수 재발을 방지하는 **2계층 지식 관리 체계(2-Tier Knowledge Architecture)**를 구축하고, 하네스 내부의 **취약한 Git SHA 커밋 범위 diff 검증을 완전히 제거(De-SHA)**하며, 개발 진입과 초고속 코드 탐색을 지원하는 **공식 ForgeFlow 스킬 제품군**을 탑재한 주요 릴리즈입니다.

## 주요 변경 사항

### 1. 2계층 지식 관리 체계 도입 (2-Tier Knowledge Architecture)
- **Tier 1 (Fast Recognition)**: `docs/spec/ANTI_PATTERNS.md` (500토큰 미만의 간결한 Never-Do / Always-Do 수칙)를 에이전트 부팅 시퀀스(Boot Sequence)에 필수 확인 항목으로 편입.
- **Tier 2 (Deep Dive)**: `docs/adr/` 디렉터리에 아키텍처 결정 레코드(ADR 001: Git SHA 및 커밋 범위 diff 결합 제거, ADR 002: spec body hash 바인딩 제거)를 영구 보존하여 온디맨드로 깊이 있는 의사결정 맥락 제공.
- **프로젝트 헌법 제6조 주입**: `.specify/memory/constitution.md`에 설계 안티패턴 및 ADR 준수 의무 명시.
- **범용 배포 스캐폴딩**: `forgeflow init --speckit`, `setup-forgeflow`, `update-forgeflow` 실행 시 다운스트림 리포지토리에 지식 체계 자동 구성.

### 2. 취약한 Git SHA 및 커밋 범위 diff 검증 완전 제거 (ADR 001)
- `src/forgeflow/harness.py`에서 `_candidate_disallowed_paths`, `_find_verified_completion_relocation_paths`, `_tree_files_at_commit` 등 취약한 diff 화이트리스트 로직을 완전히 걷어냄.
- 실용적인 안전 불변식(테스트 100% 통과 + Gate 승인 상태 + clean worktree + 패키지 완료 이동 + 패키지 매니페스트 SHA256)으로 신뢰성 확립.
- 무해한 문서 수정, 버전 범프, 패키지 이동 커밋으로 인한 거짓 경고(False Positive) 원천 해소.

### 3. 공식 ForgeFlow 스킬 제품군 탑재 (`scripts/install-skills.sh`)
- `/forgeflow`: 기획(spec)부터 릴리즈 밀봉(seal)까지 5단계 수명주기 전체를 안내·제어하는 마스터 오케스트레이터 스킬.
- `/forgeflow-graphify`: `kb-graphify` 패턴을 계승하여 대량 소스 코드 무차별 읽기를 방지하고 AST/의존성을 초고속 탐색하는 지식 지도 스킬.
- `/setup-forgeflow` & `/update-forgeflow`: 2계층 지식 관리 체계 자동 스캐폴딩 및 최신화 기능 확장.
