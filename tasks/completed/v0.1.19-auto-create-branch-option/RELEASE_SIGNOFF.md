# Gate 3 Release Sign-off: Support auto_create_branch Governance Configuration

- **Release ID**: `v0.1.19-auto-create-branch-option`
- **Version**: `0.1.19`
- **Tier**: `Tier 3 (Core / Governance Configuration & Implementation Control)`
- **Sign-off Date**: 2026-10-31
- **Verdict**: `APPROVED`

## 1. 릴리즈 개요

작업 디렉토리의 `.forgeflow.json` 거버넌스 설정에 `governance.auto_create_branch` 옵션을 도입하여, Stage 3 격리 구현 단계에서 기능 개발용 브랜치(`feat/<release-id>`) 분기 단계를 유연하게 켜고 끌 수 있도록 지원함.

타 AI 도구(Claude Code, OpenCode)나 개발자가 이미 별도의 git worktree 또는 격리 브랜치를 구성해 둔 환경에서 중복 브랜치 생성으로 인해 작업 트리가 복잡해지는 문제를 해소하기 위해 기본값을 `false`(옵션 부재 시에도 `false`)로 설정함. 사용자가 CLI에서 `--create-branch` (`--branch`)를 명시하거나 요청하면 브랜치가 생성되어 작업되며, 향후 프로젝트별 브랜치 정책을 변경할 때 `AGENTS.md` 같은 지침 문서를 오염시키지 않고 `.forgeflow.json`의 본 설정을 단일 진실 공급원(SSOT)으로 삼도록 사양을 확립함.

또한 비불리언 설정에 대한 fail-closed 차단, `forgeflow doctor` 진단 연동, 분기 브랜치 없는 환경에서의 안전한 `lifecycle close` Fast-Path를 완비함.

## 2. Gate 완료 확인

- [x] Gate 1: 명세 및 계획된 변경 경로 승인 (`GATE1_REVIEW.md` APPROVED)
- [x] Gate 2: 품질 승인 및 전체 324개 회귀 테스트 100% 통과 (`QA_SIGNOFF.md` APPROVED)
- [x] Gate 3: 릴리즈 패키지 밀봉 및 배포 준비 완료 (`RELEASE_SIGNOFF.md` APPROVED)
