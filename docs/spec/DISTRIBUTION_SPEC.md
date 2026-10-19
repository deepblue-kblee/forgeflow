# 📦 ForgeFlow 배포 및 다중 사용자 규격서 (DISTRIBUTION_SPEC.md)

이 문서는 ForgeFlow 프레임워크의 시스템 전역 배포 아키텍처, 다중 사용자 계정 공유 모델, 버전 누적 및 원자적 롤백 메커니즘을 정의하는 정식 표준 규격서이다.

---

## 1. 배경 및 설계 원칙

### 1.1 저장소 격리 (Repository Isolation)
- ForgeFlow는 프레임워크 개발 저장소(`work/repo/forgeflow`)와 런타임 배포 환경을 완전히 분리한다.
- 개발자의 작업 브랜치 전환이나 미완성 코드가 시스템 전역의 `forgeflow` 실행 환경에 직접 노출되지 않도록 고정된 배포 패키지 디렉토리를 사용한다.

### 1.2 다중 계정 접근성 (Multi-User Accessibility)
- 동일 머신의 모든 사용자 계정(예: `jarvis`, `deepblue` 등)이 권한 장벽 없이 ForgeFlow CLI를 실행할 수 있어야 한다.
- 특정 사용자의 홈 디렉토리(`~/.local/...`)에 의존하지 않고, 모든 계정이 읽기/실행 가능한 시스템 공용 디렉토리(`/opt/forgeflow`)를 기본 설치 위치로 사용한다.

### 1.3 Zero-Dependency 독립 실행 (Self-Contained Execution)
- ForgeFlow 코어는 Python 3.10+ 표준 라이브러리만을 사용하는 Zero-Dependency 원칙을 준수한다.
- 복잡한 가상환경(`venv`) 오버헤드 없이, 배포 패키지 자체의 `lib/` 디렉토리를 `PYTHONPATH`의 최우선 순위로 격리 지정하는 가벼운 셸 런처를 통해 독립 실행을 보장한다.

---

## 2. 배포 디렉토리 구조 및 계층 표준

기본 설치 루트 디렉토리는 `/opt/forgeflow`이며, 아래와 같은 디렉토리 계층을 유지한다:

```text
/opt/forgeflow/
├── packages/
│   ├── 0.17.0/
│   │   ├── lib/
│   │   │   └── forgeflow/          # Zero-dependency 순수 파이썬 라이브러리 및 템플릿
│   │   ├── bin/
│   │   │   ├── forgeflow           # 버전 격리형 런처
│   │   │   └── harness -> forgeflow # 하위 호환 심볼릭 링크
│   │   └── package.json            # 배포 메타데이터
│   └── 0.18.0/
│       ├── lib/
│       │   └── forgeflow/
│       ├── bin/
│       │   ├── forgeflow
│       │   └── harness -> forgeflow
│       └── package.json
├── current -> packages/0.18.0      # 현재 활성 버전을 가리키는 원자적 심볼릭 링크
└── bin/
    ├── forgeflow -> ../current/bin/forgeflow
    └── harness -> ../current/bin/harness

/usr/local/bin/ (전역 PATH)
├── forgeflow -> /opt/forgeflow/bin/forgeflow
└── harness -> /opt/forgeflow/bin/harness
```

---

## 3. 권한 및 보안 모델 (Security & Permissions)

1. **디렉토리 퍼미션 (`755`)**:
   - `/opt/forgeflow`, `packages/`, 각 버전 디렉토리, `bin/`은 `rwxr-xr-x`(`0755`)로 설정하여 모든 사용자 계정의 진입 및 조회를 허용하되, 비권한 사용자의 임의 변조를 차단한다.
2. **파일 퍼미션 (`644` / `755`)**:
   - 일반 소스 코드 및 템플릿 파일은 `rw-r--r--`(`0644`), 실행 런처 스크립트는 `rwxr-xr-x`(`0755`)로 설정한다.
3. **환경 오염 차단**:
   - 런처 스크립트는 `export PYTHONPATH="$PKG_DIR/lib:${PYTHONPATH:-}"`를 적용하여 사용자의 로컬 파이썬 패키지나 시스템 경로와의 충돌을 원천 방어한다.

---

## 4. 런처 스크립트 규격 (`bin/forgeflow`)

패키지 내부 `bin/forgeflow`는 POSIX 호환 bash 셸 스크립트로 생성되며 다음 동작을 보장한다:

1. **심볼릭 링크 체인 추적 및 상대 경로 탐색 (Canonical Symlink Resolution)**:
   - `/usr/local/bin/forgeflow` 또는 `~/.local/bin/forgeflow` 등 다단계 심볼릭 링크를 통해 호출되더라도 `readlink` 루프를 통해 정규화된 실제 패키지 `bin/` 및 `lib/` 경로를 정확히 추적하여 `PYTHONPATH`를 격리 바인딩한다.
   - 바이너리 이동 또는 심볼릭 링크 위치 변경 시에도 패키지 디렉토리를 올바르게 특정한다.
2. **Python 인터프리터 자동 감지**:
   - 1순위: 환경 변수 `FORGEFLOW_PYTHON` (지정된 경우 최우선 존중).
   - 2순위: `/opt/homebrew/bin/python3`.
   - 3순위: `/usr/local/bin/python3`.
   - 4순위: `PATH` 상의 `python3`.
   - 감지된 인터프리터가 `sys.version_info >= (3, 10)`을 만족하는지 즉시 검증하며, 미충족 시 명확한 오류 메시지를 표준 에러로 출력하고 종료 코드 1로 반환한다.
3. **인자 전달**: `exec "$PYTHON_BIN" -m forgeflow.cli "$@"`를 통해 전달받은 모든 CLI 인자를 원형 그대로 유지하여 포워딩한다.

---

## 5. 버전 누적, 원자적 전환 및 롤백 정책

1. **버전 누적 (Package Accumulation)**:
   - 신규 릴리즈 배포 시 `packages/<new-version>`을 생성하여 소스를 배치한다. 기존 과거 버전은 보존된다.
2. **원자적 활성화 (Atomic Activation)**:
   - `ln -sfn packages/<new-version> /opt/forgeflow/current`를 실행하여 무중단(zero-downtime)으로 활성 버전을 즉각 전환한다.
3. **버전 보관 주기 (Retention Policy)**:
   - `--keep <N>` 옵션(기본값: 5)을 통해 현재 활성 버전을 제외한 가장 오래된 구버전 패키지를 자동으로 삭제 정리한다.
4. **즉각 롤백 (Instant Rollback)**:
   - 배포 후 이상 감지 시 `./install.sh --rollback <version>`을 호출하여 `current` 링크를 지정한 과거 버전으로 즉시 원복한다.

---

## 6. CLI 단일 진입점 및 'harness' 통합 규격

1. **단일 진입점 원칙**:
   - ForgeFlow 프레임워크의 공식 표준 CLI 진입점은 `forgeflow`이다.
   - 품질 및 하네스 게이트 검사는 `forgeflow check`로 일원화한다.
   - AST 코드 스멜 정적 분석은 `forgeflow review`로 일원화한다.
2. **하위 호환 심볼릭 링크**:
   - 기존 자동화 스크립트 및 레거시 워크플로우를 위해 `bin/harness` 심볼릭 링크를 `forgeflow`로 연결한다.
   - `harness check` 호출 시 내부적으로 `forgeflow check`와 완전히 동일하게 처리된다.
