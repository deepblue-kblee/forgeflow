# Gate 3 Release Sign-off: Support Project-Level Regression Test Timeout

- **Release ID**: `v0.1.18-project-test-timeout`
- **Version**: `0.1.18`
- **Tier**: `Tier 3 (Core / Governance Configuration & Runtime Test Runner)`
- **Sign-off Date**: 2026-10-27
- **Verdict**: `APPROVED`

## 1. 릴리즈 개요

작업 리포지토리의 `.forgeflow.json` 거버넌스 설정에 `governance.test_timeout_seconds` 옵션을 도입하여, 프로젝트별 단위/회귀 테스트 실행 타임아웃을 유연하게 상향 조정할 수 있도록 지원함 (GitHub Issue #6).

대규모 회귀 테스트 스위트를 보유한 프로젝트에서 모든 테스트가 정상 통과함에도 고정 60초 제한으로 인해 가짜 타임아웃이 발생하던 문제를 해결하였으며, 설정이 없는 프로젝트에는 기존 60.0초 제한을 안전하게 유지함. 또한 비정상 설정 값에 대해서는 암묵적 폴백 없이 명확한 `ValueError`로 차단하는 엄격한 유효성 검증 및 `forgeflow doctor` 진단 연동을 완비함.

## 2. Gate 완료 확인

- [x] Gate 1: 명세 및 계획된 변경 경로 승인 (`GATE1_REVIEW.md` APPROVED)
- [x] Gate 2: 품질 승인 및 전체 318개 회귀 테스트 100% 통과 (`QA_SIGNOFF.md` APPROVED)
- [x] Gate 3: 릴리즈 패키지 밀봉 및 배포 준비 완료 (`RELEASE_SIGNOFF.md` APPROVED)
