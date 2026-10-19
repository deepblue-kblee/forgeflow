# 📦 ForgeFlow 배포 및 설치 아키텍처 규격서 (DISTRIBUTION_SPEC.md)

이 문서는 ForgeFlow 프레임워크의 사용자 계정 로컬(User-Local) 배포 아키텍처, Zero-Clone 설치 모델, AI 에이전트 스킬 생태계 연동 및 무중단 업데이트 메커니즘을 정의하는 정식 표준 규격서이다.

---

## 1. 배경 및 설계 원칙

### 1.1 Zero-Clone 원칙 (저장소 비복제 설치)
- 개발자는 ForgeFlow 소스 저장소(`work/repo/forgeflow`)를 로컬 머신에 `git clone`할 필요가 없다.
- 원격 배포 스크립트(`install.sh`)를 통해 필요한 핵심 라이브러리와 런처, 에이전트 스킬만을 대상 머신에 직접 다운로드 및 배치한다.

### 1.2 Non-Root / User-Local 원칙 (사용자 권한 격리)
- 시스템 전역 관리자 권한(`sudo`)이나 `/opt`, `/usr/local/bin` 등의 시스템 공용 디렉토리 의존성을 완전히 배제한다.
- 운영체제 표준 사용자 홈 디렉토리(`~/.local/forgeflow`, `~/.local/bin`)에 격리 배포하여 다중 사용자 충돌을 방지하고 일반 사용자 권한으로 안전하게 동작한다.

### 1.3 Zero-Dependency 독립 실행 (Self-Contained Execution)
- ForgeFlow 코어와 CLI는 외부 서드파티 런타임 의존성 없이 **Python 3.10+ 표준 라이브러리(Standard Library)만으로 100% 동작**한다.
- 별도의 무거운 가상환경(`venv`) 생성이나 패키지 매니저(`pip`) 오버헤드 없이 순수 파이썬 라이브러리 디렉토리를 `PYTHONPATH`로 바인딩하는 독립 셸 런처를 통해 가볍고 즉각적인 실행을 보장한다.

### 1.4 에이전트 스킬 생명주기 일원화
- CLI 툴과 AI 에이전트 스킬(`setup-forgeflow`, `update-forgeflow`, `speckit-*`)을 단일 설치 파이프라인에서 함께 배포하여 도구와 스킬의 버전 불일치를 원천 차단한다.

---

## 2. 배포 디렉토리 구조 및 계층 표준

설치 루트는 사용자 홈 디렉토리(`~/.local/forgeflow`)이며, 표준 디렉토리 계층은 다음과 같다:

```text
~/.local/forgeflow/
├── lib/
│   └── forgeflow/                  # Zero-Dependency 순수 파이썬 패키지 및 템플릿
│       ├── __init__.py
│       ├── cli.py                  # CLI 엔트리포인트 및 명령어 라우팅
│       ├── validator.py            # 게이트 검증 및 무결성 감사 엔진
│       ├── reviewer.py             # 정적 분석 및 린트 엔진
│       ├── scaffold.py             # 하이브리드 프로젝트 스캐폴딩 엔진
│       └── templates/              # 프로젝트 주입용 거버넌스 템플릿 및 헌법
└── bin/
    └── forgeflow                   # 격리형 셸 런처 스크립트

~/.local/bin/ (사용자 PATH)
├── forgeflow -> ~/.local/forgeflow/bin/forgeflow
└── harness -> ~/.local/forgeflow/bin/forgeflow (호환 별칭 심볼릭 링크)

~/.agents/skills/ (Vercel Skills 호환 표준 에이전트 스킬)
├── setup-forgeflow/                # /setup-forgeflow 스킬 (프로젝트 스캐폴딩)
│   └── SKILL.md
├── update-forgeflow/               # /update-forgeflow 스킬 (거버넌스 업그레이드)
│   └── SKILL.md
└── speckit-*                       # Spec Kit 공식 7종 에이전트 스킬 (자동 설치)
```

---

## 3. 원클릭 설치 체계 (`install.sh`)

### 3.1 설치 명령어
터미널 또는 AI 에이전트 대화창에서 원클릭으로 설치를 완료한다:
```bash
curl -sSL https://raw.githubusercontent.com/deepblue-kblee/forgeflow/main/install.sh | bash
```

### 3.2 설치 프로세스 파이프라인
1. **환경 사전 검증**:
   - `python3` 3.10+ 설치 여부 검증.
   - `git`, `curl`, `tar` 등 기본 도구 가용성 확인.
2. **패키지 아카이브 다운로드 및 추출**:
   - GitHub 공식 메인 브랜치에서 최신 소스 tarball을 다운로드하여 `~/.local/forgeflow/`에 패키징.
3. **격리형 런처(`bin/forgeflow`) 생성**:
   - `~/.local/forgeflow/lib`를 `PYTHONPATH`로 주입하고 `python3 -m forgeflow.cli "$@"`를 호출하는 실행 스크립트 생성 (`chmod 755`).
4. **전역 PATH 심볼릭 링크 등록**:
   - `~/.local/bin/forgeflow` 및 호환 별칭 `~/.local/bin/harness` 링크 생성.
   - 사용자 셸 설정(`.zshrc`, `.bashrc` 등)에 `~/.local/bin` PATH 포함 여부 감지 및 안내.
5. **에이전트 스킬 자동 설치 (`scripts/install-skills.sh`)**:
   - `~/.agents/skills/setup-forgeflow/` 및 `update-forgeflow/` 복사.
   - Spec Kit 공식 7종 스킬(`speckit-specify`, `speckit-clarify`, `speckit-plan`, `speckit-tasks`, `speckit-implement`, `speckit-constitution`, `speckit-analyze`)의 존재 여부를 감지하고, 미설치 시 `npx -y skills add`를 통해 자동 설치.

---

## 4. 버전 관리 및 마이그레이션 (`update`)

### 4.1 CLI 업데이트
프레임워크 버전 업그레이드는 CLI 명령 또는 에이전트 스킬을 통해 비파괴적으로 수행된다:
```bash
forgeflow update
```
*(또는 에이전트 대화창에서 `/update-forgeflow` 호출)*

### 4.2 프로젝트 거버넌스 헌법 마이그레이션
- 기존 개발 프로젝트에서 `update`를 실행할 경우, 현재 진행 중인 태스크(`tasks/in-progress/`)와 과거 완료 아카이브(`tasks/completed/`) 데이터는 100% 안전하게 보존된다.
- `.specify/memory/constitution.md` 및 `.specify/extensions.yml`의 강제 훅 설정만을 최신 프레임워크 규격으로 원자적 갱신한다.
