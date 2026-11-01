# ForgeFlow 프로젝트 원칙

Core는 Python 3.10+ 표준 라이브러리만 사용합니다. 사용자 위임 범위 안에서 요구사항·비례적 계획·실제 검증·허용된 통합·task-owned 정리를 완료까지 조정합니다.

구현 전 scope·acceptance·plan·checks, 통합 전 필수 검증 통과·operation authority를 확정합니다. 작은 수정에 다중 서명·seal을 요구하지 않으며 추가 심사는 실제 위험·프로젝트 요구에 따릅니다.

사용자 작업을 보존합니다. 무관한 파일을 몰래 stage/reset/stash하거나 destructive recovery하지 않습니다. Host-managed worktree의 소유권을 지키고 ready/integrated/cleaned를 구분합니다.

docs/spec/README.md에서 소유 계약을 찾습니다. 기존 strict lifecycle는 명시적 compatibility이며 completed historical evidence는 불변입니다. Active task는 explicit adoption 전까지 content-pinned runtime을 따릅니다.

이번 governance control-plane 전환에는 src 변경 전 독립 Security/Reliability/Maintainability 설계 심사를 요구했고 독립 최종 심사도 유지합니다. 모든 downstream task에 해당 panel을 강제하지 않습니다.
