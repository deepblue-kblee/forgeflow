# Gate 3 Release Sign-off: Relocate Configuration to .forgeflow/config.json with Update Migration

- **Release ID**: `v0.1.20-relocate-config-to-forgeflow-dir`
- **Version**: `0.1.20`
- **Tier**: `Tier 3 (Core / Governance Configuration & Implementation Control)`
- **Sign-off Date**: 2026-10-31
- **Verdict**: `APPROVED`

## 1. 릴리즈 개요

프로젝트 루트 디렉터리의 정돈성을 극대화하기 위해, 프로젝트 전역 설정 파일 경로를 루트 `.forgeflow.json`에서 `.forgeflow/config.json`으로 이전함.

하위 버전 프로젝트(`.forgeflow.json`이 루트에 존재하는 프로젝트)에서 `forgeflow update`를 실행하면, 기존 사용자 설정을 100% 보존하면서 `.forgeflow/config.json`으로 자동 마이그레이션하고 루트의 구버전 `.forgeflow.json`은 안전하게 삭제(unlink)하여 최신 프로젝트 레이아웃으로 일원화함.

또한 아직 `forgeflow update`를 수행하지 않은 프로젝트에서도 `ReleaseScanner`, `RuntimeTestRunner`, `SystemDiagnostics`, `resolve_auto_create_branch` 등 모든 엔진이 깨지지 않고 투명하게 하위 호환 폴백(Graceful Fallback) 동작하도록 보장함.

## 2. Gate 완료 확인

- [x] Gate 1: 명세 및 계획된 변경 경로 승인 (`GATE1_REVIEW.md` APPROVED)
- [x] Gate 2: 품질 승인 및 전체 325개 단위/회귀 테스트 100% 통과 (`QA_SIGNOFF.md` APPROVED)
- [x] Gate 3: 릴리즈 패키지 밀봉 및 배포 준비 완료 (`RELEASE_SIGNOFF.md` APPROVED)
