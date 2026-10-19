# 📋 ForgeFlow 변경 이력 (CHANGELOG.md)

ForgeFlow 프레임워크의 모든 주요 변경 사항은 이 문서에 기록됩니다. 본 문서는 [Keep a Changelog](https://keepachangelog.com/ko/1.0.0/) 원칙과 [유의적 버전(Semantic Versioning)](https://semver.org/lang/ko/)을 준수합니다.

> [!NOTE]
> 본 퍼블릭 저장소로 전환되기 이전의 초기 연구 및 프로토타입 개발 이력(v0.1.0 ~ v0.22.1)은 비공개 아카이브 저장소(`deepblue-kblee/forgeflow-old`)에 영구 보존되어 있습니다.

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
