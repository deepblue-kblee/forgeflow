# 📋 ForgeFlow 변경 이력 (CHANGELOG.md)

ForgeFlow 프레임워크의 모든 주요 변경 사항은 이 문서에 기록됩니다. 본 문서는 [Keep a Changelog](https://keepachangelog.com/ko/1.0.0/) 원칙과 [유의적 버전(Semantic Versioning)](https://semver.org/lang/ko/)을 준수합니다.

> [!NOTE]
> 본 퍼블릭 저장소로 전환되기 이전의 초기 연구 및 프로토타입 개발 이력(v0.1.0 ~ v0.22.1)은 비공개 아카이브 저장소(`deepblue-kblee/forgeflow-old`)에 영구 보존되어 있습니다.

---

## [0.1.19] - 2026-10-31

### 🌿 브랜치 자동 분기 On/Off 거버넌스 설정 지원 (Support auto_create_branch Configuration)

### Added
- **격리 브랜치 자동 생성 제어 옵션 (`governance.auto_create_branch`)**:
  - `.forgeflow.json`의 `governance.auto_create_branch` 불리언 옵션 추가 (미지정 시 기본값 `false`).
  - `auto_create_branch: false`인 경우 Stage 3 격리 구현 시 별도 브랜치(`feat/<release-id>`) 생성을 건너뛰고 현재 브랜치/worktree에서 직접 진행하여, 타 AI 도구(Claude Code, OpenCode)나 개발자가 사전에 설정한 worktree 환경과의 브랜치 중복 및 충돌 방지.
  - CLI 명령(`release create`, `task create`)에 `--create-branch` (별칭 `--branch`) 플래그를 제공하여 설정이 `false`이더라도 사용자의 명시적 요청 시 브랜치를 분기하여 전환할 수 있도록 지원.
  - 향후 브랜치 생성 정책을 변경할 때 `AGENTS.md` 같은 지침 문서를 오염시키지 않고 `.forgeflow.json`의 본 설정을 단일 진실 공급원(SSOT)으로 삼도록 사양 확립.
- **엄격한 불리언 타입 검증 및 진단 엔진 연동**:
  - `resolve_auto_create_branch` 함수를 통해 비불리언(문자열, 숫자 등) 설정 값을 `ValueError`로 fail-closed 차단.
  - `forgeflow doctor`(`SystemDiagnostics`)에서 유효하지 않은 `auto_create_branch` 값을 `INVALID_AUTO_CREATE_BRANCH` 이상 징후로 검출.
- **안전한 라이프사이클 종료 가드**:
  - `forgeflow lifecycle close` 실행 시 별도 브랜치를 생성하지 않은 경우에도 안전하게 Fast-Path로 릴리즈를 종료하도록 보장.

---

## [0.1.18] - 2026-10-27

### ⏱️ 프로젝트별 회귀 테스트 타임아웃 오버라이드 지원 (Support Project-Level Regression Test Timeout)

### Added
- **프로젝트별 테스트 타임아웃 설정 (`governance.test_timeout_seconds`)**:
  - `RuntimeTestRunner.resolve_test_timeout` 메서드를 도입하여 `.forgeflow.json`의 `governance.test_timeout_seconds`를 통해 프로젝트별 테스트 타임아웃을 유연하게 오버라이드할 수 있도록 지원 (Issue #6).
  - 설정 누락 시 기존의 60.0초 기본 동작을 안전하게 유지.
  - 불리언(`bool`), 비숫자(`str`), 비유한수(`inf`, `nan`), 0 이하(`val <= 0`)의 잘못된 값이 지정되면 암묵적 폴백 없이 명확한 `ValueError`로 엄격 차단(Fail-Closed).
- **진단 엔진(`SystemDiagnostics`) 설정 검증 연동**:
  - `forgeflow doctor` 실행 시 `.forgeflow.json`의 `test_timeout_seconds`가 비정상 형식인 경우 `INVALID_TEST_TIMEOUT` 경고 이상 징후로 즉시 검출 및 조치 가이드 제공.

---

## [0.1.17] - 2026-10-27

### 🔒 forgeflow update 시 작업 repo의 사용자 커스텀 설정 보존 및 불필요한 덮어쓰기 방지 (Preserve Custom Configuration on Update)

### Fixed
- **작업 리포지토리 `.forgeflow.json` 커스텀 설정 100% 보존**:
  - `TemplateScaffolder.deep_merge_config` 엔진을 도입하여, 작업 리포지토리에서 사용자가 수정한 거버넌스 설정(`strict_mode`, `max_loop_budget`, 커스텀 `tasks_dir`) 및 최상위 커스텀 메타데이터/플러그인 설정이 `forgeflow update` 실행 시 기본 템플릿 값으로 덮어써지지 않고 원형 그대로 보존되도록 개선.
  - 최신 프레임워크 규격의 누락된 기본 설정 키만 안전하게 재귀적으로 보강(Deep Merge with User Precedence).
- **무변경 시 불필요한 파일 덮어쓰기 방지 (Idempotent No-Op)**:
  - 이미 최신 버전이며 내용에 변경이 없는 경우 `.forgeflow.json`을 다시 쓰지 않고 `updated_files` 목록에서도 제외하여 불필요한 mtime 갱신 및 Git 변경 감지 방지.
- **`scaffold_speckit_hybrid` 이중 쓰기 및 커스텀 키 유실 방지**:
  - `update_repo_governance` 실행 중 `scaffold_speckit_hybrid`가 `.forgeflow.json`을 중간에 덮어쓰지 않도록 `skip_config=True` 경로 분리 및 단독 강제 스캐폴드(`force=True`) 시에도 사용자 커스텀 키 보존.

---

## [0.1.16] - 2026-10-27

### 🧠 2계층 지식 관리 체계 구축 및 Git SHA diff 결합 제거 (2-Tier Knowledge Architecture & De-SHA)

### Added
- **2계층 지식 관리 체계 (2-Tier Knowledge System)**:
  - **Tier 1 (Fast Recognition)**: `docs/spec/ANTI_PATTERNS.md` (500토큰 미만의 간결한 Never-Do / Always-Do 수칙)를 도입하여 AI 에이전트의 부팅 시퀀스에서 아키텍처 금기 사항을 즉각 인지.
  - **Tier 2 (Deep Dive)**: `docs/adr/` 아키텍처 결정 레코드(ADR 001: Git SHA 및 커밋 범위 diff 결합 제거, ADR 002: spec body hash 바인딩 제거)를 영구 문서화하여 심층 컨텍스트 필요 시에만 선택적 참조.
  - **거버넌스 헌법 제6조 주입**: `.specify/memory/constitution.md`에 설계 안티패턴 및 ADR 필수 준수 조항 추가.
- **공식 ForgeFlow 스킬 제품군 탑재 (`scripts/install-skills.sh`)**:
  - `/forgeflow`: 기획(spec)부터 릴리즈 밀봉(seal)까지 전 과정을 제어하는 마스터 오케스트레이터 스킬.
  - `/forgeflow-graphify`: `kb-graphify` 패턴을 계승하여 대량 소스 코드 무차별 읽기를 방지하고 AST/의존성을 초고속 탐색하는 지식 지도 스킬.
  - `/setup-forgeflow` & `/update-forgeflow`: 2계층 지식 관리 체계 자동 스캐폴딩 및 최신화 기능 확장.

### Removed
- **취약한 Git SHA 커밋 범위 diff 검증 완전 제거 (ADR 001)**:
  - `harness.py`의 `_candidate_disallowed_paths`, `_find_verified_completion_relocation_paths`, `_tree_files_at_commit` 등 취약한 Git commit diff range 화이트리스트 로직을 완전히 걷어내고, 실용적인 안전 불변식(테스트 100% 통과 + Gate 승인 상태 + clean worktree + 패키지 완료 이동 + 패키지 매니페스트 SHA256)으로 간소화.
  - 사소한 문서 수정, 버전 범프, 패키지 이동 커밋으로 인해 발생하던 릴리즈 후보 거부 오탐 원천 해소.

---

## [0.1.15] - 2026-10-26

### 🛡️ 릴리즈 완료 패키지 이동 사후 감사 오탐 해소 (Allow Committed Completion Relocation in Lifecycle Audit)

### Fixed
- **`forgeflow check --lifecycle` 사후 후보 감사 결함 수정 (Issue #5)**:
  - 릴리즈 밀봉(`lifecycle seal`) 및 완료(`lifecycle complete`) 후 `tasks/in-progress/<id>`에서 `tasks/completed/<id>`로 원자적 이동된 패키지가 커밋되었을 때, 바이트가 100% 동일함에도 `release_candidate_range_invalid`로 잘못 거부되던 오탐 결함 해소.
  - Git Blob SHA 대조 기반의 `_find_verified_completion_relocation_paths` 엔진을 도입하여, 패키지 파일의 추가·삭제·변조 없이 바이트 단위로 동일하게 이동되었음을 증명하고 사후 감사 화이트리스트에 안전하게 편입.
  - 런타임 코드, 테스트, 스크립트 수정 및 패키지 내용 1바이트 변조, 무인가 파일 추가, 원본 파일 잔류, 타 릴리즈 이동 등에 대한 엄격한 fail-closed 차단 유지.
  - `lifecycle complete`의 태스크 루트 탐색 시 사용자 정의 tasks 디렉터리(`configured`) 호환성 보강.

---

## [0.1.14] - 2026-10-24

### 📋 forgeflow update 시 CHANGELOG 요약 한 줄 출력 개선 (Changelog Summary Simplification)

### Changed
- **`forgeflow update`의 `changelog_summary` 출력 간결화**:
  - `CHANGELOG.md` 전문 대신 버전 헤더(`[<version>] - <date>`)와 대표 타이틀 1줄(`- <title>`)만 출력하도록 간소화하여 터미널 가독성 대폭 향상.
  - 다중 버전 판올림 시 버전별 1줄 요약 블록을 순차 출력하고, 전체 변경 이력은 기존과 동일하게 `forgeflow doc show changelog`로 안내.
  - 마크다운 섹션 1줄 요약 파서 `summarize_changelog_section` 엔진 탑재 및 `extract_changelog_range(..., summary=True)` 기본값 연동.

---

## [0.1.13] - 2026-10-24

### 📢 CHANGELOG 배포 연동 및 upgrade/update 변경 내역 자동 프리뷰 (Changelog Preview & Distribution)

### Added
- **`forgeflow update` 실행 시 거버넌스 사양 변경 내역(What's Changed) 자동 출력**:
  - `previous_version`에서 `current_version`으로 판올림되면서 도입된 주요 거버넌스 규범 변경 사항을 번들된 `CHANGELOG.md`에서 파싱하여 터미널에 요약 출력.
  - `--json` 모드 응답 객체에 `changelog_summary` 필드를 함께 제공하여, AI 에이전트가 새 거버넌스 규칙을 프롬프트 컨텍스트로 즉각 흡수하도록 지원.
  - 전체 변경 이력 열람 안내(`💡 전체 세부 사양서 열람: 'forgeflow doc show changelog'`) 제공.
- **`forgeflow upgrade` 완료 시 최신 릴리즈 하이라이트 출력**:
  - 전역 런타임 업그레이드 완료 성공 메시지 하단에, 방금 설치된 신규 버전의 주요 변경점(Highlights: Added, Changed, Fixed)을 터미널에 자동 프리뷰 출력.
  - `--json` 모드 응답 객체에 `release_highlights` 필드 포함.
- **CHANGELOG 마크다운 추출 엔진 탑재 (`src/forgeflow/scaffold.py`)**:
  - `extract_changelog_section(version)` 및 `extract_changelog_range(prev_ver, curr_ver)` 헬퍼 구현.

---

## [0.1.12] - 2026-10-24

### ⏳ Date-Based Amnesia 검증 완비 및 Gate 3 최종 단일 바인딩 확립 (Date-Based Amnesia & Gate 3 Single-Binding)

### Added & Improved
- **Date-Based Amnesia (2026-10-20 기준일) 정밀 판별 로직 탑재**:
  - `diagnostics.py`에 파일 수정 시각(`mtime`), 기준일(`2026-10-20`), 및 Spec Kit 하이브리드 표준 자산(`.specify/memory/constitution.md`) 존재 여부를 교차 검증하는 로직 구현.
  - 과거 2026-10-20 이전의 구버전 ForgeFlow(v0.4.4 ~ v0.23.0) 환경을 확실히 레거시로 감지하면서, 미래에 정당하게 판올림될 최신 버전(`0.22.0+`)과의 버전 번호 충돌 및 오탐을 원천 해소.
- **Gate 3 최종 단일 릴리즈 바인딩 및 사양 간소화**:
  - Gate 2는 테스트 100% Pass 및 정적 분석 통과에 대한 기술적 품질 합격 체크포인트로 작동.
  - Gate 2 이후의 패키지 부기(Bookkeeping: `tasks.md` 완료 체크, `RELEASE_NOTES.md`, `RELEASE_SIGNOFF.md` 작성)는 중간 QA-SHA 마찰 없이 자유롭게 수행되도록 허용.
  - 사용자 최종 Go/No-Go 승인을 거쳐 Gate 3 패키지 밀봉 시점에 최종 커밋 스냅샷을 단일 Release-SHA로 묶어 영구 보존.

---

## [0.1.11] - 2026-10-24

### 🩺 진단 엔진 오탐 제거 및 패키지 전용 변경 QA 재바인딩 방지 (Doctor Fix & Package-Only QA Preservation)

### Fixed
- **`forgeflow doctor` LEGACY_CONFIG_DETECTED 오탐 제거 (Issue #4)**:
  - `diagnostics.py`의 `forgeflow_version != "0.1.0"` 하드코딩 검사를 버전 튜플 비교(`parse_version_tuple(v) < (0, 1, 0)`)로 교정하여, `0.1.1` 이상의 최신 버전으로 정상 갱신된 환경에서 레거시 경고가 발생하는 오탐 결함 해소.

### Added & Improved
- **하네스 게이트 패키지 문서 화이트리스트 확장 (Issue #3)**:
  - `harness.py`의 `_candidate_disallowed_paths`에 최신 Spec Kit 하이브리드 표준 문서(`spec.md`, `plan.md`, `tasks.md`, `GATE1_REVIEW.md`, `CHANGE_NOTE.md`, `checklist.md`, `status.md`)를 전수 반영.
  - 패키지 디렉토리(`tasks/...`) 내의 문서 변경 및 릴리즈 노트 작성이 QA-SHA 바인딩을 깨뜨리지 않고 안전하게 보존되도록 개선.
- **릴리즈 ID 조기 검증 (Preflight Validation)**:
  - `forgeflow check --stage 2` 시점에 `validate_release_id`를 선제 검증하여 유효하지 않은 릴리즈 ID 형식을 조기 차단, 사후 패키지 경로 변경 마찰을 원천 예방.
- **거버넌스 승인 권한 경계 명문화**:
  - `FLOW_SPEC.md` 및 `GATES_AND_LOOPS.md`에 Gate 2(테스트 통과 및 하네스 감사에 따른 기술적 QA 자동 보증)와 Gate 3(사용자 최종 배포 패키지 Go/No-Go 인간 승인)의 역할 책임을 단일 진실 공급원(SSOT)으로 분리 명시.

---

## [0.1.10] - 2026-10-22

### 🛡️ `forgeflow upgrade` CDN 캐시 우회, 역전 감지 및 실설치 버전 검증 (Cache Busting, Inversion Guard & Verification)

### Added
- **Cache-Busting 헤더 및 쿼리 파라미터**:
  - `raw.githubusercontent.com` 요청 시 Fastly/Varnish CDN 300초 강제 캐시를 우회하기 위해 `Cache-Control: no-cache, no-store, must-revalidate` 및 `Pragma: no-cache` 헤더 부여.
  - 버전 확인(`_version.py`) 및 인스톨러(`install.sh`) URL에 타임스탬프 쿼리(`?t={int(time.time())}`) 추가.
- **원격 버전 역전 감지 (Inverted Version Guard)**:
  - 원격 버전이 현재 로컬 버전보다 낮게 조회될 경우(`remote_tuple < current_tuple`), CDN 캐시 갱신 지연 가능성을 안내하는 경고 문구(`⚠️ Warning: ... CDN cache may still be updating.`) 출력 및 JSON 모드 payload warning 필드 제공.
- **설치 완료 후 실설치 버전 재검증**:
  - `install.sh` 실행 성공 후, 사전에 파싱했던 원격 변수 대신 실제 로컬에 설치/활성화된 패키지 버전을 확인하여 정확한 업그레이드 완료 메시지(`🎉 Successfully upgraded ForgeFlow to v{installed_version}!`) 출력.

---

## [0.1.9] - 2026-10-21

### 💬 `forgeflow upgrade` 대화형 확인 프롬프트 및 `--force` 옵션 도입 (Interactive Upgrade Prompt & Force Option)

### Added
- **버전 비교 사전 안내**:
  - `forgeflow upgrade` 실행 시, 업그레이드 전 현재 로컬 버전과 원격 최신 버전을 터미널에 비교 출력.
- **대화형 승인 프롬프트 (`y/n`)**:
  - 업그레이드 대상이 발견되었을 때 `Do you want to upgrade to v{remote_version}? [y/N]: ` 프롬프트를 통해 사용자 동의를 수렴. `y` 입력 시에만 설치를 진행하고 그 외에는 취소.
- **`--force` 바이패스 플래그**:
  - `--force` 지정 시 대화형 프롬프트를 건너뛰고 즉시 업그레이드/재설치를 수행하도록 지원.

---

## [0.1.8] - 2026-10-21

### ⚓ 부팅 앵커 기존 주석 삭제 및 파일 맨 마지막 추가 개선 (Append Boot Anchor to End)

### Changed
- **부팅 앵커 주입 위치 개선**:
  - `AGENTS.md` / `CLAUDE.md` 등에 ForgeFlow 부팅 앵커 주입 시, 기존 상단/중간에 위치하던 주석 마커 블록을 완전히 삭제하고 문서 맨 마지막(하단)으로 이동하여 안전하게 추가하도록 개선 (`bind_boot_anchor`).
  - 프로젝트 고유 타이틀 및 본문 컨텍스트를 최상위에 온전히 보존.
  - 정규식 기반 클린징을 통해 멱등성 및 원본 텍스트 100% 보존 보장.
- **테스트 스위트 강화**:
  - 상단/중간 위치 기존 주석 삭제 및 파일 끝 이동 검증 단위 테스트 추가 (`tests/test_boot_anchor.py`).

---

## [0.1.7] - 2026-10-21

### 🧹 레거시 템플릿 정화 및 사양서 발견성 강화 (Purge Legacy Templates & Spec Discovery)

### Added
- **`forgeflow doc` (호환 별칭 `spec`) CLI**:
  - 터미널에서 프레임워크 7대 공식 사양서를 손쉽게 열람할 수 있는 목록 조회(`doc list`) 및 개별 사양 출력(`doc show <spec>`) 명령어 제공.
- **비파괴적 세션 진입점 앵커 주입 (`bind_boot_anchor`)**:
  - 고유 마커를 통해 `AGENTS.md` / `CLAUDE.md`의 기존 사용자 고유 지침을 100% 보존하면서 부팅 시퀀스 앵커를 인플레이스 주입 및 해제 지원.

### Removed
- **레거시 템플릿 5종 영구 삭제**:
  - `src/forgeflow/templates/` 최상위에서 2026-10-20 이전 산출물(`PRD.md`, `DESIGN.md`, `ROADMAP.md`, `GOVERNANCE.md`, `RELEASE_NOTES.md`)을 완전히 삭제.

---

## [0.1.6] - 2026-10-21

### 🧹 과거 유산 및 규격 불일치 전수 청산 (Comprehensive Legacy Cleanup)

### Changed
- **원자적 루프 정의 현대화**:
  - 자가 치유(Loop 2) 루프마다 `git commit (새 SHA 발행)`을 강제하던 조항을 제거하고, 루프 중에는 로컬 수정-테스트를 반복하며 모든 테스트가 100% 통과된 최종 시점에 단일 원자적 커밋 1개를 생성하도록 단일화.
- **Spec SHA-256 해시 바인딩 잔재 완전 제거**:
  - `FLOW_SPEC.md` 스키마 및 `GATES_AND_LOOPS.md`, `README.md`에 남아있던 해시 바인딩 및 해시 재바인딩 설명 영구 삭제.
- **거버넌스 용어 및 Stage 표기 단일화**:
  - 모호한 '사전 심사' 표현을 'Gate 1: 명세 승인 (Spec Sign-Off)'으로 완전 통일.
  - 하이브리드 워크플로우에 맞추어 구현 단계를 'Stage 3'으로 일치화.
- **배포 사양 및 과거 버전 표기 교정**:
  - `DISTRIBUTION_SPEC.md`에 `upgrade`(전역)와 `update`(로컬), `/update-forgeflow`(스마트 파사드)의 명확한 역할 분리 반영.
  - 과거 버전 번호(v0.22/v0.23 등)를 v0.1.x 표준으로 교정.

---

## [0.1.5] - 2026-10-21

### 🔄 `forgeflow update` 명령어 정식 도입 및 스마트 파사드 간결화

### Added
- **`forgeflow update` CLI 서브커맨드**:
  - 로컬 리포지토리의 거버넌스 사양(`.forgeflow.json`, `.specify/scripts/bash/`, 템플릿, 헌법, 훅)을 최신 버전으로 갱신하는 단독 명령어 구현.
  - `tasks/in-progress/` 및 `tasks/completed/`의 모든 작업 데이터 100% 보존.
- **스마트 파사드 `/update-forgeflow` 간결화**:
  - 내부 파일 복사 지침 대신 전역 `forgeflow upgrade` ➔ 로컬 `forgeflow update`를 순차 호출하도록 DRY 원칙 기반 캡슐화 완성.

---

## [0.1.4] - 2026-10-21

### 🗑️ 레거시 `update` 및 구버전 카탈로그 완전 폐기

### Removed
- **과거 유산 삭제**:
  - 2026-10-20 이전 v0.4.4~v0.22.0 시절의 구시대 정적 바이트 카탈로그(`bundle_catalog.py`, `catalog_oracles/`) 및 관련 모듈(`update.py`) 영구 삭제.

---

## [0.1.3] - 2026-10-21

### ⚡ `forgeflow upgrade` CLI 및 전역 런타임 최신화

### Added
- **`forgeflow upgrade` 서브커맨드**:
  - `--check` 무설치 버전 검사, Idempotency 보장, 원격 `install.sh` 자동 다운로드 및 전역 런타임/스킬 일괄 승격 지원.

---

## [0.1.2] - 2026-10-21

### 🎯 Gate/Stage 분리 및 `spec.md` 해시 바인딩 제거

### Changed
- **`spec.md` 해시 바인딩(Spec SHA256) 완전 제거**: 사소한 텍스트/포맷 편집에도 해시가 깨져 Loop 3 무한 루프로 헛돌던 마찰 요인 원천 해소 (`cli.py`, `validator.py`, `scaffold.py`).
- **Stage와 Gate 개념 완전 분리**: 작업 단계(Stage 1~3)와 승인 관문(Gate 1~3: Spec Sign-Off, QA Sign-Off, Release Sign-Off)의 위치, 주체, 승인 방법을 명확히 단일 진실 공급원(SSOT)으로 정비.

---

## [0.1.1] - 2026-10-20

### 🚀 Spec Kit 런타임 자산 번들링 및 Date-Based Amnesia 적용

### Fixed
- **Spec Kit 필수 런타임 bash 스크립트 번들링 (Exit 127 블로커 해결)**:
  - `check-prerequisites.sh`, `common.sh`, `create-new-feature.sh`, `resolve-template.sh`, `setup-plan.sh`, `setup-tasks.sh` 등 6개 핵심 bash 스크립트를 번들링하여 스캐폴딩 시 자동 생성 및 `0o755` 실행 권한 부여.
  - `spec-template.md`, `plan-template.md`, `tasks-template.md`, `checklist-template.md` 템플릿 번들링.
- **거버넌스 엔진 하이브리드 산출물 정식 인식**:
  - `validator.py` 및 `harness.py`에서 하이브리드 산출물(`spec.md`, `GATE1_REVIEW.md`, `plan.md`, `tasks.md`, `QA_SIGNOFF.md`, `RELEASE_SIGNOFF.md`)을 정식 거버넌스 문서로 인식하도록 개정.
- **날짜 기반 과거 레거시 강제 폐기 (Date-Based Amnesia Policy)**:
  - 2026-10-20 이전 생성된 구버전 설정 감지 시 하위 호환 마이그레이션을 거부하고 v0.1.0/v0.1.1 표준으로 강제 재정립.
- **진단 및 헬스체크 (`forgeflow doctor`) 고도화**:
  - Spec Kit 로컬 bash 스크립트 누락 및 실행 권한 누락 감지 룰 추가.

---

## [0.1.0] - 2026-10-20

### 🌟 하이브리드 아키텍처 공식 첫 공개 릴리즈 (Initial Public Release)

GitHub Spec Kit의 대화형 명세 개발(Spec-Driven Development) 실행력과 ForgeFlow의 엔터프라이즈 하네스 거버넌스(Harness Governance) 통제력을 유기적으로 결합한 하이브리드 AI 에이전트 거버넌스 프레임워크의 첫 공식 릴리즈입니다.

### Added
- **이중 엔진 하이브리드 아키텍처 (Dual-Engine Architecture)**:
  - 실행 엔진(Worker): GitHub Spec Kit을 통한 요구사항 명세(`spec.md`), 아키텍처 계획(`plan.md`), 원자적 태스크 분해(`tasks.md`) 및 TDD 순차 구현 주도.
  - 거버넌스 엔진(Supervisor): ForgeFlow를 통한 게이트 통과 심사(Gate 1/2/3), 증적 결속 및 물리적 코드 작성 사전 차단.
- **Fail-Closed 게이트키퍼 CLI (`forgeflow check --stage 2`)**:
  - Spec Kit의 `before_implement` 훅에 바인딩되어 사전 심사 증적(`GATE1_REVIEW.md`) 누락 또는 `spec.md` 해시 변조 시 코드 작성을 물리적으로 차단(`exit 1`).
- **원클릭 계정 로컬 설치 체계 (`install.sh`)**:
  - 시스템 전역(`/opt`, `/usr/local/bin`) 의존성을 제거하고, 일반 사용자 권한으로 `~/.local/forgeflow` 및 `~/.local/bin`에 설치되는 Zero-Clone 및 Non-Root 배포 모델 구축.
- **AI 에이전트 스킬 생태계 연동**:
  - `/setup-forgeflow`: 프로젝트에 `.forgeflow.json`, `.specify/`, `tasks/` 레이아웃을 원스톱으로 구성.
  - `/update-forgeflow`: 진행 중인 작업을 보존하면서 거버넌스 헌법과 훅 설정을 안전하게 마이그레이션.
  - Spec Kit 공식 7종 스킬(`speckit-*`) 자동 감지 및 설치 지원.
- **5대 불변 거버넌스 헌법 (`.specify/memory/constitution.md`)**:
  - 제1조: 게이트 승인 전 구현 엄격 금지 (Fail-Closed).
  - 제2조: 원자적 태스크 순차 실행 및 TDD 원칙.
  - 제3조: 5회 자율 자가 치유 한도 (Infinite Loop 방지).
  - 제4조: Gate 2 QA Sign-Off 및 커밋 SHA 바인딩.
  - 제5조: 패키지 밀봉 및 불변 보관.
- **가벼운 릴리즈 수명주기 디렉토리 (`tasks/`)**:
  - `tasks/in-progress/<release-id>`: 단일 활성 릴리즈 패키지 작업 공간.
  - `tasks/completed/<release-id>`: Gate 3 통과 후 원자적으로 밀봉된 불변 아카이브 공간.
- **자율 자가 치유 루프 (Loop 2) 규범**:
  - 구현 도중 단위/통합 테스트 실패 시 `원인 분석 ➔ 코드 수정 ➔ 테스트 검증 ➔ git commit` 단위를 에이전트가 최대 5회 자율 수행.
- **Zero-Dependency 원칙**:
  - 외부 서드파티 런타임 의존성 없이 Python 3.10+ 표준 라이브러리(Standard Library)만으로 100% 동작 보장.
