# 실제 CLI 개발 사이클 검증

2026-11-02. 기존 단일 파일 smoke test를 보완해, 격리 설치된 ForgeFlow로 작은 프로그램의 개발·실패·복구를 실행했습니다. 원본 runtime을 import하거나 mock하지 않고 CLI를 별도 process로 호출했습니다.

## 대상과 방법

대상 프로그램은 Decimal로 할인 금액을 계산하는 Python CLI입니다. `100 20`을 입력하면 `80.00`을 출력하고, 0..100 범위를 벗어난 할인율은 실패해야 합니다. 프로그램 실행을 검사하는 실제 unittest를 프로젝트 필수 checks로 선언했습니다. Task checks를 빈 배열로 주어도 프로젝트 검사는 실행됩니다.

매번 임시 prefix/bin/skills에 설치하고 실제 Git 저장소를 구성합니다. Push 대상도 로컬 bare remote입니다. 원격 서비스·사용자 프로젝트·전역 설치를 변경하지 않습니다. Spec Kit support scripts로 문서 경로와 templates를 생성하고, 테스트 수행자가 spec/plan/tasks와 프로그램을 작성합니다. LLM이 요구사항을 해석하거나 구현을 작성한 실험은 아닙니다.

## 시나리오와 관찰

| 시나리오 | 실제 실행·판정 |
| --- | --- |
| Spec Kit부터 통합·정리까지 | feature/plan/tasks 준비 → project 검사 실패 → finalize 차단 → 구현 수정 → PASS → scope commit → bare remote push → local FF merge → branch 삭제 → cleaned. 통합된 프로그램 출력과 remote SHA 확인 |
| 사용자 변경 보존 | 위 흐름에서 같은 파일의 staged/unstaged 내용과 별도 untracked 파일을 각각 유지. Target commit에 사용자 draft가 들어가지 않았음을 확인 |
| 검증 freshness | 구현 파일 또는 선언 환경 변경 뒤 verification-stale·finalize 차단. Git commit/ref 미변경 확인 |
| 미commit dependency | dirty rates.json을 사용해 검사 자체는 성공하더라도 scope 밖 dependency가 빠진 commit·통합은 차단. 파일과 main의 기존 내용 보존 |
| 실제 Git lock 후 재개 | source ref lock 때문에 branch 삭제 실패. 이미 통합된 결과와 verification을 저장하고 별도 CLI process에서 cleanup만 재개. Target SHA·검증 기록 동일 |
| Host adapter 계약 | core가 직접 commit/merge하지 않고 pending 반환. 외부 Git 수행 전 merge/delete receipt 거절, 수행 후 실제 Git 결과와 일치할 때만 수용 |
| Target divergence | main과 source가 갈라지면 reconcile로 차단. 외부 rebase 및 재검증 후 FF integration 완료 |
| 권한 없음 | 검증 PASS만으로 commit/merge/delete를 실행하지 않음. Source/target refs·current branch 보존 |
| 설치 교체·baseline adoption | 같은 version의 다른 spec build에서 기존 task 실행 차단. 기록된 pinned command로 기존 규칙을 실행한 뒤 명시적 adopt·재검증·readiness-only 완료 |
| 검사 생성물 | Git ignore에서 빠진 Python cache 생성 시 검사 exit=0이어도 stale로 차단. 프로젝트의 생성물 ignore 정책을 복원하고 재검증한 뒤 완료 |

위 표의 사용자 변경 보존은 첫 시나리오에 포함합니다. 9개 acceptance를 포함한 전체 424 tests가 통과했습니다(124.733초). 이후 fixture의 rates.json 입력 선언과 동일 prefix에서 실제 current 전환 관찰을 강화하고 해당 9개를 다시 실행해 모두 통과했습니다(31.017초). 모든 명령과 stdout/stderr를 선택적으로 보존할 수 있습니다.

설치 CLI에서 pinned 명령으로 전환하면 launcher의 PYTHONPATH 또는 interpreter path 차이로 환경 digest가 달라질 수 있습니다. 이 경우 baseline은 유지하면서 검사만 다시 실행합니다. 실제 실험에서 content/baseline digest는 같고 environment digest만 바뀜을 확인했습니다. 같은 규칙을 재개할 수 있다는 주장과 이전 실행 환경의 PASS를 그대로 재사용한다는 주장을 구분합니다.

## 재현

Repository root에서 Python 3.10+·Bash·Git으로 실행합니다.

~~~bash
python3 -m unittest discover -s tests -p 'test_workflow_e2e.py' -v
~~~

선택적으로 `FORGEFLOW_E2E_EVIDENCE`에 로그 저장 디렉터리를 지정하면 scenario별 argv/cwd/exit/stdout/stderr JSON을 보존합니다. 지정하지 않으면 임시 fixture만 사용합니다. 전체 unittest discovery에도 같은 9개 검사가 포함됩니다.

## 제출 근거와 남은 범위

Core CLI의 로컬 개발·검증·통합·복구 및 host adapter 계약에 대한 구현 검토 근거를 확보했습니다. 실패를 PASS로 간주하거나 Git 결과 대신 문서의 완료 표시로 판정하지 않았습니다.

실제 GitHub PR lifecycle·branch protection·Codex worktree archive tool은 실행하지 않았습니다. Host 시나리오의 실행자는 명시적으로 external-git-fixture이며, 이를 실제 Codex host integration 완료로 표시하지 않습니다. 생성 skill을 읽은 에이전트가 자연어 요구사항부터 끝까지 자율 수행하는 pilot, 다른 stack/OS 운영 검증도 이번 실험의 결과에 포함하지 않습니다.
