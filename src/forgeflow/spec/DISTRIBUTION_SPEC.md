# 📦 ForgeFlow 배포 및 설치 아키텍처 규격서 (DISTRIBUTION_SPEC.md)

이 문서는 ForgeFlow 프레임워크의 사용자 계정 로컬(User-Local) 배포 아키텍처, Zero-Clone 설치 모델, AI 에이전트 스킬 생태계 연동 및 무중단 업데이트 메커니즘을 정의하는 정식 표준 규격서이다.

---

## 1. 배경 및 설계 원칙

### 1.1 Zero-Clone 원칙 (저장소 비복제 설치)
- 개발자는 ForgeFlow 소스 저장소(`work/repo/forgeflow`)를 로컬 머신에 `git clone`할 필요가 없다.
- 원격 배포 스크립트(`install.sh`)를 통해 필요한 핵심 라이브러리와 런처, 에이전트 스킬만을 대상 머신에 직접 다운로드 및 배치한다.

### 1.2 Non-Root / User-Local 원칙 (사용자 권한 격리)
- 시스템 전역 관리자 권한(`sudo`)이나 `/opt`, `/usr/local/bin` 등의 시스템 공용 디렉토리 의존성을 완전히 배제한다.
- 운영체제 표준 사용자 홈 디렉토리(`~/.local/share/forgeflow`, `~/.local/bin`)에 격리 배포하여 다중 사용자 충돌을 방지하고 일반 사용자 권한으로 안전하게 동작한다.

### 1.3 Zero-Dependency 독립 실행 (Self-Contained Execution)
- ForgeFlow 코어와 CLI는 외부 서드파티 런타임 의존성 없이 **Python 3.10+ 표준 라이브러리(Standard Library)만으로 100% 동작**한다.
- 별도의 무거운 가상환경(`venv`) 생성이나 패키지 매니저(`pip`) 오버헤드 없이 순수 파이썬 라이브러리 디렉토리를 `PYTHONPATH`로 바인딩하는 독립 셸 런처를 통해 가볍고 즉각적인 실행을 보장한다.

### 1.4 에이전트 스킬 생명주기 일원화
- CLI 툴과 AI 에이전트 스킬(`setup-forgeflow`, `update-forgeflow`, `speckit-*`)을 단일 설치 파이프라인에서 함께 배포하여 도구와 스킬의 버전 불일치를 원천 차단한다.

---

## 2. 배포 디렉토리 구조 및 계층 표준

설치 루트는 XDG 표준 데이터 디렉토리(`~/.local/share/forgeflow`)이며, 표준 디렉토리 계층은 다음과 같다:

```text
~/.local/share/forgeflow/
├── CHANGELOG.md                    # 전체 릴리즈 변경 이력 (spec/ 외부로 격리)
├── current -> packages/<version>   # 현재 활성화된 최신 버전 심볼릭 링크 (SSOT)
├── bin/
│   ├── forgeflow -> ../current/bin/forgeflow
│   └── harness -> ../current/bin/harness
└── packages/                       # 설치된 버전별 패키지 (AI 에이전트 직접 탐색 엄격 금지)
    └── <version>/
        ├── package.json            # 패키지 빌드 메타데이터
        ├── bin/
        │   ├── forgeflow           # 격리형 셸 런처 스크립트
        │   └── harness             # 호환 별칭 심볼릭 링크
        └── lib/
            └── forgeflow/          # Zero-Dependency 순수 파이썬 패키지
                ├── _version.py
                ├── cli.py
                ├── validator.py
                ├── reviewer.py
                ├── scaffold.py
                ├── spec/           # 공식 거버넌스 사양서 및 라우터 (README.md, VERSION)
                └── templates/      # 프로젝트 주입용 거버넌스 템플릿

~/.local/bin/ (사용자 PATH)
├── forgeflow -> ~/.local/share/forgeflow/bin/forgeflow
└── harness -> ~/.local/share/forgeflow/bin/harness

타깃 프로젝트/
└── .forgeflow/
    ├── config.json                 # 프로젝트 거버넌스 설정
    └── spec -> ~/.local/share/forgeflow/current/lib/forgeflow/spec/  # 사양서 심볼릭 링크
```

> [!IMPORTANT]
> **패키지 직접 탐색 금지 규범**: AI 에이전트는 `packages/` 하위 디렉토리를 직접 열람하거나 과거 버전을 참조해서는 안 된다. 모든 사양과 바이너리는 반드시 `current` 심볼릭 링크를 통해서만 참조한다.


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
   - GitHub 공식 메인 브랜치에서 최신 소스 tarball을 다운로드하여 `~/.local/share/forgeflow/`에 패키징.
   - 전체 변경 이력(`CHANGELOG.md`)을 `~/.local/share/forgeflow/CHANGELOG.md`로 배포하여 사양서(`spec/`)로부터 이력을 완전 격리.
3. **격리형 런처(`bin/forgeflow`) 생성**:
   - `packages/<version>/lib`를 `PYTHONPATH`로 주입하고 `python3 -m forgeflow.cli "$@"`를 호출하는 실행 스크립트 생성 (`chmod 755`).
   - `current` 심볼릭 링크를 해당 패키지 버전으로 원자적 전환.
4. **전역 PATH 심볼릭 링크 등록**:
   - `~/.local/bin/forgeflow` 및 호환 별칭 `~/.local/bin/harness` 링크 생성.
   - 사용자 셸 설정(`.zshrc`, `.bashrc` 등)에 `~/.local/bin` PATH 포함 여부 감지 및 안내.
5. **에이전트 스킬 자동 설치 (`scripts/install-skills.sh`)**:
   - `~/.agents/skills/setup-forgeflow/` 및 `update-forgeflow/` 복사.
   - Spec Kit 공식 7종 스킬(`speckit-specify`, `speckit-clarify`, `speckit-plan`, `speckit-tasks`, `speckit-implement`, `speckit-constitution`, `speckit-analyze`)의 존재 여부를 감지하고, 미설치 시 `npx -y skills add`를 통해 자동 설치.

---

## 4. 버전 관리 및 마이그레이션 (`upgrade` & `update`)

프레임워크 버전 관리와 거버넌스 사양 마이그레이션은 역할에 따라 명확히 분리된 대칭 CLI와 스마트 파사드 스킬을 통해 비파괴적으로 수행된다.

### 4.1 전역 런타임 업그레이드 (`forgeflow upgrade`)
사용자 OS 계정 전역의 CLI 바이너리, 순수 파이썬 라이브러리(`~/.local/share/forgeflow`), 및 에이전트 스킬(`~/.agents/skills/`)을 최신 공식 릴리즈로 판올림한다:
- **Cache-Busting & Inversion Guard**: GitHub Raw CDN의 기본 300초 캐시로 인한 구버전 반환 문제를 방지하기 위해 `Cache-Control: no-cache` 헤더 및 타임스탬프 쿼리(`?t=...`)를 적용하며, 캐시 전파 지연으로 원격 버전이 로컬 버전보다 낮을 경우 이상 감지 경고를 출력한다.
- **실설치 버전 검증**: 업그레이드 완료 후 실제 설치/활성화된 패키지 버전을 직접 재검증하여 성공 메시지를 출력한다.
```bash
# 최신 버전 확인
forgeflow upgrade --check

# 전역 런타임 및 스킬 대화형 업그레이드 (버전 비교 후 y/n 확인)
forgeflow upgrade

# 확인 프롬프트 없이 즉시 강제 업그레이드/재설치
forgeflow upgrade --force
```

### 4.2 로컬 프로젝트 거버넌스 사양 동기화 (`forgeflow update`)
- 현재 개발 프로젝트 루트에서 실행하여 `.forgeflow/config.json`(구버전 .forgeflow.json 시 자동 마이그레이션), `.specify/scripts/bash/`(0o755 권한 부여), 템플릿, 헌법 및 훅을 현재 설치된 ForgeFlow 규격으로 원자적 갱신한다.
- 현재 진행 중인 태스크(`tasks/in-progress/`)와 과거 완료 아카이브(`tasks/completed/`) 데이터는 100% 안전하게 보존된다:
```bash
forgeflow update
```

### 4.3 통합 스마트 파사드 스킬 (`/update-forgeflow`)
AI 에이전트 대화창에서 원스톱으로 호출하여 1단계 전역 최신화 점검(`forgeflow upgrade`) ➔ 2단계 현재 프로젝트 거버넌스 갱신(`forgeflow update`)을 순차 실행한다:
```text
/update-forgeflow
```
