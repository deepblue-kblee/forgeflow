# Spec Kit 연결 규칙

규모 있는 요구사항·계획·태스크 작업을 Spec Kit에 위임합니다. 작은 작업에는 짧은 계획을 사용할 수 있습니다. Specify/clarify/plan/tasks/implement를 필요에 맞게 사용하며 constitution/analyze도 적절할 때 사용할 수 있습니다. 일괄 제외나 필수 호출 목록을 강제하지 않습니다.

## 로컬 support

forgeflow init --speckit은 누락된 scripts/templates를 구성할 수 있습니다. 기존 project constitution·hooks·command overrides·templates·config는 보존합니다. 기본 setup은 universal 다중 Gate constitution·대량 ADR·필수 AST 검사를 주입하지 않습니다. 날짜만으로 기존 자료를 삭제하지 않습니다.

Support scripts는 명시적 feature state를 해석하고 계획 자산을 만듭니다. 번들 create-new-feature.sh는 독자적으로 Git branch를 만들지 않습니다. Feature identifier는 branch 생성·전환·merge·삭제 권한을 뜻하지 않습니다.

Agreement의 기존 source/owner를 사용합니다. Host-created worktree는 host가 소유하며 Spec Kit feature-name 예시 때문에 새 branch를 만들지 않습니다.

## 선택적 hook

프로젝트가 필요하면 pinned launcher의 forgeflow workflow check <id>에 explicit task ID로 pre-implementation hook을 연결할 수 있습니다. 이는 scope/plan/check agreement를 확인하며 기본 작업에 strict Gate 문서를 요구하지 않습니다.

Strict package는 [호환 전제](GATES_AND_LOOPS.md)에 따라 forgeflow check <id> --stage 2를 의도적으로 유지할 수 있습니다. Strict hook은 그 경로에만 적용됩니다. Tool update가 사용자 hook 교체나 active strict 재해석을 허용하지 않습니다.

## 실행·완료

tasks.md는 구현 진행을 기록합니다. 관찰된 결과에 따라 완료하고 reviewer-owned requirements checklist marker 의미를 보존합니다. Checkbox 변경만으로 동일 구현 검증을 무효화하지 않습니다.

Commit은 권한과 task scope를 따릅니다. Checkbox마다 commit을 강제하거나 실패 시 사용자 작업을 자동 reset/revert하지 않습니다. 진단·수정 후 영향 검사를 실행하고 no-progress stop rule을 적용합니다.

ForgeFlow는 구현 후 검증·허용된 통합·정리까지 조정합니다. Spec Kit command 완료나 strict package seal은 merge/cleanup을 증명하지 않습니다. [FLOW_SPEC.md](FLOW_SPEC.md)가 상태·권한을, [DISTRIBUTION_SPEC.md](DISTRIBUTION_SPEC.md)가 baseline을 소유합니다.
