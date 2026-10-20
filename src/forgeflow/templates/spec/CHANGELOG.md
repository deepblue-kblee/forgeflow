# 📋 ForgeFlow 변경 이력 (CHANGELOG.md)

ForgeFlow 프레임워크의 모든 주요 변경 사항은 이 문서에 기록됩니다. 본 문서는 [Keep a Changelog](https://keepachangelog.com/ko/1.0.0/) 원칙과 [유의적 버전(Semantic Versioning)](https://semver.org/lang/ko/)을 준수합니다.

> [!NOTE]
> 본 퍼블릭 저장소로 전환되기 이전의 초기 연구 및 프로토타입 개발 이력(v0.1.0 ~ v0.22.1)은 비공개 아카이브 저장소(`deepblue-kblee/forgeflow-old`)에 영구 보존되어 있습니다.

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
