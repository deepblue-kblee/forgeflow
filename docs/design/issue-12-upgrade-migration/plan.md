# Issue #12 implementation plan

## 1. 공통 migration layer

새 `src/forgeflow/migration.py`가 inventory, classification, plan, apply를 소유한다. `scaffold.py`는 desired asset 계산과 기존 init 흐름을 유지하고, update는 migration layer를 사용한다.

### Asset 분류

| classification | 판정 |
| --- | --- |
| `missing` | 필요한 framework asset이 없음 |
| `framework-owned-unmodified` | 현재 desired bytes 또는 알려진 v0.1.24 bytes와 exact match |
| `user-modified-or-unknown` | 알려진 path이지만 known bytes와 다름 |
| `historical-evidence` | `tasks/completed/**`, `docs/releases/**`; inventory에서 write 대상 제외 |
| `active-baseline-dependent` | `.forgeflow/runtime/**`, `run.py`, `runtime.json`, `spec` link; active task 존재 시 write 금지 |

Ownership은 version 문자열, mtime, 단어 존재로 추정하지 않는다. hash/exact content와 managed block만 사용한다.

### Plan/apply

- `build_update_plan(root, config, ...)`는 write 없이 asset 목록, config 변경, baseline 전환, blocker, conflict를 계산한다.
- `apply_update_plan(plan)`은 lock 없는 단일 process 가정에서 write 직전 hash를 재확인한다. 계획 이후 사용자 bytes가 바뀌면 중단하고 `needs-action`를 반환한다.
- 변경 대상은 `.forgeflow/migration-backups/<UTC>-<pid>/`에 상대 경로로 backup한다. backup은 active 지침 경로에 두지 않는다.
- 실패 시 이번 operation이 만든/바꾼 managed file만 backup에서 복구하고, 새 directory/file은 제거한다. 사용자 파일과 Git index는 건드리지 않는다.
- 성공/실패/partial 기록은 `.forgeflow/migrations/<UTC>-<pid>.json`에 남긴다.
- 두 번째 실행은 모든 action이 `none`이면 filesystem을 쓰지 않고 `no-op`을 반환한다.

### 결과 status와 exit code

| status | 의미 | exit |
| --- | --- | --- |
| `applied` | 계획된 managed 변경 적용 완료 | 0 |
| `planned` | dry-run inventory/plan | 0 |
| `no-op` | 변경 없음 | 0 |
| `needs-action` | active work/plan drift/unresolved conflict로 write 전 중단 | 3 |
| `partial` | 일부 적용 후 실패, managed 변경 복구 시도 결과 보고 | 4 |
| `error` | 입력/환경 오류 | 1 |

`conflicts`는 자동 적용하지 않은 알려진 framework path와 이유/필요 조치를 포함한다. `blockers`는 write를 막은 항목이다. 자동 실행 주체는 `status`와 exit code로 완료 여부를 판단한다.

### Config·baseline

- `.forgeflow.json`만 있으면 값을 보존한 `.forgeflow/config.json`을 생성하고 legacy는 recovery evidence로 유지한다.
- 둘 다 있으면 modern을 authoritative로 사용하고, legacy와의 차이를 `warnings`/`assets`에 보고한다. 자동 병합·삭제하지 않는다.
- `forgeflow_version`만 올리는 것으로 migration 완료를 보고하지 않는다.
- active work가 있으면 write 전에 차단한다. baseline이 현재 배포와 같으면 유지하고, 다르면 `workflow adopt` 또는 pinned command를 next action으로 안내한다.
- active work가 없으면 현재 배포 snapshot으로 baseline을 갱신하고 created/updated file을 결과에 포함한다.

## 2. Legacy asset 정책

| 자산 | v0.1.24 exact match | 그 외 |
| --- | --- | --- |
| `.specify/memory/constitution.md` | lean reference로 교체 | 보존 + conflict |
| `.specify/extensions.yml` | framework hook 제거한 lean extensions로 교체 | 보존 + conflict |
| `.specify/templates/commands/implement.md` | lean command로 교체 | 보존 + conflict |
| `.specify/scripts/bash/*` | 현재 bundled script로 갱신 | 보존 + conflict |
| `.specify/templates/*.md` | 현재 bundled template로 갱신 | 보존 + conflict |
| `docs/spec/ANTI_PATTERNS.md` | 현재 packaged spec으로 갱신 | 보존 |
| `docs/adr/{001,002,template}.md` | 현재 packaged ADR로 갱신 | 보존 |
| root guides | managed boot anchor만 교체, 본문 보존 | 본문 보존 |
| tasks/completed, docs/releases | 변경 없음 | 변경 없음 |

현재 bundled desired content가 v0.1.24 bytes와 같은 asset은 `none`으로 처리한다. `.specify`가 없는 project에는 optional asset을 만들지 않는다.

## 3. Upgrade

### 취득 대상 고정

- `upgrade --revision <ref>`를 추가한다. 기본 `main`.
- version과 installer는 같은 `--repo-url`/revision에서 읽는다.
- raw GitHub URL은 clone URL로 변환해 installer에 `FORGEFLOW_REPO`와 `FORGEFLOW_REVISION`을 전달한다. custom source는 동일 source로만 설치하며, 변환 불가 시 install 전에 실패한다.
- `source_identity = sha256(version_bytes + installer_bytes)`를 산출해 installer에 `FORGEFLOW_SOURCE_IDENTITY`로 전달하고 package metadata에 기록한다.
- `--check`는 version, `upgrade_available`, `source_identity`, `identity_comparison`을 반환한다. current package metadata에 `source_identity`가 없으면 `unknown`으로 표시한다.

### 실제 결과 검증

installer exit 0 후 다음을 확인한다.

1. `PREFIX/current/package.json` 존재, `version` 일치, `content_identity` 존재
2. 전달한 `source_identity`가 metadata와 일치(기록 가능한 경우)
3. `BIN_DIR/forgeflow version` subprocess 성공 및 version 일치
4. `BIN_DIR/forgeflow workflow --help` 성공
5. `PREFIX/current/lib/forgeflow/spec/README.md` 존재

하나라도 실패하면 `status: error`, `upgraded: false`, 관찰값과 next action을 반환하고 exit 1. `remote_version`을 installed version 기본값으로 사용하지 않는다.

## 4. Installer

- `FORGEFLOW_REVISION` clone/checkout 지원.
- package metadata에 `source_identity` 기록.
- switch 전 staging completeness 확인: `_version.py`, `spec/VERSION`, `spec/README.md`, `scripts/install-skills.sh`, launcher.
- activation 실패 시 이전 `current`, `bin` link를 복구하고 이전 package generator로 skills를 재생성한다. 복구 불가 시 구체 경로와 명령을 보고한다.
- retention은 모든 post-activation probe 성공 후에만 실행한다.
- `--dry-run`은 어떤 것도 쓰지 않는다.

## 5. CLI·spec·skill

- `update --dry-run`, `--accept <path>` (repeatable), help 갱신.
- `upgrade --revision`, help 갱신.
- `DISTRIBUTION_SPEC.md`, `FLOW_SPEC.md`에 migration/upgrade 계약 반영.
- `scripts/install-skills.sh`의 update-forgeflow 지침에 dry-run → apply → conflict resolution 순서 반영.
- version은 0.1.X patch 정책으로 올린다.

## 6. 검증

- 신규 `tests/test_migration.py`: M01, M02, M03, M04(basic), M08, M09, M10
- `tests/test_upgrade_cli.py`: U02(no-op installer), installed metadata/entrypoint probe, same-version identity
- local HTTP fixture 기반 U01-lite: version/installer를 같은 revision에서 취득하고 fake 설치를 실제 subprocess로 검증
- `python3 -m unittest discover -s tests -p "test_*.py"`
- `python3 scripts/sync-distribution.py --check`
- 실제 wheel build 및 격리 install delivery
- 기존 completed strict archive audit 중 영향받는 범위
