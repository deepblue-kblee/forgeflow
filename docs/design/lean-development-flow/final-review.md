# 최종 독립 심사

2026-11-02. 대상은 v0.1.25 lean workflow 전환의 구현·현행 지침·배포 계약입니다. 완료된 strict package는 심사 증거 갱신 대상이 아닙니다.

| 심사 | 최종 판정 | 확인 범위 |
| --- | --- | --- |
| Security | APPROVED | Git argv/ref/pathspec, operation authority, project host ownership, scope·receipt 검증, runtime integrity, 정보 보존 |
| Reliability | APPROVED | 검증 freshness·실패 무효화, pinned baseline, update 보존, 통합 재관찰·cleanup 재개, CLI/skill rollback 계약 |
| Maintainability | APPROVED | 현행 문서·생성 지침 정합, task별 baseline 진입, 설치 resource 링크, skill 적용 실패 복구 |

독립 reviewer는 각각 security_review, reliability_review, maintainability_review입니다. 구현 담당 파일을 나누고 다른 소유 경로를 cross-review했습니다. 각 판정은 실제 source와 재현·회귀 검사에 근거하며 전체 suite·delivery 결과는 verification.md에 기록합니다.

## 해소한 findings

- Scope 밖 dirty dependency로 통과한 검증을 그 dependency가 빠진 commit의 통합 증거로 사용할 수 있었음: committed-input guard와 보존 회귀 추가.
- Merge 이후 target rollback을 놓친 채 task branch를 지울 수 있었음: cleanup 직전 accepted source ancestry 재확인.
- Host receipt 경로가 scope 밖 기존 commit을 수용할 수 있었음: pending intent와 receipt 공통 committed-scope 검증.
- Project host 소유권을 standalone agreement로 덮어쓸 수 있었음: start와 finalize의 durable owner 검사.
- 다른 project cwd에서 pinned 명령이 다른 명세를 읽을 수 있었음: 실행 snapshot 자체의 spec을 우선하고 명시적 --path는 유지.
- Rollback이 CLI와 generated skills를 서로 다른 배포로 만들 수 있었음: 선택 package의 generator 보관·복원, generator 없는 legacy package 거절.
- Skill publish 후반 실패가 앞선 파일 교체를 남겼음: destination 전체 사전검사, 임시 파일 rename과 실패 복원. Maintainability가 신규 회귀 3개를 독립 실행해 재확인.
- 배포 spec의 ADR 상대 링크 및 설치 snapshot의 CHANGELOG가 누락됐음: canonical ADR 기계적 복제·package data·installer resource 복사와 실제 설치/pinned 문서 조회 회귀 추가.

필요한 source/dependency를 verification_paths에 선언하는 것은 프로젝트 검증 계약입니다. 임의 filename whitelist를 추가하지 않았으며, 완료 checkbox 등 검증과 무관한 문서만 명시적으로 제외해 유효한 검증을 재사용할 수 있습니다.

추가 blocker는 없습니다. Main merge·전역 설치·배포·issue 종결은 이 심사의 승인 범위에 포함되지 않습니다.
