# 구현·전달성 검증

2026-11-02. Python 3.14.6, macOS, source branch codex/lean-development-flow. 이 문서는 관찰된 결과를 기록하며 main 통합을 뜻하지 않습니다.

후속 실제 개발 사이클 검증은 [behavior-verification.md](behavior-verification.md)에 기록했습니다. 설치 CLI에서 실행하는 9개 acceptance tests를 추가했으며, 기존 단일 파일 smoke test와 검증 범위를 구분합니다.

## 결과

| 검사 | 결과 |
| --- | --- |
| 최초 전체 unittest | 415 tests PASS, 93.555초 |
| 실제 개발 사이클 보완 후 전체 unittest | 424 tests PASS, 124.733초; 설치 CLI acceptance 9개 포함 |
| 최종 설치 CLI acceptance 개별 실행 | 9개 PASS, 31.017초; 실제 프로그램·Git·bare remote, 무관한 작업 보존·실패/복구 확인 |
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

후속 424개 검사는 `PYTHONPATH=src python3 -m unittest discover -s tests -p 'test_*.py'`로 실행했습니다. Runtime·parser·기존 strict evidence를 바꾸지 않고 black-box tests와 근거 문서만 추가했습니다. 실제 host 도구/PR와 LLM 자율 수행 pilot의 미검증 범위는 behavior-verification.md에 명시했습니다.

전체 회귀 이후 fixture의 dependency 선언과 동일 prefix의 실제 current 전환 관찰을 강화했으며, 영향받은 acceptance 9개를 최종 재실행했습니다. Runtime이나 나머지 검사의 입력은 바뀌지 않았습니다.

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

구현 commit 8c6197638df6862c71525551b1add38e25ff6438을 origin/codex/lean-development-flow에 push했고 원격 SHA 일치를 확인했습니다. 이후 전달 기록은 같은 branch의 문서 commit에 포함합니다. Main merge·PR 생성·배포·전역 설치·issue #9/#10 종결은 수행하지 않았습니다.
