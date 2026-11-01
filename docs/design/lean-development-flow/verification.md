# 구현·전달성 검증

2026-11-02. Python 3.14.6, macOS, source branch codex/lean-development-flow. 이 문서는 관찰된 결과를 기록하며 main 통합을 뜻하지 않습니다.

## 결과

| 검사 | 결과 |
| --- | --- |
| 전체 unittest | 415 tests PASS, 93.555초 |
| Legacy strict archive audit | completed package 23개 모두 PASS |
| 최종 installer resource 보완 후 focused suite | test_distribution 11개 PASS, 17.6초 |
| Wheel build | uv isolated build 성공, forgeflow-0.1.25-py3-none-any.whl |
| 실제 wheel 설치 | 임시 venv에 wheel 설치 후 CLI로 init/start/verify/finalize, cleaned·finalization_complete 확인 |
| Account-local installer | prefix/bin/skills 모두 임시 경로로 설치 후 동일 CLI flow, cleaned·finalization_complete 확인 |
| 설치 resource | spec/VERSION, ADR, CHANGELOG, Spec Kit 지원 파일, package generator와 4개 skills 확인 |
| Pinned 문서 조회 | ADR 링크 resolve, snapshot의 CHANGELOG 경로·내용 확인, 다른 project cwd에서도 task spec 유지 |
| 배포 원본 정합 | sync-distribution.py --check PASS |
| Shell/diff | bash -n install.sh scripts/install-skills.sh 및 git diff --check PASS |
| 과거 증거 보존 | tasks/completed·docs/releases에 diff 없음 |
| 독립 최종 심사 | Security/Reliability/Maintainability 모두 APPROVED |

전체 suite는 `PYTHONPATH=src python3 -m forgeflow.cli check --all --strict --json`의 내부 unittest 실행으로 확인했습니다. 개별 archive마다 같은 suite를 반복 실행하지 않습니다. 마지막 CHANGELOG 복사 보완은 installer 전용이며 이후 installer 11개와 실제 전달성 probe를 다시 실행했습니다.

Wheel은 metadata/resource만 검사하지 않고 임시 venv에 실제 설치했습니다. 두 전달 경로에서 scope commit, local --ff-only integration, task branch 삭제와 최종 app 내용까지 관찰했습니다. 테스트 과정에서 새 버전을 전역 CLI/skills에 설치하지 않았습니다.

## 현행 문서·지침 조사 범위

| 표면 | 적용 내용 |
| --- | --- |
| docs/spec 8개 문서·VERSION | lean 기본, 명시적 strict compatibility, 단일 상태·owner·runtime/검증 소유 계약 |
| AGENTS·README·TODO·tasks/README | 실제 실행 명령, 기존 권한 재사용, 완료 보고·세션 연속성 |
| .forgeflow/config.json | 프로젝트 필수 checks·검증 입력·owner·timeout·branch 정책 |
| .specify 현행 constitution/extensions/templates/command | 일괄 strict hook·강제 주입 제거, Spec Kit 위임·기존 사용자 파일 보존 |
| src templates·legacy GOVERNANCE | 기본 진입 지침 정합, strict signoff/manifest 순서의 호환 보존 |
| scripts/install-skills.sh | fresh 생성한 forgeflow/setup/update/graphify skills의 같은 배포 계약 |
| Canonical ADR·배포 복제 | ADR-005로 과거 SHA 금지 적용 범위 명확화, 역사 ADR 본문 보존 |
| docs/session-state | 중복 완료 장부 대신 next-actions checkpoint로 연결 |

존재하지 않는 과거 작업을 가리키던 .specify/feature.json을 삭제했습니다. 날짜를 이유로 과거 evidence나 사용자 자료를 삭제하지 않았습니다. Source spec/ADR/CHANGELOG의 배포 복제는 sync-distribution.py로 생성하고 검사합니다.

## 실행 경계

Standalone 통합은 --ff-only이며 divergence를 자동 해결하지 않습니다. PR은 owner=host에 위임합니다. Host checkout archive는 owning tool의 외부 완료 경계로 남습니다. 검증 입력에서 필요한 dependency를 제외하거나 외부 receipt를 위조해 성공을 보고하지 않습니다.

Main merge·PR 생성·배포·전역 설치·issue #9/#10 종결은 수행하지 않습니다. Commit/push의 관찰 결과는 session checkpoint와 최종 전달에서 별도로 기록합니다.
