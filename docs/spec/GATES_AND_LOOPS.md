# 검증·실패 처리 규칙

ForgeFlow 0.2.x의 기본 흐름은 [FLOW_SPEC.md](FLOW_SPEC.md)가 정의합니다. 이 문서는 프로젝트 검증과 실패 처리만 소유합니다.

## 필수 검증

- 프로젝트가 선언한 test/lint/build를 우선 사용합니다.
- `workflow.checks`는 필수이며 task checks는 이를 추가합니다.
- 실제 명령·환경·exit result·관련 content를 기록합니다.
- Task에서 project checks를 제거하거나 결과를 위조할 수 없습니다.
- 변경 동작·실제 연결·사용자가 받는 entrypoint를 확인합니다.
- 코드·환경·통합 결과가 바뀌면 영향받는 검사를 다시 실행합니다.

`workflow verify`는 project/task checks를 실행합니다. 실패하면 state가 `verification-failed`가 되고, 통과 후 입력이 바뀌면 `verification-stale`이 됩니다.

## 실패 처리와 중단

- 실패 원인을 파악하고 관련 수정을 한 뒤 영향받는 검사를 실행합니다.
- 같은 자료 조회와 무변경 명령 반복은 전진이 아닙니다.
- 반복 실패에는 설정된 no-progress budget(통상 5회)을 적용합니다.
- 외부 권한·필수 capability·중대한 사용자 결정이 없으면 해당 단계에서 막힐 수 있습니다.
- 차단 단계와 다음 행동을 기록하고, 실제 재실행 성공 전에는 실패를 통과로 바꾸지 않습니다.

## 선택적 review

`forgeflow review`는 프로젝트가 선택한 경우에만 사용하는 AST 보조 도구입니다.

```bash
forgeflow review --strict
forgeflow review --strict --findings-baseline <ref>
```

- `--strict`: 선택 scope의 Warning 0건
- `--findings-baseline`: Critical 0건과 신규 Warning 0건
- 기존 findings는 표시하며, 관련 없는 기존 Warning 때문에 작은 작업을 전면 refactor로 확대하지 않습니다.
- 프로젝트 필수 checks를 review 결과로 대체할 수 없습니다.

## Content와 dirty 작업

- 관련 없는 dirty 파일은 그대로 둡니다.
- 모든 작업에 global clean status를 강제하지 않습니다.
- 사용자 변경을 몰래 commit/stash/reset하지 않습니다.
- 통합 전 accepted source commit에 검증 입력이 포함됐는지 확인합니다.
- scope 밖 미commit dependency로 PASS한 결과를 그 dependency가 빠진 commit의 성공으로 취급하지 않습니다.

## 과거 strict 경로

0.1.x strict lifecycle/audit은 0.2.x의 선택지가 아닙니다. 과거 완료 증거는 archive tag에서만 확인하며 현행 workflow가 이를 재해석하거나 재승인하지 않습니다.
