# Release Notes: v0.1.15

## 릴리즈 개요
`v0.1.15`는 릴리즈 밀봉(`lifecycle seal`) 및 완료(`lifecycle complete`) 후 `tasks/in-progress/<id>`에서 `tasks/completed/<id>`로 원자적 이동된 패키지가 커밋되었을 때, 바이트가 100% 동일함에도 사후 감사(`forgeflow check --lifecycle`)에서 `release_candidate_range_invalid`로 잘못 거부되던 결함(Issue #5)을 근본적으로 해결했습니다.

## 주요 변경 사항
1. **완료 패키지 이동 인식 및 Git Blob 기반 바이트 동일성 검증 (`harness.py`)**:
   - `_tree_files_at_commit` 및 `_find_verified_completion_relocation_paths` 엔진을 구현하여, 후보 커밋(`candidate`) 시점의 패키지 파일 트리와 현재 HEAD의 완료 패키지 파일 트리를 Git Blob SHA 수준에서 1:1 대조.
   - 단 1바이트라도 변조되거나, 신규 파일이 추가되거나, 원본 디렉토리에 파일이 잔류하거나, 타 릴리즈 파일이 혼입된 경우 즉각 차단(fail-closed)하고, 100% 바이트 동일성이 입증된 이동에 한해 사후 감사 화이트리스트로 수용.
2. **`lifecycle_complete` 태스크 디렉터리 호환성 보강**:
   - `configured` 커스텀 tasks 디렉터리가 설정된 환경에서도 완료 패키지 이동이 일관되게 동작하도록 보강.
3. **회귀 테스트 및 검증 완비**:
   - 정상 완료 이동 커밋 통과, 변조/추가/원본잔류/타릴리즈 혼입 차단, 실전 `seal -> complete -> commit -> audit` 전 과정 검증 단위 테스트 6종 추가 (총 304개 테스트 100% 통과).
