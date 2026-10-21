# Specification: Interactive Upgrade Prompt and Force Option

- **Release ID**: `v0.1.9-interactive-upgrade-prompt`
- **Created Date**: 2026-10-21
- **Risk Tier**: **Tier 1 (Minor / Fast-track - CLI UX Improvement)**

---

## 1. 개요 및 목적 (Overview & Purpose)

현재 `forgeflow upgrade` 명령어는 새 버전이 발견되었을 때 사용자 확인 없이 즉시 원격 설치 스크립트를 다운로드하여 실행한다.
사용자가 현재 로컬 버전과 원격 최신 버전을 사전에 비교·인지하고 업그레이드 여부를 능동적으로 선택할 수 있도록 대화형 확인 프롬프트(`y/n`)를 도입한다.
동시에 CI/CD 파이프라인이나 무인 자동화 환경, 사용자의 즉시 실행 요청을 위해 `--force` 옵션 지정 시 확인 프롬프트 없이 바로 업그레이드/재설치를 수행하도록 개선한다.

---

## 2. 세부 요구사항 (Detailed Requirements)

1. **버전 비교 정보 출력**:
   - `forgeflow upgrade` 실행 시, 업그레이드 수행 전 현재 로컬 버전(`current_version`)과 원격 최신 버전(`remote_version`)을 명확히 비교하여 터미널에 표시.
2. **대화형 승인 프롬프트 (`y/n`)**:
   - 업그레이드가 가능하거나 강제 재설치 대상일 때, `--force` 플래그가 없으면 사용자에게 업그레이드 여부를 질문:
     `Do you want to upgrade to v{remote_version}? [y/N]: `
   - 사용자가 `y` 또는 `yes`(대소문자 무관)를 입력한 경우에만 실제 업그레이드(설치) 프로세스 진행.
   - `n`, `no`, 또는 빈 입력(Enter) 등 그 외 입력을 한 경우 `Upgrade cancelled.` 메시지와 함께 변경 없이 종료 (return 0).
3. **`--force` 옵션 동작**:
   - `--force` 지정 시 대화형 프롬프트를 건너뛰고(skip confirmation prompt) 즉시 업그레이드/재설치 수행.
   - 최신 버전인 경우에도 `--force` 지정 시 확인 없이 강제 재설치 수행.
4. **`--json` 및 비대화형 환경 지원**:
   - `--json` 모드 호출 시 대화형 프롬프트 대기 없이 JSON 응답을 정상 제공.
5. **단위 테스트 동기화 (`tests/test_upgrade_cli.py`)**:
   - 대화형 프롬프트에서 `y` 입력 시 업그레이드 정상 진행 테스트.
   - `n` 입력 시 업그레이드 취소 및 미실행 테스트.
   - `--force` 옵션 사용 시 프롬프트 없이 즉시 진행 테스트.
6. **버전 승격**:
   - `src/forgeflow/_version.py`를 `0.1.9`로 승격.

---

## 3. 인수 조건 (Acceptance Criteria)

- **AC-1**: `forgeflow upgrade` 실행 시 현재 버전과 최신 버전이 출력되고 `y/n` 확인을 묻는다.
- **AC-2**: 대화형 프롬프트에서 `y` 입력 시 업그레이드가 실행되고, `n` 입력 시 취소된다.
- **AC-3**: `forgeflow upgrade --force` 실행 시 확인 질문 없이 즉시 업그레이드가 진행된다.
- **AC-4**: 이미 최신 버전일 때 `forgeflow upgrade`는 추가 질문 없이 최신 상태임을 안내하고 종료한다.
- **AC-5**: `tests/test_upgrade_cli.py` 단위 테스트가 추가/갱신되고 전체 테스트 스위트 100% Pass 및 `forgeflow check --all --strict` 🟢 ALL PASSED를 달성한다.
- **AC-6**: `src/forgeflow/_version.py` 버전이 `0.1.9`로 승격된다.
