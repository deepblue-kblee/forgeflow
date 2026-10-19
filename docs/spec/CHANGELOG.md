# 📜 ForgeFlow 개발 플로우 버전 이력 (CHANGELOG.md)

이 문서는 개발 플로우 자체의 표준 규격 및 거버넌스 프레임워크의 변경 이력을 관리합니다.

## [v0.22.1] - 2026-10-19

### Fix AttributeError on forgeflow update Command
- `forgeflow update` (및 `--apply`) 실행 시 `update_parser`에 `--json` 옵션이 누락되어 발생하던 `AttributeError: 'Namespace' object has no attribute 'json'` 오류를 수정했다.
- `update_parser`에 `--json` 플래그를 정식 추가하고, 결과 출력 시 `getattr(parsed, 'json', False)`로 안전하게 접근하도록 방어 코드를 적용했다.
- 프레임워크 패치 버전을 0.22.1로 갱신하고 번들 카탈로그를 동기화했다.

## [v0.22.0] - 2026-10-19

### Root Tasks Architecture, Deterministic Seal Pipeline, Migration Enforcement, and Autonomous Continuation Loop Hardening
- 과거 릴리즈 문서의 구버전 제약이 에이전트의 컨텍스트를 오염시키는 문제를 원천 차단하기 위해, 프로젝트 루트에 순수 작업 영역인 `tasks/` (충돌 시 `ff-tasks/`) 디렉터리와 3단 칸반(`backlog/`, `in-progress/`, `completed/`) 아키텍처를 도입했다.
- `tasks/README.md` 가드 문서를 자동 배치하여 "이 디렉터리는 순수 작업 산출물이며 거버넌스 행동 지침이 일절 포함되어 있지 않음"을 선언하고 에이전트의 규칙 참조를 물리적으로 차단했다.
- 상태 이동(`in-progress` ➔ `completed`), Git 커밋, Candidate 결속 및 Package Seal 순서를 단방향 트랜잭션으로 통제하는 결정론적 Seal 파이프라인을 정립하여 재검증 무한 루프를 제거했다.
- v0.21.0 이하 모든 버전을 마이그레이션 대상으로 선언하고, `forgeflow migrate --tasks` CLI를 제공하여 레거시 `docs/releases/`를 `tasks/completed/`로 안전하게 이동하도록 지원했다.
- 로컬 단일 에이전트(LLM-in-the-loop) 환경에서는 HMAC/nonce attestation이 완전히 면제됨을 정본 스펙 첫머리에 못박고, 사용자의 작업 지시 시 대화형에 멈추지 않고 Loop 2 자가 치유를 완결하는 지침을 배포 템플릿과 정본 스펙에 반영했다.
- 프레임워크 코어 버전을 0.22.0으로 갱신하고 번들 카탈로그 및 표준 명세/템플릿의 바이트 패리티를 100% 동기화했다.

## [v0.21.0] - 2026-10-18

### Mandatory OIDR Trigger Derivation, Structured Fixture-to-RTM Binding, and Artifact-Bound Consumer Delivery Verification
- 조건부 OIDR(Operational Incident and Delivery Readiness) 트랙의 선언적 우회 취약점(Issue #22)을 해결하기 위해, 릴리즈 팩트(인시던트 수정, 공용 표면 변경, 운영 해결 클레임)를 대조하여 OIDR 트랙을 결정론적으로 강제 도출(Deterministic Trigger Derivation)하도록 구현했다.
- 트리거 조건에 해당함에도 `OIDR Track: none`으로 선언하거나 공용 표면 변경 시 `Consumer Surface Declared: no`로 선언하는 우회 시도를 fail-closed로 차단했다.
- Gate 1 `supported` 평결 시 `PROP-<ID> -> FIXTURE-<ID> -> ORACLE-<ID> -> REQ-<ID>`의 4단 정형 구조 매핑을 강제하고, 중복 ID, 누락된 ID, 플레이스홀더 잔존을 엄격히 검출했다.
- Gate 2 소비자 전달 준비성 검증에서 후보 아티팩트 Identity, 64자리 SHA-256 다이제스트, 격리 클린 설치, 비파괴 프로브 커맨드/결과/exit code 0, 소스 체크아웃 누출 차단 및 restricted waiver(`delivery ready; active target unverified`) 정합성을 기계적으로 검증했다.
- 8대 음성 테스트 케이스(Negative tests)를 포함한 종합 회귀 방지 테스트 스위트를 구축했다.
- 프레임워크 코어 버전을 0.21.0으로 갱신하고 번들 카탈로그 및 표준 명세/템플릿의 바이트 패리티를 100% 동기화했다.

## [v0.20.0] - 2026-10-17

### Conditional Operational Incident and Delivery Readiness (OIDR) Track, Gate 1 Incident-Fit, and Gate 2 Consumer Delivery Readiness
- 인시던트 해결을 표방하는 릴리즈가 실제 장애 형상(Shape)을 검증하지 않고 통과하거나, 일회용 격리 환경에만 설치해보고 실제 소비자 엔트리포인트를 검증하지 않는 거버넌스 공백(Issue #20)을 해결하기 위해 조건부 OIDR 트랙을 공식 도입했다.
- **적응형·비례적 거버넌스**: 모든 릴리즈에 불필요한 관료주의를 강제하지 않고, 인시던트 해결(`incident-fix`), 공용 표면 변경(`public-surface-change`), 운영 해결 주장(`operational-claim`) 시에만 OIDR 트랙이 조건부 활성화되도록 트리거 모델을 설계했다.
- **Gate 1 Incident Applicability**: PRD에 정제된(Sanitized) `Incident Brief`, 6대 필수 필드, 프로퍼티 보존 픽스처 매핑, 3대 평결(`supported`, `explicitly-excluded`, `discovery-only`)을 의무화하고, 평결과 모순되는 외부 릴리즈 클레임 표기를 엄격히 차단했다.
- **Gate 2 Consumer Delivery Readiness**: 소스 체크아웃이 아닌 독립된 소비자 설치 환경에서 비파괴 프로브(Non-mutating probe)를 실행하여 런타임 전달성을 입증하도록 했으며, 사용자 관리 활성 대상의 검증이 불가능한 경우 명시적 waiver(`delivery ready; active target unverified`)를 요구했다.
- `src/forgeflow/validator.py`에 OIDR 감사 엔진을 탑재하여 트리거 감지, 누락 필드 검출, 유효/무효 평결 판정, 공용 표면 전달성 프로브 검증, 민감 데이터 유출 방지 필터를 구현했다.
- 프레임워크 코어 버전을 0.20.0으로 갱신하고 번들 카탈로그 및 표준 명세/템플릿의 바이트 패리티를 100% 동기화했다.

## [v0.19.0] - 2026-10-17

### Autonomous Loop Specification, True vs False Stopping Rules, Supervisor-Worker Protocol, and Template Stale Attestation Sanitization
- AI 에이전트의 대화 편향(Conversational Bias)으로 인한 조기 턴 종료(Early Turn-Stop)를 원천 차단하기 위해, 자율 실행 모드(`continuation_policy="autonomous"`)의 4단계 불변 루프(`Dispatch` ➔ `Verify` ➔ `Evaluate & Remediate` ➔ `Completion Guard`)를 공식 표준화했다.
- 에이전트가 절대로 멈추지 않고 즉시 Loop 2 자가 치유를 연속 실행해야 하는 가짜 멈춤(Non-Stop: 테스트 실패, 리뷰어 REJECT, 픽스처 누락)과 오직 사용자 지시를 대기해야 하는 진짜 멈춤(True Stop: 동일 실패 5회 서킷 브레이커, 권한 경계, 아키텍처 모순, Gate 3 사용자 릴리즈 대기)을 대조하는 흑백 체크리스트를 규격화했다.
- 메인 에이전트(Supervisor)의 상태·장부·충돌 관리와 워커 에이전트(Worker)의 관심사별 파일 경로 격리(`File-Path Partitioning`) 및 순차 병합 통제를 명시한 Supervisor-Worker 다중 에이전트 오케스트레이션 프로토콜을 명문화했다.
- 이식형 거버넌스 템플릿(`src/forgeflow/templates/GOVERNANCE.md`)에서 0.16.x 구버전 잔재인 `valid activation attestation` 요구 문구를 제거하고 경량 durable loop record 규격과 루트 `AGENTS.md` 제6조의 `Completion Integrity (미완료 Gate 종료 금지)` 규범을 이식했다.
- 프레임워크 코어 버전을 0.19.0으로 갱신하고 번들 카탈로그 및 표준 명세/템플릿의 바이트 패리티를 동기화했다.

## [v0.18.0] - 2026-10-17

### Multi-User Distribution Architecture, install.sh Script, and Harness CLI Consolidation into forgeflow check
- 개발자 로컬 가상환경 종속성을 분리하고 단일 머신의 모든 사용자 계정(`jarvis`, `deepblue` 등)이 공용 접근 가능한 `/opt/forgeflow` 표준 배포 아키텍처(`docs/spec/DISTRIBUTION_SPEC.md`)를 수립했다.
- `packages/<version>` 디렉토리에 버전별 패키지를 누적 보관하고, `current` 심볼릭 링크(`ln -sfn`)를 통해 활성 버전을 무중단 원자적으로 전환하는 배포 메커니즘을 구현했다.
- 저장소 루트에서 원클릭으로 호출 가능한 배포 스크립트(`install.sh`)를 제공하여 소스 복사, standalone 격리 런처(`bin/forgeflow`) 생성, 전역 PATH(`/usr/local/bin`) 심볼릭 링크 연결, 버전 보관(`--keep`), 롤백(`--rollback`), 드라이런(`--dry-run`)을 표준화했다.
- 방법론적 명칭으로 분산되어 있던 `harness` 실행 명령을 상위 도구인 `forgeflow check` 및 `forgeflow review`로 완전 흡수 통합하고, 기존 자동화 스크립트 호환을 위해 `bin/harness` 심볼릭 링크 및 하위 호환 래퍼를 유지했다.
- `validator.py`의 `SelfGovernanceValidator.CORE_FILES`에 `install.sh`를 등록하여 자체 거버넌스 감시 대상으로 승격했다.
- 프레임워크 코어 버전을 0.18.0으로 갱신하고 번들 카탈로그 및 표준 명세/템플릿의 바이트 패리티를 동기화했다.

## [v0.17.0] - 2026-10-17

### Decouple Autonomous Continuation from Attestation, Lightweight Durable Remediation Loop, and Deterministic Failure Fingerprinting
- `lifecycle.py`에서 `continuation_policy="autonomous"` 활성화 시 무거운 암호학적 서명 증명(`ActivationAttestation`) 없이도 로컬 파일 시스템 기반의 경량 자율 수명주기 및 `control.loop_record`를 초기화할 수 있도록 정책과 Tier를 직교화했다.
- `lifecycle.py`에 `record_remediation`, `resolve_remediation`, `get_loop_record` 메서드를 추가하여 시도 횟수(`attempt_count`), 동일 결함 무진전 카운터(`no_progress_count`), 최대 버짓(5회), 정형화된 지적사항 목록(`remediations`), 최신 판정을 영속 관리하도록 구현했다.
- `harness.py`에 타임스탬프, UUID, 임시 디렉터리 경로(`/tmp/...`), 메모리 주소(`0xADDR`)를 정규화하여 일관된 SHA-256 해시를 산출하는 결정론적 failure fingerprint 알고리즘(`compute_failure_fingerprint`)을 구현했다.
- `harness.py`의 `lifecycle_complete` 및 `_validate_lifecycle_state_for_audit`에 미해결 지적사항(`status="OPEN"`)이나 REJECT/FAIL 판정이 남아있는 경우 최종 완료로의 불법 전이를 차단(`unresolved_remediation_active`)하는 거버넌스 가드레일을 구축했다.
- `reviewer.py`의 `ReviewResult`에 정적 코드 스멜을 정형화된 remediation 목록으로 변환하는 `to_remediations()` 메서드를 구현했다.
- `cli.py`의 `lifecycle` 서브커맨드에 지적사항 기록 및 해결을 지원하는 `remediate` 명령을 추가했다.
- 프레임워크 코어 버전을 0.17.0으로 갱신하고 표준 명세 및 템플릿의 바이트 패리티를 동기화했다.

## [v0.16.1] - 2026-10-17

### Lifecycle State Idempotency, Candidate Diff Path Alignment, CLI Flexibility, and Code Hygiene
- `lifecycle.py`의 `mark_package_review_pending` 및 `seal_package`가 이미 대상 상태일 때 `TransitionError`를 발생시키지 않고 식별자(QA-SHA, Candidate SHA, Package Manifest)를 원자적으로 갱신하는 멱등적 상태 전이를 지원했다.
- `harness.py`의 `_candidate_disallowed_paths` 허용 경로(`allowed`)에 `ROADMAP.md`를 추가하여, QA Sign-off 이후 릴리즈 체크리스트 문서가 갱신되어도 `release_candidate_range_invalid` 오류 없이 씰링을 정상 완료하도록 보장했다.
- `cli.py`의 `package-review` 및 `seal` 명령어에서 위치 인자(`<qa-sha>`, `<candidate-sha>`)와 플래그(`--qa-sha`, `--release-candidate-sha`)를 모두 유연하게 수용하도록 파서와 핸들러를 개선하고 `README.md` 가이드에 명시했다.
- `validator.py`의 4대 산출물 파서 반환 타입 어노테이션에서 파이썬 내장 소문자 `any`를 `typing.Any`로 표준화했다.
- `update.py` 내 미사용 데드 코드 상수 `UPGRADEABLE_VERSIONS`를 제거했다.
- 프레임워크 코어 버전을 0.16.1로 갱신하고 번들 카탈로그 및 표준 명세/템플릿의 바이트 패리티를 동기화했다.

## [v0.16.0] - 2026-10-17

### Code Review Engine Enhancement (Multi-Axis AST Smells, Security Patterns, Incremental Cache, Fail-Closed Pipeline)
- `smell_detector.py`에 루프 내부 디스크 I/O 호출(`I/O in Loop`), 모듈 결합도 및 과다 임포트(`Excessive Imports` > 20), 미사용 임포트(`Unused Import`)를 정적 AST 레벨에서 감지하는 다축 복합 지표 룰셋을 도입했다.
- `smell_detector.py`에 예외 묵살(`Silent Exception`: except 블록의 pass/ellipsis), 보안 취약 패턴(`Security Vulnerability`: `subprocess` shell=True, `eval()`, `exec()`, `tempfile.mktemp()`), 파이썬 내장 빌트인 식별자 재정의(`Builtin Shadowing`) 패턴 매칭 규칙을 구현했다.
- `review_cache.py`에 파일 내용 SHA-256 다이제스트 기반의 증분 리뷰 체크포인트 캐시(`ReviewCacheManager`)를 구현하여 변경되지 않은 소스 파일의 불필요한 AST 재파싱을 건너뛰고 O(1) 캐시 히트 성능을 확보했다.
- `reviewer.py`의 `ReviewEngine`과 `cli.py`에 증분 캐시 연동, `--no-cache`, `--fail-on-warning` 플래그 및 구문/인코딩/보안 취약점 검출 시 즉시 검증 실패 처리하는 Fail-Closed 파이프라인을 확립했다.
- 프레임워크 코어 버전을 0.16.0으로 갱신하고 표준 명세 및 템플릿의 바이트 패리티를 동기화했다.

## [v0.15.0] - 2026-10-17

### Core Defect Remediation, Scanner Semantics, Performance Caching, and Spec Alignment
- `scanner.py`의 릴리즈 디렉터리 정렬 방식을 사전식 문자열 비교에서 세맨틱 버전 숫자 튜플(`(major, minor, patch)`) 정렬 키(`_release_sort_key`)로 교체하여, `v0.10.0` 이상의 릴리즈가 `v0.9.0`보다 과거로 역전 정렬되던 P1 버그를 해결했다.
- `issue.py`에서 콜드 스타트 상태(캐시 미존재)에서 `close` 호출 시 로컬 캐시가 빈 상태로 덮어써져 이슈 목록이 영구 유실되던 문제를 원격 사전 조회(`view(refresh=True)`) 및 원자적 캐시 무효화를 통해 해결했다.
- `validator.py`에서 Tier 1 릴리즈의 단일 산출물 규격(`CHANGE_NOTE.md`)을 지원하도록 `TierRules.get_required_docs` 및 `DocumentIntegrityValidator`에 분기를 추가하고 타입 힌트를 정합화했다.
- `smell_detector.py`에서 비UTF-8 바이너리 파일 순회 중 발생하는 `UnicodeDecodeError`를 조용히 묵살(silent pass)하지 않고 Fail-Closed 원칙에 따라 `CRITICAL` 심각도의 `Encoding Error` 결함으로 명시 보고하도록 개선했다.
- `catalog_oracles/__init__.py`의 `_load_verified_oracle_bundle`에 `@lru_cache`를 적용하여 매 호출 시 번들 압축 해제 및 디코딩이 2회 중복 실행되던 성능 오버헤드를 제거했다.
- `diagnostics.py`의 `generate_doctor_report` 내 `session.jsonl` 중복 I/O를 1회 캐싱으로 개선하고, streak 지속 시 Anomaly가 이벤트마다 중복 누적되던 현상을 방지했다.
- `harness.py` 내 미사용 데드 코드(`_normalize_stage`, `_lifecycle_status_payload`) 및 미사용 import를 정리하고, `runner.py`의 소문자 `any` 타입 힌트를 `Any`로 수정했다.
- `cli.py`의 `check_parser` 및 `forgeflow check`에 `--self-governance`, `--release-id`, `--base`, `--python` 옵션을 연동하여 `harness check`와의 CLI 옵션 정합성을 일치시켰다.
- `README.md`, `lifecycle-adapters.md`, `AGENTS.md`, `TODO.md`의 미존재 CLI 명령(`qa-signoff`, `release-signoff`), Evidence v2/Schema 2 규격, 5대 필수 산출물 명칭을 최신 표준으로 정합화했다.
- 프레임워크 코어 버전을 0.15.0으로 갱신하고 표준 명세 및 템플릿의 바이트 패리티를 동기화했다.

## [v0.14.0] - 2026-10-16

### Spec Modernization, Circuit Breaker, Diagnostic Guidance, and Audit Optimization
- Gate 1 Loop 1(설계 반복) 상한을 최대 5회로 표준화하고, 5회 도달 시 무한 루프를 방지하는 명시적 `PENDING` 서킷 브레이커 상태 머신을 규격화했다 (Issue #15).
- Gate 2 QA Evidence v2 파싱 실패 시 원시 파싱 토큰 대신 기대 블록 형식과 누락 필드를 안내하는 친절한 에러 진단 가이드와 next_action을 제공하고, Tier 2(1인 이상) 및 Tier 3(3대 관점) 동적 검증을 지원하도록 개선했다 (Issue #16).
- 과거 규격 잔재 전수 조사 결과를 반영하여 스펙 헤더 버전 정합화(v0.14.0), 디렉토리 구조도 최신화(`harness_check.py` 제거), Hermes 전용 하드코딩 경로 제거, 3대 독립 관점 용어(Security, Reliability, Maintainability) 통일, Lifecycle Schema Version 2 동기화를 완료했다.
- 표준 템플릿의 잔재를 정비하여 `DESIGN.md`에 Gate 1 심사 표를 공식 탑재하고, `ROADMAP.md`를 5-Stage 수명주기 체크리스트로 개편했으며, `QA_SIGNOFF.md`의 Tier 메타데이터를 동적 템플릿화했다.
- 검증 성능 최적화로서 `lifecycle_seal`의 중복 Git diff/ancestor 호출을 제거하여 서브프로세스 오버헤드를 절감하고, clean working tree 상태에서 불필요한 전체 소스 강제 스캔을 방지하도록 `reviewer`에 조기 탈출(bailout)을 적용했다.
- 프레임워크 코어 버전을 0.14.0으로 갱신하고 표준 명세 및 템플릿의 바이트 패리티를 동기화했다.

## [v0.13.0] - 2026-10-16

### Gate 3 Seal Integrity, Post-Candidate Evidence Descendance, and State Clarity
- `_candidate_disallowed_paths`에서 `HEAD`가 `candidate` 커밋과 일치하거나 직계 자손(Descendant)인 경우를 지원하여, 완료 후 라이프사이클 증적(`.forgeflow/lifecycle/<release>.json`)을 커밋한 클린 워크트리에서도 `check --lifecycle --strict`가 안정적으로 통과하도록 고정점 불가능성 결함을 해결했다 (Issue #14).
- `lifecycle_seal` 시점에 `RELEASE_SIGNOFF.md` 파일의 존재, 파싱, `Gate-3: APPROVED`, `User-Verdict: GO`, 패키지 매니페스트 SHA-256 일치 여부를 필수 검증하도록 강제하여 무승인 씰링을 차단했다.
- `package-review` 및 `seal` 사전 검증 단계에 필수 산출물(`DESIGN.md`, `COMPLETION_REPORT.md` 등) 구조 무결성 검증(`_check_package_artifacts_integrity`)을 도입하여 불완전한 상태에서의 승인 요청을 사전 차단했다.
- 패키지 씰 완료 상태를 명확히 표현하기 위해 `Status.PACKAGE_SEALED`를 도입하고 상태 머신 전이 규칙을 정비하여, `PACKAGE_REVIEW_PENDING`으로의 오판 및 루프 반복을 방지했다.
- 씰 완료 후 패키지 아티팩트 수정 시 씰 상태와 Gate 3 바인딩을 자동으로 무효화(`unseal_package`)하고 재검토 단계로 복구하는 자기 치유 메커니즘을 구축했다.
- `FLOW_SPEC.md`의 Feature close 명세와 실제 `lifecycle_close` 구현의 브랜치 정리 책임을 일치시켰다.
- 프레임워크 코어 버전을 0.13.0으로 갱신하고 표준 명세 및 번들 카탈로그를 동기화했다.

## [v0.12.0] - 2026-10-11

### Flexible Gate 2 Evidence Validation and Branch Cross-Binding
- Gate 2 Evidence v2 검증기에서 `Stage`가 `PACKAGE_REVIEW_PENDING`일 때 `Next-Action`으로 `RELEASE_SIGNOFF`뿐만 아니라 `PACKAGE_REVIEW`도 자연스럽게 수용하도록 유연화했다 (Issue #13).
- `Task-Branch` 접두사 제약을 완화하여 `codex/`를 포함한 안전하고 표준적인 Git 브랜치 명명 규칙을 지원하도록 확장했다.
- 리뷰어 수를 정확히 3인으로 제한하던 제약을 완화하여, 필수 3대 관점(Security, Reliability, Maintainability)을 포함하는 3인 이상의 다수 리뷰어를 수용하고 lifecycle state evidence에 구조화된 형태로 보존하도록 개선했다.
- `Verification` 증적 라인에 옵셔널 `output-digest` 및 `digest` 키 지원을 추가하여 테스트 플랜 및 템플릿 규격과의 일치성을 확보했다.
- `lifecycle package-review` 수행 시 lifecycle control state의 브랜치와 증적의 `Task-Branch`를 상호 교차 검증하여 상태 변조를 차단하는 fail-closed 무결성을 강화했다.
- 프레임워크 코어 버전을 0.12.0으로 갱신하고 표준 명세(`FLOW_SPEC.md`) 및 번들 카탈로그를 동기화했다.

## [v0.11.0] - 2026-10-11

### Simplified Governance Bundle Update and Catalog Modernization
- `forgeflow update`에서 과거 마크다운 전체 텍스트를 대조하던 경직된 바이트 단위 오라클 비교 및 가짜 drift 블로커를 폐지했다 (Issue #12).
- `.forgeflow.json`의 버전 및 디렉터리 안전성 검증 기반으로 `upgrade_available`을 판정하고, 기존 저널 트랜잭션(`_apply_governance_transaction`)을 통해 최신 표준 번들로 원자적 동기화하도록 단순화했다.
- 프레임워크 릴리즈 누적에 따른 소스 비대화와 오라클 누락 부채를 해소하기 위해 `bundle_catalog` 및 오라클 아키텍처를 경량화했다.
- 프레임워크 코어 버전을 0.11.0으로 갱신하고 표준 명세(`FLOW_SPEC.md`)를 동기화했다.

## [v0.10.1] - 2026-10-11

### Root Documentation Modernization and CLI Reference Sync
- 루트 `README.md`에 최신 프레임워크 기능(`forgeflow doctor`, `forgeflow issue`, `forgeflow lifecycle`, `forgeflow review`, AST 기반 리팩토링 가드레일) 및 전체 CLI 서브커맨드 레퍼런스를 전면 반영했다 (Issue #11).
- 설치 및 빠른 시작 가이드에서 하드코딩된 구 개발자 로컬 경로를 표준 범용 경로(`~/work/repo/forgeflow`)로 교체하고, 최신 모듈 구성에 맞게 디렉토리 구조도를 최신화했다.
- 프레임워크 코어 버전 0.10.1 패치 갱신 및 카탈로그 동기화를 완료했다.

## [v0.10.0] - 2026-10-09

### Field Diagnostics Telemetry and Doctor CLI
- 외부 SaaS 전송 없이 100% 로컬(`.forgeflow/diagnostics/session.jsonl`)에서 동작하는 비침습적 진단 로깅 엔진(`DiagnosticLogger`)을 도입했다 (Issue #5).
- 소스 코드, 커밋 diff, 환경 변수 등 민감 정보를 원천 필터링(Zero Data Leak)하고 상태 전이 및 성능 메타데이터만을 안전하게 수집한다.
- 대표적 안티패턴(3회 이상 연속 실패 루프, 중복 회귀 검증, 60초 이상 고지연)을 정량 식별하는 이상 탐지 엔진(`DiagnosticAnalyzer`)을 구축했다.
- `forgeflow doctor` (별칭 `diagnose`) CLI 명령어를 신설하여 저장소 상태 진단 리포트를 출력하고, `--report-issue` 옵션으로 GitHub Issue 마크다운 초안을 자동 생성할 수 있도록 지원했다.

## [v0.9.0] - 2026-10-09

### Deep Module Refactoring Guardrail and AST Cognitive Complexity Analyzer
- John Ousterhout의 Deep Module 철학 및 SonarSource 모델 기반으로 파일 크기(LOC) 및 함수별 인지 복잡도(Cognitive Complexity)를 정밀 측정하는 Zero-Dependency AST 분석기를 도입했다 (Issue #3).
- 모듈 레벨 500 LOC 초과 시 Soft Warning, 800 LOC 초과 시 Critical God Module 경고를 검출하며, 함수별 인지 복잡도 15점 초과 시 High Cognitive Complexity 경고를 검출한다.
- `forgeflow review` 및 `ReportRenderer`에 Early Return(Guard Clause), Subroutine Extraction, Subpackage Promotion 등 실용적 리팩토링 권장 사항 및 메트릭 요약을 연동했다.
- `harness check --strict` 실행 시 변경 소스 중 800 LOC 초과 파일이 존재할 경우, Gate 산출물(`DESIGN.md` 등) 내 `Architecture Exception` 명시적 사유 기록이 없으면 하네스 게이트를 불합격 처리하는 엄격 가드레일을 구축했다.
- 공식 표준 리팩토링 가이드 문서(`REFACTORING_GUIDE.md`)를 제정하고 포터블 템플릿과 100% 동기화했다.

## [v0.8.2] - 2026-10-09

### Candidate Runtime Lock Bypass and Worktree Lifecycle Invariants
- Gate 3 후보 커밋 diff(`_has_v2_candidate_binding`) 검증 시 `.forgeflow/lifecycle/` 런타임 락 파일(`*.lock`)을 패키지 증적 위반 대상에서 자동 배제하고, 불허 경로 발생 시 진단 목록(`Disallowed paths`)을 명시하여 Gate 3 봉인 거부 문제를 해결했다 (Issue #10).
- `forgeflow lifecycle close` 실행 시 `git worktree list --porcelain` 기반으로 타 worktree의 task branch 점유 여부를 식별하여 안전하게 fail-closed 처리하고, detached HEAD 상태 감지 및 Post-close branch invariant(`main` 브랜치 정렬 및 clean 상태)를 보장했다 (Issue #9).

## [v0.8.1] - 2026-10-06

### Lifecycle Close Command and Self-Governance Early Bailout
- `forgeflow lifecycle close <release-id>` 커맨드를 도입하여 완료된(`COMPLETE`) 릴리즈의 상태 확인 및 잔여 격리 작업 브랜치(`feat/<release-id>`) 안전 삭제(`git branch -d`)를 0.1초 내에 수행하는 Fast-Path를 구축했다.
- 이미 완료된 릴리즈에 대해 `check --self-governance` 호출 시 불필요한 재검사를 조기 차단(Early Bailout)하는 가드레일을 `SelfGovernanceValidator`에 추가했다.
- `src/forgeflow/templates/GOVERNANCE.md` 및 `spec/FLOW_SPEC.md`에 완료 후 과잉 재검증 금지 규범 및 Fast-Path 표준을 공식 탑재했다.

## [v0.8.0] - 2026-10-06

### Incremental Audit Optimization and Release Boundary Resolution
- `check --all` 실행 시 Git diff/status상 변경되지 않은 과거 완료(`COMPLETE`) 아카이브 릴리즈는 문서 파싱을 건너뛰는 증분 감사(Incremental Audit) 엔진 및 컴팩트 1줄 요약 출력을 도입했다.
- `ReleaseScanner.get_latest_release`에 최신 버전 명명 역순 정렬 기반 조기 종료(Early-exit)를 적용하고, `ReviewScanner`에 `os.walk` 디렉토리 가지치기 안전 가드레일을 적용했다.
- QA-SHA 이후 릴리즈 패키지 결속 범위(`_has_v2_candidate_binding` 및 `_has_candidate_binding`)에 `.forgeflow/lifecycle/{release_id}.json` 및 `docs/session-state/**`를 공식 허용 경로로 완전히 확정하여 외부 채택 저장소와의 릴리즈 봉인(Seal) 경계 충돌을 해결했다.
- `SelfGovernanceValidator`에 `.forgeflow/` 경로를 `repository-state`로 분류하여 자체 거버넌스 감사 호환성을 확보했다.

## [v0.7.1] - 2026-10-06

### Lifecycle Idempotency and Audit Redundancy Fix
- `forgeflow lifecycle complete` 시 이전 엄격 감사(strict audit) 통과 증적과 동일한 candidate/manifest/clean-worktree 상태일 경우 전체 회귀 테스트 재실행을 건너뛰는 지능형 감사 캐시를 도입했다.
- `package-review`, `seal`, `complete` 수명주기 전이에 멱등성(idempotency)을 부여하여 이미 목표 상태인 경우 원시 예외 대신 현재 상태를 안전하게 반환하도록 개선했다.
- `_has_v2_candidate_binding` 경로 검증 allowlist에 `.forgeflow/lifecycle/{release_id}.json` 및 `docs/session-state/` 경로를 허용하여 수명주기 상태 변경 커밋과의 충돌을 방지했다.
- CLI 수명주기 예외 처리에서 `TransitionError`, `ValidationError`, `CASConflict`를 구조화된 JSON 에러로 포획하도록 개선했다.

## [v0.7.0] - 2026-10-06

### First-Class Issue Command in ForgeFlow CLI
- `forgeflow issue` 서브커맨드를 1급(first-class) 명령어로 코어 CLI에 공식 통합했다.
- `forgeflow issue --title "..." --body "..."` 형태의 기본 생성(shortcut create)과 `create`, `list`, `view`, `edit`, `close`, `delete` 하위 명령어를 지원한다.
- Zero-Dependency 원칙(표준 라이브러리 및 `gh` CLI)과 `.cache/issues/` 로컬-퍼스트 캐싱 엔진을 코어 모듈(`src/forgeflow/issue.py`)로 승격했다.

## [v0.6.0] - 2026-10-05

### QA and Release Sign-off separation
- Gate 2를 `QA Sign-off`로 정의하고 QA-SHA의 automated verification 및 Security/Reliability/Maintainability technical review를 분리했다.
- Gate 2 뒤 선택적 `PACKAGE_FINALIZATION`, Gate 3 `Release Sign-off`, Release-Candidate-SHA, Package Seal, `COMPLETE`, Feature Close의 순서를 명시했다.
- `RELEASE_SIGNOFF.md`, Evidence v2, Lifecycle State Schema 2와 package-manifest strict audit을 도입하고, historical Evidence v1 audit을 유지했다.

## [v0.4.8] - 2026-10-03

### User-facing Release Notes artifact
- 새 release scaffold에 `RELEASE_NOTES.md`를 추가하고 사용자·운영자 문서의 역할을 정의했다.
- Evidence v1 core artifact와 strict lifecycle audit은 기존 exact four artifact만 검사하도록 경계를 명확히 했다.

## [v0.4.7] - 2026-10-01

### Autonomous guidance consolidation
- autonomous continuation의 상세 정책과 Tier 분류 규칙을 `GATES_AND_LOOPS.md` 단일 원본으로 통합했다.

## [v0.4.2] - 2026-09-29

### Automatic-mode continuation guidance
- “자동 모드”를 `autonomous`의 명시적 완료 위임 표현으로 추가하고, `Go`·`계속`은 이미 활성화된 lifecycle의 재개 신호로 한정했다.
- autonomous lifecycle owner의 wait → evaluate → self-resolvable remediation 규칙과 final-response/authority boundary를 portable guidance로 명확히 했다.

## [v0.3.9] - 2026-09-29

### Selectable autonomous continuation policy
- 기본 interactive workflow를 유지하면서 explicit completion delegation에만 autonomous user-proxy lifecycle owner와 portable logical sub-agent hierarchy를 추가했다.
- product runtime state를 도입하지 않고, host별 delegation은 portable operating guidance로 유지한다.

## [v0.3.8] - 2026-09-29

### Lifecycle Completion Integrity
- agent runtime state transition 대신 canonical release artifact의 evidence completeness를 읽는 harness contract를 규격화했다.
- completion readiness는 Gate 1/2, Tier별 independent reviewer, branch/base에 결속된 candidate SHA verification, current artifact와 strict regression을 요구한다.
- `harness check --lifecycle <release-id> --strict --json`을 portable audit contract에 추가했다. 이 audit은 자연어 approval이나 transient agent state를 Gate evidence로 해석하지 않는다.

## [v0.1.0] - 2026-08-29

### 기계적 게이트 자동화 하네스 CLI 탑재 (Automated Gate Harness Release)
- **하네스 CLI 도구(`harness check`) 공식 배포**:
  - 릴리즈 필수 4종 문서(`PRD`, `DESIGN`, `QA_SIGNOFF`, `COMPLETION_REPORT`) 및 내부 필수 키워드/섹션 기계적 자동 전수 검사 엔진 구축.
  - 전역 실행 파일 [~/.local/bin/harness](file:///Users/jarvis/.local/bin/harness) 심볼릭 링크 연결.
  - 단일 릴리즈 검사, `--all` 전체 일괄 검사, `--json` 구조화 리포트, `--strict` 모드 및 신호등(🟢/🟡/🔴) 뷰 지원.
  - 런타임 회귀 테스트 스위트 결합 러너(`-t`/`--run-tests`) 연동.
- **독립 전문가 n인 병렬 패널 심사 모델 (Parallel Independent Panel Review) 확립**:
  - 에이전트 간 핑퐁식 토론/회의 오버헤드를 전면 배제하고, 동일한 전문성을 가진 독립 심사관 n인에게 1회성 병렬 자문(Fan-Out) ➔ 피드백 취합(Fan-In) ➔ 사령관 단독 결단 메커니즘을 Gate 1(기획) 및 Gate 2(QA)에 공식 표준화.
- **거버넌스 프레임워크 승격**:
  - 단순 텍스트 가이드라인 단계(`v0.0.x`)에서, 기계적 실행 바이너리를 갖춘 정식 마이너 프레임워크(`v0.1.0`)로 공식 승격.

---

## [v0.0.2] - 2026-08-29

### 위험도 기반 동적 검증 티어링 체계 도입 (Dynamic Verification Tiering)
- **3단계 검증 티어링 매트릭스 (Tiering Matrix) 수립**:
  - **Tier 1 (Minor)**: 50줄 미만 단순 패치/문서 수정은 Linter 및 단위 테스트 100% Pass 시 메인 에이전트 단독 검증/승격 (Zero-Subagent, 오버헤드 최소화).
  - **Tier 2 (Standard)**: 50~300줄 규모 일반 기능은 독립 QA 서브에이전트 1인이 요구사항 매핑 및 테스트 결과를 심사하여 서명.
  - **Tier 3 (Critical)**: 보안/인증, 코어 데몬, 다자 인터페이스 변경 시 사전(Gate 1) 및 사후(Gate 2) 2~3인 서브에이전트 교차 검증 및 전원 합의 의무화.
- **고밀도 경량 검증 컨텍스트 프로토콜 (Lightweight Context Protocol)**:
  - 교차 검증 시 프로젝트 전체 코드 대신 `Git Diff`, `테스트 실행 로그`, `요구사항 매핑표(RTM)`의 3대 핵심 아티팩트만 주입하여 토큰 소모량 80% 이상 절감.
- **규격 문서 동기화**:
  - [FLOW_SPEC.md](file:///Users/jarvis/work/repo/openclaw-env-helper/docs/framework/flow/FLOW_SPEC.md) 및 [GATES_AND_LOOPS.md](file:///Users/jarvis/work/repo/openclaw-env-helper/docs/framework/flow/GATES_AND_LOOPS.md)에 동적 게이트 및 검증 절차 반영.

---

## [v0.0.1] - 2026-08-28

### 최초 실험 기준 제정 (Experimental Baseline Release)
- **버전 정책 수립**:
  - `v0.0.1`부터 시작하여 실전 태스크 수행을 통해 점진적으로 버전을 고도화.
  - 정식 `v1.0.0` 승격은 사용자의 명시적 승인 및 지시가 있을 때 릴리즈하도록 규정.
- **도메인 3단계 격리 체계 확립**:
  - `Framework Domain` (`docs/framework/flow/`): 플로우 표준 규격 및 거버넌스 규칙
  - `Release Domain` (`docs/releases/<release-id>/`): 기획(PRD), 설계(DESIGN), 검증(QA_SIGNOFF), 완료보고(COMPLETION_REPORT)
  - `Workspace Domain` (`workspaces/task-<release-id>/`): 코드 격리 개발 및 테스트 공간
- **2대 핵심 게이트 & 완료 보고서 의무화**:
  - `Gate 1 (Pre-Implementation Gate)`: 3인 서브에이전트 2회 교차 심사 게이트
  - `Gate 2 (Release Sign-off Gate)`: 요구사항 100% 충족 QA Sign-off 및 `COMPLETION_REPORT.md`(미완/개선점 포함) 제출 의무화
- **자가 치유 3대 순환 루프 및 정량적 서킷 브레이커 탑재**:
  - Loop 1 (설계 검증 3회 상한), Loop 2 (코드 자가수정 5회 상한), Loop 3 (아키텍처 회귀 2회 상한)
- **표준 운영 프로토콜 및 산출물 템플릿 완성**:
  - `QA_SIGNOFF.md` 및 `COMPLETION_REPORT.md` 표준 템플릿 제정
  - 5단계 라이프사이클 2차원 RACI 매트릭스 수립
  - Conventional Commits 규약 및 운영 승격(Promotion) 절차 확립
