# Issue #12 design and final review record

## Design review

세 독립 관점(Security, Reliability, Maintainability)이 `spec.md`/`plan.md` 초안을 검토했고 모두 CHANGES REQUIRED를 반환했습니다. 반영한 핵심 변경:

- active work는 baseline identity와 무관하게 write barrier로 확정.
- `needs-action`/`planned`/`failed-rolled-back`/`partial` invariant와 exit code 확정.
- v0.1.24 exact bytes fixture를 checked-in으로 추가.
- transaction journal, plan drift 재확인, managed backup, `--recover` 추가.
- installer staging/atomic publish, activation rollback, retention 후순위.
- 실제 설치 entrypoint와 metadata/spec/skills 검증.
- custom target 해소와 `--revision` 계약.

## Final review

구현 후 같은 세 관점의 독립 review를 다시 수행했습니다. 지적된 항목과 처리:

| 지적 | 처리 |
| --- | --- |
| recovery가 `.git/**` 등 protected path를 덮어쓸 수 있음 | `_assert_relative_writable` 적용, terminal journal 거부, per-entry error/conflict 보고 |
| recovery가 link entry를 처리하지 못함 | `link` operation과 `symlink_to` 복원, final component 비추적 path resolver 추가 |
| custom prefix를 default HOME으로 해소 | 설치 package 경로에서 prefix 역산, package metadata의 bin/skills target 사용, entrypoint containment 검증 |
| 설치가 없는데 already-up-to-date 성공 | `installed:false` 관찰, non-force upgrade는 비성공, `--force`만 설치 |
| `--revision` raw URL fetch 깨짐 | fetch base에 revision을 유지, clone URL 유도 test 추가 |
| same-version different build 미탐지 | installed `source_revision`/`git_commit`과 resolved revision 비교 |
| dry-run planned exit 1 | `planned` exit 0, planned created/updated/dirs 채움 |
| boot anchor 내부 사용자 수정 삭제 | 현재/legacy template exact match만 교체, 그 외 conflict |
| partial journal이 다음 update를 통과 | `partial`/`unreadable` journal을 pending blocker로 처리 |
| root guide symlink가 generic error | symlink를 구조화 conflict로 보고 |
| baseline target을 apply 중에만 검사 | `preflight_baseline`으로 write 전 blocker |
| activation command 실패 시 rollback 누락 | activation link 실패를 `fail_activation`으로 연결, restore는 best-effort |
| CHANGELOG backup 시점 | prefix CHANGELOG 덮어쓰기를 backup 이후로 이동 |
| 동일 package key active 삭제 | complete package는 재사용, 불완전할 때만 교체 |
| rollback 검증 없음 | package completeness/version 확인과 entrypoint/workflow/skills probe 추가 |
| version path traversal | 안전한 version 문자 집합 검증 |
| partial/failure report에 journal 경로 누락 | `backup_dir`/`migration_record` 포함 |
| strict_mode warning이 human 출력에 없음 | warnings를 human output에 추가, spec에 default 처리 명시 |

남은 한계:

- 실제 GitHub main 이동, branch protection, 다른 OS/Python 3.10 runtime은 이 환경에서 실행하지 않았습니다. Python 3.10 annotation 호환성은 `from __future__ import annotations`와 `get_type_hints` 재현으로 보완했습니다.
- M05/M06/M07의 모든 symlink·host 변형과 U06 retention 실패 주입은 대표 case만 자동화했습니다. 해당 항목은 code path와 기존 distribution test로 보장하며, 전체 matrix를 실행 완료로 주장하지 않습니다.
- installer activation 중 SIGKILL처럼 shell trap이 실행되지 않는 중단은 다음 설치의 staging/완전성 검사로 회복하며, 단일 atomic transaction으로 주장하지 않습니다.
