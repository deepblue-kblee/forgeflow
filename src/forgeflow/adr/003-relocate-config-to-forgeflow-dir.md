# [ADR-003] 프로젝트 거버넌스 설정 파일의 .forgeflow/config.json 일원화 및 update 마이그레이션

- **상태 (Status)**: 승인됨 (Accepted)
- **결정 일자 (Date)**: 2026-10-31
- **결정자 (Deciders)**: User & Antigravity Panel
- **관련 릴리즈 ID**: `v0.1.20-relocate-config-to-forgeflow-dir`

---

## 1. 맥락 및 배경 (Context & Problem Statement)

기존 ForgeFlow 셋업 시 프로젝트 루트에 `.forgeflow.json` 설정 파일과 `.forgeflow/` 진단/캐시 디렉터리가 동시에 생성되었다. 이로 인해 프로젝트 루트 디렉터리에 프레임워크 관련 파일이 분산되어 루트 구조가 복잡해지는 문제가 있었다.

또한 기존 프로젝트에서 `forgeflow update`를 수행할 때 기존 설정을 유실하지 않고 자연스럽게 새로운 표준 경로로 이전할 수 있는 안전한 마이그레이션 메커니즘이 필요했다.

---

## 2. 결정 사항 (Decision)

1. **설정 파일 표준 경로 이전 (Canonical Path)**:
   - 프로젝트 거버넌스 설정의 단일 표준 경로를 `<root>/.forgeflow/config.json`으로 확정한다.
   - 신규 스캐폴딩(`forgeflow setup`, `scaffold_speckit_hybrid`, `init_project_governance` 등) 시 `.forgeflow/config.json`을 기본 생성한다.

2. **`forgeflow update` 하위 버전 자동 마이그레이션 (Auto Migration)**:
   - 루트에 구버전 `.forgeflow.json`이 존재하는 프로젝트에서 `forgeflow update` 실행 시, 사용자 커스텀 설정을 100% 보존하면서 `.forgeflow/config.json`으로 자동 딥 머지한다.
   - 새 설정 파일 저장 완료 후 루트의 구버전 `.forgeflow.json`을 안전하게 언링크(unlink)하여 최신 레이아웃으로 일원화한다.

3. **투명한 하위 호환 폴백 (Graceful Fallback)**:
   - `scanner`, `runner`, `diagnostics`, `resolve_auto_create_branch` 등 모든 설정 조회 로직에서 `.forgeflow/config.json`을 최우선 탐색하고, 구버전 파일이 잔존하는 경우 `.forgeflow.json`을 안전하게 폴백 조회한다.

---

## 3. 고려했던 대안들 (Considered Alternatives)

- **대안 1: 루트 `.forgeflow.json` 유지**:
  - 기각 사유: 프로젝트 루트에 여러 개의 설정 파일/디렉터리가 난립하여 정돈성이 저하됨.
- **대안 2: 구버전 `.forgeflow.json` 수동 마이그레이션 안내만 제공**:
  - 기각 사유: 사용자가 수동으로 파일 이동 및 삭제를 수행해야 하는 마찰이 발생하므로, `forgeflow update` 명령 시 자동 마이그레이션으로 편의성과 안정성을 극대화함.

---

## 4. 결과 및 영향 (Consequences)

- **긍정적 효과 (Positive)**:
  - 프로젝트 루트가 정돈되고 `.forgeflow/` 디렉터리 내에 거버넌스 설정과 캐시가 일원화됨.
  - `forgeflow update` 한 번으로 하위 버전 프로젝트가 무중단으로 최신 구조로 자동 전환됨.
- **트레이드오프 및 보완 (Trade-offs)**:
  - 설정 파일 경로 변경에 따른 기존 도구 호환성 우려는 Graceful Fallback 조회 로직으로 완전히 해소함.
