# ForgeFlow

ForgeFlow는 Spec Kit, 프로젝트 검증 명령, Git/host 기능을 연결해 개발부터 허용된 통합·정리까지 조정하는 도구예요. Python 3.10+ 표준 라이브러리로 동작해요.

기본 흐름은 요구사항 → 계획 → 구현 → 검증 → 통합 → 정리 → 완료 보고예요. 구현 전 범위·완료 조건·검증 방법을 확정하고, 통합 전 검증 결과와 실행 권한을 확인해요. 작은 수정에는 짧은 계획을 쓰고 큰 작업에는 Spec Kit spec/plan/tasks를 활용해요. 기본 흐름에 다중 서명 문서나 패키지 밀봉을 강제하지 않아요.

## 설치와 프로젝트 설정

~~~bash
curl -sSL https://raw.githubusercontent.com/deepblue-kblee/forgeflow/main/install.sh | bash
forgeflow --version
forgeflow init --speckit
~~~

설치는 사용자 계정의 ~/.local/share/forgeflow 및 ~/.local/bin을 사용해요. 생성 스킬은 /forgeflow, /setup-forgeflow, /update-forgeflow, /forgeflow-graphify예요. 외부 Spec Kit 스킬 자동 설치는 FORGEFLOW_INSTALL_SPECKIT_SKILLS=1 opt-in이며, core의 runtime dependency는 아니에요.

setup/update는 사용자 설정·헌법·hook·템플릿·진행 중 작업을 보존해요. 프로젝트에 필요한 test/lint/build 명령을 .forgeflow/config.json의 workflow.checks에 선언해주세요. 파일 생성일을 이유로 과거 자료를 삭제하지 않아요.

## 작업 시작

다음 agreement.json은 이미 준비된 codex/example-fix branch에서 src/example.py와 tests/test_example.py의 수정을 검증하고, 해당 범위의 commit까지 위임하는 예시예요. 실제 경로·branch·프로젝트 검증 명령으로 바꿔 사용해주세요. 시작 시 이미 존재하던 변경을 포함하려면 include_existing_changes를 명시적으로 결정해야 해요.

~~~json
{
  "scope": ["src/example.py", "tests/test_example.py"],
  "acceptance": ["재현된 오류가 해결되고 회귀 테스트가 통과한다"],
  "plan": "오류를 재현하고 해당 범위의 구현을 수정한 뒤 프로젝트 검증을 실행한다",
  "checks": [["python3", "-m", "unittest", "discover", "-s", "tests"]],
  "owner": "standalone",
  "source": "codex/example-fix",
  "target": "main",
  "integration": "none",
  "permissions": ["commit"],
  "remote": "origin",
  "task_owned_branch": true,
  "include_existing_changes": false
}
~~~

~~~bash
forgeflow workflow start example-fix --agreement agreement.json
forgeflow workflow check example-fix
# 합의된 범위의 구현
forgeflow workflow verify example-fix
forgeflow workflow finalize example-fix
forgeflow workflow status example-fix
~~~

프로젝트 workflow.checks는 task에서 생략할 수 없어요. 실행 상태의 단일 근거는 .forgeflow/workflows/<id>.json이에요. source/target, owner, 각 operation의 위임 범위를 이미 확인했다면 같은 승인을 반복 요청하지 않아요.

## 통합·정리와 재개

local 통합은 PR 없이 사용할 수 있고 pr route는 owner=host에서 지원해요. merge/push/delete-branch는 각각 해당 permission이 필요해요. host-managed worktree는 host가 소유하며 중복 branch를 만들지 않아요. host 작업은 pending action과 관찰 가능한 실행 영수증으로 연결하고, 정리는 소유 도구를 사용해요.

ready는 검증 완료, integrated는 통합 확인, cleaned는 허용된 정리 완료를 뜻해요. 요청된 위임 범위의 완료는 finalization_complete로 구분해 readiness-only 작업의 완료를 merge로 오인하지 않아요. 통합 후 정리가 실패하면 통합 결과를 유지하고 정리부터 재개해요. 관련 없는 dirty 파일은 보존하고 임의로 commit/reset/stash하지 않아요.

## 업데이트와 작업 기준 고정

~~~bash
forgeflow upgrade --check
forgeflow update
~~~

전역 upgrade와 프로젝트 update는 별도 범위예요. 진행 중 작업은 runtime/spec/templates의 content identity와 실행 가능한 .forgeflow/runtime/<digest>/ snapshot을 유지해요. 전역 current가 바뀌거나 같은 버전의 bytes가 달라져도 새 규칙을 조용히 적용하지 않아요. Task state의 baseline.command(통상 python3 .forgeflow/run.py --runtime-identity <digest>)로 해당 기준을 계속 실행해요. 여러 task의 기준이 다르면 이 명령의 doc show 또는 baseline.path/spec를 사용하고 프로젝트 기본 spec 링크로 대체하지 않아요.

기준 변경은 영향 검토 후 명시적으로 수행해요.

~~~bash
forgeflow workflow adopt example-fix --reason "기준 변경 이유" --impact "검토한 변경과 영향"
~~~

## 명세와 호환 경로

[공식 명세 색인](docs/spec/README.md)에서 각 계약의 원본을 확인할 수 있어요. docs/spec/가 편집 원본이며 src/forgeflow/spec/는 기계적으로 동기화해요. [개발 흐름](docs/spec/FLOW_SPEC.md), [검증·strict 호환](docs/spec/GATES_AND_LOOPS.md), [배포·기준 고정](docs/spec/DISTRIBUTION_SPEC.md)을 참고해주세요.

기존 release/task/lifecycle 명령과 완료된 strict 증거는 보존해요. strict 경로를 명시적으로 선택하면 package-review → RELEASE_SIGNOFF/manifest 준비 → seal → complete 순서를 따르고, 해당 패키지의 git-sha 또는 sha-free 정책을 유지해요. 패키지 완료는 Git merge를 의미하지 않아요.

## 개발·검증

~~~bash
PYTHONPATH=src python3 -m unittest discover -s tests -p 'test_*.py'
PYTHONPATH=src python3 -m forgeflow.cli --help
~~~

설치 검증은 임시 prefix/bin과 FORGEFLOW_SKILLS_DIR을 지정해 전역 설치를 건드리지 않게 수행해요. 이 저장소의 작업 지침은 [AGENTS.md](AGENTS.md), 현재 진행 상태는 [next-actions.md](docs/session-state/next-actions.md)에 있어요.
