# Setup·배포·runtime 연속성

ForgeFlow는 Python 3.10+ 표준 라이브러리 CLI·공식 spec·templates·생성 skills를 한 배포 단위로 전달합니다. src/forgeflow/_version.py가 버전을, docs/spec/가 공식 spec 편집 원본을 소유합니다. src/forgeflow/spec/는 기계적으로 동기화합니다.

## 설치

install.sh는 ~/.local/share/forgeflow와 ~/.local/bin의 account-local 설치를 지원하며 current는 전역 기본 배포를 가리킵니다. forgeflow upgrade --check는 가용성을 읽고 forgeflow upgrade는 승인된 범위에서 설치합니다.

새 전역 package key는 packages/<version>-<builddigest16>입니다. Metadata의 전체 content_identity는 runtime/spec/templates와 installer/skill-generator 입력을 포함합니다. 버전만으로 다른 bytes를 식별할 수 없습니다. 각 package는 scripts/install-skills.sh도 보관합니다. Install/rollback은 선택한 package generator로 필수 skills를 임시 생성·검사한 후 적용하고 current를 전환합니다. Rollback은 정확한 설치 key를 선택하며 generator가 없는 과거 package는 기존 current/skills를 보존하고 거절합니다. 해당 배포 전체를 명시적으로 재설치해야 합니다. Project runtime snapshot은 installer script를 제외한 별도 runtime content digest를 사용합니다.

scripts/install-skills.sh는 forgeflow/setup-forgeflow/update-forgeflow/forgeflow-graphify를 생성합니다. 테스트는 FORGEFLOW_SKILLS_DIR을 임시 디렉터리로 지정합니다. Npx를 통한 외부 Spec Kit 스킬 설치는 FORGEFLOW_INSTALL_SPECKIT_SKILLS=1 opt-in이며 core dependency가 아닙니다.

## 프로젝트 setup

forgeflow init --speckit은 최소 config·runtime/spec entrypoint와 필요한 Spec Kit support를 구성합니다. 기존 사용자 config·constitution·hooks·templates·지침은 보존합니다. --force가 임의 사용자 문서·증거 폐기를 허용하지 않습니다.

Project workflow.checks에는 실제 프로젝트 검사를 선언합니다. 새 프로젝트의 stack에 맞는 명령을 선택해야 하며 generic Python 명령으로 모든 프로젝트 검증을 대신하지 않습니다. 기본 setup에 대량 ADR/constitution 주입이나 universal strict hook을 요구하지 않습니다.

날짜 기준 폐기·amnesia 정책은 없습니다. 파일 나이는 폐기 근거가 아닙니다. Legacy config를 읽거나 이전할 때 사용자 값을 보존하고 active/completed 작업을 유지합니다.

## 실행 가능한 baseline

Active task는 실제 runtime/spec/templates의 content identity와 로컬 실행 snapshot을 유지합니다.

~~~text
.forgeflow/
  config.json
  workflows/<id>.json
  runtime/<digest>/forgeflow/
  run.py
  spec -> runtime/<digest>/forgeflow/spec/
~~~

Launcher는 global current 대신 pinned runtime을 실행합니다. 다른 설치 bytes가 active 작업에 새 규칙을 조용히 적용할 수 없으며 mismatch는 pinned 명령을 안내합니다. Runtime과 spec은 동일 baseline에 속하고 state 파일은 snapshot과 분리합니다.

Task state의 baseline.command를 사용합니다. 통상 python3 .forgeflow/run.py --runtime-identity <digest> workflow status <id> 형태입니다. 여러 task의 baseline이 다르면 identity 선택 없이 project 기본 launcher만 실행해서는 안 됩니다. Global current가 바뀌어도 해당 snapshot을 실행할 수 있으며 의존하는 active 작업이 있는 동안 보존합니다.

재개할 때는 같은 baseline.command에 doc show FLOW_SPEC 등을 붙여 task 기준의 spec을 읽거나 baseline.path/spec를 확인합니다. .forgeflow/spec는 새 작업/프로젝트 기본 baseline의 편의 링크이며 다른 active task의 기준을 덮어쓰지 않습니다.

명시적 adoption:

~~~text
forgeflow workflow adopt <id> --reason "이유" --impact "변경 및 증거 영향 검토"
~~~

Adoption은 이전/새 identity·이유·영향을 기록합니다. 영향받는 검증을 다시 판단하며 prose/receipt 변경만으로 모든 단계를 반복하지 않습니다. 권한 확대나 완료 strict 패키지 수정은 adoption에 포함되지 않습니다.

## 프로젝트 update

forgeflow update는 호출한 배포 기준으로 통합을 갱신하며 사용자 변경을 보존합니다. Active default workflow·strict package를 조용히 이전하지 않습니다. 보고된 경계는 explicit adoption/completion으로 해소하며 state 삭제로 우회하지 않습니다. finalization_complete인 readiness-only 작업은 완료된 위임 범위로 취급하되 baseline/snapshot은 보존합니다.

update-forgeflow 스킬은 현재 baseline과 요청 범위를 먼저 확인합니다. 전역 upgrade 권한이 있으면 수행하고 허용된 project update를 연결합니다. 새 버전의 존재만으로 active 규칙 변경을 승인받은 것으로 보지 않습니다.

## 전달성 검증

배포 전 spec equality·버전 stamp·fresh generated skills·package data를 확인합니다. Source/새 build entrypoint를 격리 실행하며 과거 설치 CLI로 새 source를 검증했다고 주장하지 않습니다. Installer 테스트는 prefix·bin-dir·FORGEFLOW_SKILLS_DIR 모두 격리합니다. 완료된 historical evidence는 변경하지 않습니다.
