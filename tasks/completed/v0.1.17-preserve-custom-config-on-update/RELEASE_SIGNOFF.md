# Gate 3 Release Sign-off: Preserve Custom Configuration on Update

- **Release ID**: `v0.1.17-preserve-custom-config-on-update`
- **Version**: `0.1.17`
- **Tier**: `Tier 1 (Minor / Fast-track)`
- **Sign-off Date**: 2026-10-27
- **Verdict**: `APPROVED`

## 1. 릴리즈 개요
작업 리포지토리의 거버넌스 설정 파일인 `.forgeflow.json`에서 사용자가 커스텀 수정한 설정(거버넌스 옵션, 커스텀 태스크 디렉터리, 사용자 정의 최상위 메타데이터/플러그인 키 등)이 `forgeflow update` 실행 시 기본 템플릿 값으로 덮어써지지 않고 100% 보존되도록 개선함.
동시에 이미 최신 버전이고 실질적 내용 변경이 없는 경우 불필요한 파일 쓰기를 생략(No-Op)하도록 하여 멱등성을 확보함.

## 2. Gate 완료 확인
- [x] Gate 1: 명세 및 계획된 변경 경로 승인 (`GATE1_REVIEW.md` APPROVED)
- [x] Gate 2: 품질 승인 및 전체 306개 회귀 테스트 100% 통과 (`QA_SIGNOFF.md` APPROVED)
- [x] Gate 3: 릴리즈 패키지 밀봉 및 배포 준비 완료 (`RELEASE_SIGNOFF.md` APPROVED)
