# Setup·배포·runtime 연속성

ForgeFlow는 Python 3.10+ 표준 라이브러리 CLI·공식 spec·templates·생성 skills를 한 배포 단위로 전달합니다. `src/forgeflow/_version.py`가 버전을, `docs/spec/`가 공식 spec 편집 원본을 소유합니다. `src/forgeflow/spec/`는 기계적으로 동기화합니다.

## 설치

install.sh는 `~/.local/share/forgeflow`와 `~/.local/bin`의 account-local 설치를 지원하며 current는 전역 기본 배포를 가리킵니다. `FORGEFLOW_INSTALL_DIR`, `FORGEFLOW_BIN_DIR`, `FORGEFLOW_SKILLS_DIR`로 target을 바꿀 수 있습니다.

새 package key는 `packages/<version>-<builddigest16>`입니다. Metadata의 content identity는 runtime/spec/templates와 installer/skill-generator 입력을 포함합니다. 각 package는 `scripts/install-skills.sh`도 보관합니다.

Installer는 package를 staging directory에 만든 뒤 completeness와 version stamp를 확인하고 immutable key로 publish합니다. current 전환 후 실제 entrypoint·spec·skills를 probe하며, 실패하면 이전 current/bin/skills/CHANGELOG를 복구하고 retention을 실행하지 않습니다. 성공한 probe 뒤에만 retention을 적용합니다.

## Upgrade

`forgeflow upgrade --check --json`은 version, revision, source identity를 읽습니다. `forgeflow upgrade --revision <ref>`는 승인된 범위에서 설치합니다.

- version과 installer는 같은 revision에서 취득합니다.
- immutable revision을 확인할 수 없으면 설치를 거부합니다.
- installer exit 0만으로 성공을 보고하지 않습니다.
- 실제 package metadata, source revision/identity, entrypoint version, spec, 생성 skills를 검증합니다.
- target이 없거나 불일치하면 비성공과 관찰 상태를 반환합니다.

## 프로젝트 setup

`forgeflow init`은 lean config·runtime/spec entrypoint를 구성합니다. `forgeflow init --speckit`은 Spec Kit scripts/templates를 추가합니다. 기존 사용자 config·지침·파일은 보존합니다.

새 프로젝트는 `tasks/`를 만들지 않습니다. 실행 상태는 `.forgeflow/workflows/<id>.json`, 현재 사양서는 `.forgeflow/spec/`입니다.

Project `workflow.checks`에는 실제 프로젝트 검사를 선언합니다. 새 프로젝트의 stack에 맞는 명령을 선택해야 하며 generic Python 명령으로 모든 프로젝트 검증을 대신하지 않습니다.

## 실행 가능한 baseline

```text
.forgeflow/
  config.json
  workflows/<id>.json
  runtime/<digest>/forgeflow/
  run.py
  runtime.json
  spec -> runtime/<digest>/forgeflow/spec/
```

Launcher는 global current 대신 pinned runtime을 실행합니다. 다른 설치 bytes가 active 작업에 새 규칙을 조용히 적용할 수 없으며 mismatch는 pinned 명령을 안내합니다.

## 프로젝트 update

`forgeflow update`는 현재 0.2.x project의 config/runtime/docs를 갱신합니다. `--dry-run --json`은 write 없이 예정 변경을 반환합니다.

- legacy `.forgeflow.json`, `tasks/`, `.forgeflow/lifecycle`이 있으면 자동 변환하지 않고 `needs-action`을 반환합니다.
- legacy project는 별도 `forgeflow-migrate` 도구로 정리한 뒤 update합니다.
- active workflow가 있으면 write 전에 차단하고 pinned command를 안내합니다.
- 사용자 config key와 파일을 보존합니다.

## User project migration

0.1.x project 정리는 core `update`가 아니라 별도 `forgeflow-migrate` 도구가 수행합니다. 이 도구는 `archive/forgeflow-migrate` branch에서 관리하며 core package에는 포함하지 않습니다.

- user repo에 `archive/pre-forgeflow-0.2.0` tag 생성
- `tasks/`, `docs/releases/`, strict constitution/hook/implement, old spec/template 복제본 제거
- 사용자 수정본은 conflict로 보존
- 0.2.x config/docs/AGENTS 작성
- dry-run/apply, JSON/exit code, active-work 차단, idempotency 제공
- migration 후 old path/command 잔존 여부 검증

## 전달성 검증

배포 전 spec equality·버전 stamp·fresh generated skills·package data를 확인합니다. Source/새 build entrypoint를 격리 실행하며 과거 설치 CLI로 새 source를 검증했다고 주장하지 않습니다. Installer 테스트는 prefix·bin-dir·FORGEFLOW_SKILLS_DIR 모두 격리합니다.
