# Release Sign-off - {{RELEASE_ID}}

> 명시적 strict compatibility 템플릿입니다. 기본 workflow에는 필요하지 않습니다. 패키지의 git-sha/sha-free 정책과 실제 evidence를 기록합니다. Package 완료는 Git merge/cleanup을 뜻하지 않으며 operation 권한은 별도입니다.

> Gate 3의 사용자 Go/No-Go 기록입니다. 구현 품질 재심사가 아니라, Gate 2가 승인한 이후의 최종 release package를 승인합니다.

- **릴리즈 식별자**: `{{RELEASE_ID}}`
- **상태**: PENDING — `PACKAGE_REVIEW_PENDING`

## 검토 대상

- Package manifest SHA-256: `PENDING`
- QA 승인 snapshot: `PENDING` (QA-SHA 또는 SHA-free 무결성)
- 포함 문서: `PRD.md` (또는 `spec.md`), `DESIGN.md` (또는 `plan.md`), `QA_SIGNOFF.md`, `COMPLETION_REPORT.md` (또는 `tasks.md`), `RELEASE_NOTES.md` (존재 시)

## 사용자 판정

- Verdict: `PENDING`
- 승인자: `PENDING`
- 승인 시각: `PENDING`

## ForgeFlow Release Sign-off v1

```text
Release-ID: {{RELEASE_ID}}
Package-Manifest-SHA256: PENDING
Gate-3: PENDING
User-Verdict: PENDING
```
