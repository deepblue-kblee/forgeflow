# Release Notes - {{RELEASE_ID}}

> 사용자와 운영자를 위한 문서입니다. Gate evidence나 승인 근거를 대신하지 않습니다.

## 기능 변화

- 새 기능, 변경된 동작, 제거된 동작을 사용자 관점에서 설명합니다.
- OIDR 트랙 활성화 릴리즈의 경우 PRD의 Applicability Verdict(`supported` 외에는 해결 주장 금지) 및 QA의 Active Target Waiver(`delivery ready; active target unverified`) 클레임 범위를 반드시 준수합니다.

## 사용자 영향

- 사용자 workflow, 호환성, 권한 또는 데이터 영향과 필요한 조치를 설명합니다.

## 운영·업그레이드 유의사항

- 배포 순서, 설정 변경, migration, rollback 및 모니터링 항목을 기록합니다.

## 알려진 제약

- 현재 버전의 제한사항, 미지원 환경, 우회 방법을 기록합니다.

## 근거 문서

- [PRD.md](PRD.md) — 요구사항과 사용자 영향의 근거
- [DESIGN.md](DESIGN.md) — 설계와 호환성 판단의 근거
- [QA_SIGNOFF.md](QA_SIGNOFF.md) — 검증 결과와 sign-off
- [COMPLETION_REPORT.md](COMPLETION_REPORT.md) — 완료 상태와 후속 과제
- [RELEASE_SIGNOFF.md](RELEASE_SIGNOFF.md) — final release package의 사용자 Go/No-Go

## Evidence 경계

Gate 2 이후 이 파일을 포함한 release 문서를 사용자가 정리할 수 있습니다. 이 정리는 `PACKAGE_FINALIZATION`이며 Gate가 아닙니다. 사용자 변경이 없으면 Gate 2 시점 package manifest를 그대로 Gate 3에 사용합니다. Gate 3은 이 파일을 포함한 manifest를 승인하고, 이후 생성되는 Release-Candidate-SHA를 seal합니다.
