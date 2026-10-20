# 🔍 Code Review & Architecture Audit Report

- **판정 상태**: 🔴 FAILED
- **검사 일시**: 2026-10-20 19:13:18
- **검사 범위**: Explicit (4 files)
- **엄격 모드(Strict)**: 비활성화
- **체크포인트 캐시**: 활성화 (Hit: 4, Miss: 0)
- **스펙 소스**: `README.md`
- **참조 표준**: 기본 베이스라인

---

## 📊 요약 통계
- 검사 파일 수: 4개
- 검출 결함 총계: 154건 (Critical: 3, Warning: 151, Info: 0)

---

## 🛠️ 정적 AST 코드 스멜 & 메트릭 (Stage 1)
### [🔴 CRITICAL] `src/forgeflow/scaffold.py:1` - File Bloat
- **진단**: 파일의 전체 줄 수가 974줄로 기준(800줄)을 초과하여 God Module 위험이 있습니다.
- **개선 제안**: 패키지 디렉터리로 승격(Package Promotion)하거나 하위 도메인별 모듈로 역할을 분리하세요.

### [🟡 WARNING] `src/forgeflow/scaffold.py:20` - Large Class
- **진단**: 클래스 'TemplateScaffolder'의 메서드가 18개로 지나치게 많습니다.
- **개선 제안**: 클래스의 책임을 단일화하고 일부 역할을 컴포지션으로 분리하세요.

### [🟡 WARNING] `src/forgeflow/scaffold.py:180` - Long Function
- **진단**: 함수 '_recover_governance_transaction'의 길이가 54줄로 기준(50줄)을 초과합니다.
- **개선 제안**: 함수의 단일 책임 원칙(SRP)을 점검하고 보조 헬퍼 메서드로 분할하세요.

### [🟡 WARNING] `src/forgeflow/scaffold.py:180` - High Cognitive Complexity
- **진단**: 함수 '_recover_governance_transaction'의 인지 복잡도(Cognitive Complexity)가 21점으로 기준(15점)을 초과합니다.
- **개선 제안**: 중첩 제어 흐름 및 복합 조건식을 단순화하고 Guard Clause(Early Return)를 도입하거나 보조 서브루틴으로 추출하세요.

### [🟡 WARNING] `src/forgeflow/scaffold.py:224` - I/O in Loop
- **진단**: 루프 내부에서 반복적인 디스크 I/O 함수('backup.read_text')가 호출되어 심각한 I/O 병목이 발생할 수 있습니다.
- **개선 제안**: 루프 진입 전 데이터를 일괄 로드하거나 메모리 버퍼링 후 한 번에 기록하세요.

### [🟡 WARNING] `src/forgeflow/scaffold.py:236` - Long Function
- **진단**: 함수 '_apply_governance_transaction'의 길이가 64줄로 기준(50줄)을 초과합니다.
- **개선 제안**: 함수의 단일 책임 원칙(SRP)을 점검하고 보조 헬퍼 메서드로 분할하세요.

### [🟡 WARNING] `src/forgeflow/scaffold.py:247` - I/O in Loop
- **진단**: 루프 내부에서 반복적인 디스크 I/O 함수('path.read_text')가 호출되어 심각한 I/O 병목이 발생할 수 있습니다.
- **개선 제안**: 루프 진입 전 데이터를 일괄 로드하거나 메모리 버퍼링 후 한 번에 기록하세요.

### [🟡 WARNING] `src/forgeflow/scaffold.py:277` - Deep Nesting
- **진단**: 코드 블록의 중첩 깊이가 4단계로 가독성이 저하됩니다.
- **개선 제안**: Early return(Guard Clause)을 도입하거나 내부 로직을 별도 함수로 추출하세요.

### [🟡 WARNING] `src/forgeflow/scaffold.py:302` - Long Function
- **진단**: 함수 'scaffold_governance_binding'의 길이가 103줄로 기준(50줄)을 초과합니다.
- **개선 제안**: 함수의 단일 책임 원칙(SRP)을 점검하고 보조 헬퍼 메서드로 분할하세요.

### [🟡 WARNING] `src/forgeflow/scaffold.py:302` - Too Many Parameters
- **진단**: 함수 'scaffold_governance_binding'의 매개변수가 7개로 기준(5개)을 초과합니다.
- **개선 제안**: 매개변수를 하나의 DTO/Dataclass 객체로 묶어 전달하는 것을 고려하세요.

### [🟡 WARNING] `src/forgeflow/scaffold.py:302` - High Cognitive Complexity
- **진단**: 함수 'scaffold_governance_binding'의 인지 복잡도(Cognitive Complexity)가 56점으로 기준(15점)을 초과합니다.
- **개선 제안**: 중첩 제어 흐름 및 복합 조건식을 단순화하고 Guard Clause(Early Return)를 도입하거나 보조 서브루틴으로 추출하세요.

### [🟡 WARNING] `src/forgeflow/scaffold.py:369` - Deep Nesting
- **진단**: 코드 블록의 중첩 깊이가 4단계로 가독성이 저하됩니다.
- **개선 제안**: Early return(Guard Clause)을 도입하거나 내부 로직을 별도 함수로 추출하세요.

### [🟡 WARNING] `src/forgeflow/scaffold.py:380` - I/O in Loop
- **진단**: 루프 내부에서 반복적인 디스크 I/O 함수('guide.read_text')가 호출되어 심각한 I/O 병목이 발생할 수 있습니다.
- **개선 제안**: 루프 진입 전 데이터를 일괄 로드하거나 메모리 버퍼링 후 한 번에 기록하세요.

### [🟡 WARNING] `src/forgeflow/scaffold.py:384` - Deep Nesting
- **진단**: 코드 블록의 중첩 깊이가 4단계로 가독성이 저하됩니다.
- **개선 제안**: Early return(Guard Clause)을 도입하거나 내부 로직을 별도 함수로 추출하세요.

### [🟡 WARNING] `src/forgeflow/scaffold.py:397` - Deep Nesting
- **진단**: 코드 블록의 중첩 깊이가 4단계로 가독성이 저하됩니다.
- **개선 제안**: Early return(Guard Clause)을 도입하거나 내부 로직을 별도 함수로 추출하세요.

### [🟡 WARNING] `src/forgeflow/scaffold.py:454` - Long Function
- **진단**: 함수 'create_release_scaffold'의 길이가 122줄로 기준(50줄)을 초과합니다.
- **개선 제안**: 함수의 단일 책임 원칙(SRP)을 점검하고 보조 헬퍼 메서드로 분할하세요.

### [🟡 WARNING] `src/forgeflow/scaffold.py:454` - Too Many Parameters
- **진단**: 함수 'create_release_scaffold'의 매개변수가 6개로 기준(5개)을 초과합니다.
- **개선 제안**: 매개변수를 하나의 DTO/Dataclass 객체로 묶어 전달하는 것을 고려하세요.

### [🟡 WARNING] `src/forgeflow/scaffold.py:454` - High Cognitive Complexity
- **진단**: 함수 'create_release_scaffold'의 인지 복잡도(Cognitive Complexity)가 19점으로 기준(15점)을 초과합니다.
- **개선 제안**: 중첩 제어 흐름 및 복합 조건식을 단순화하고 Guard Clause(Early Return)를 도입하거나 보조 서브루틴으로 추출하세요.

### [🟡 WARNING] `src/forgeflow/scaffold.py:471` - I/O in Loop
- **진단**: 루프 내부에서 반복적인 디스크 I/O 함수('guard.write_text')가 호출되어 심각한 I/O 병목이 발생할 수 있습니다.
- **개선 제안**: 루프 진입 전 데이터를 일괄 로드하거나 메모리 버퍼링 후 한 번에 기록하세요.

### [🟡 WARNING] `src/forgeflow/scaffold.py:572` - I/O in Loop
- **진단**: 루프 내부에서 반복적인 디스크 I/O 함수('dest_file.write_text')가 호출되어 심각한 I/O 병목이 발생할 수 있습니다.
- **개선 제안**: 루프 진입 전 데이터를 일괄 로드하거나 메모리 버퍼링 후 한 번에 기록하세요.

### [🟡 WARNING] `src/forgeflow/scaffold.py:578` - Long Function
- **진단**: 함수 'init_project_governance'의 길이가 162줄로 기준(50줄)을 초과합니다.
- **개선 제안**: 함수의 단일 책임 원칙(SRP)을 점검하고 보조 헬퍼 메서드로 분할하세요.

### [🟡 WARNING] `src/forgeflow/scaffold.py:578` - Too Many Parameters
- **진단**: 함수 'init_project_governance'의 매개변수가 7개로 기준(5개)을 초과합니다.
- **개선 제안**: 매개변수를 하나의 DTO/Dataclass 객체로 묶어 전달하는 것을 고려하세요.

### [🟡 WARNING] `src/forgeflow/scaffold.py:578` - High Cognitive Complexity
- **진단**: 함수 'init_project_governance'의 인지 복잡도(Cognitive Complexity)가 19점으로 기준(15점)을 초과합니다.
- **개선 제안**: 중첩 제어 흐름 및 복합 조건식을 단순화하고 Guard Clause(Early Return)를 도입하거나 보조 서브루틴으로 추출하세요.

### [🟡 WARNING] `src/forgeflow/scaffold.py:688` - Deep Nesting
- **진단**: 코드 블록의 중첩 깊이가 4단계로 가독성이 저하됩니다.
- **개선 제안**: Early return(Guard Clause)을 도입하거나 내부 로직을 별도 함수로 추출하세요.

### [🟡 WARNING] `src/forgeflow/scaffold.py:690` - Deep Nesting
- **진단**: 코드 블록의 중첩 깊이가 5단계로 가독성이 저하됩니다.
- **개선 제안**: Early return(Guard Clause)을 도입하거나 내부 로직을 별도 함수로 추출하세요.

### [🟡 WARNING] `src/forgeflow/scaffold.py:712` - Silent Exception
- **진단**: 'except' 블록에서 예외를 처리하거나 로깅하지 않고 침묵(pass/ellipsis)으로 은폐합니다.
- **개선 제안**: 적절한 로깅을 추가하거나 명시적 예외 처리 또는 상위 재발생(raise)을 고려하세요.

### [🟡 WARNING] `src/forgeflow/scaffold.py:717` - Silent Exception
- **진단**: 'except' 블록에서 예외를 처리하거나 로깅하지 않고 침묵(pass/ellipsis)으로 은폐합니다.
- **개선 제안**: 적절한 로깅을 추가하거나 명시적 예외 처리 또는 상위 재발생(raise)을 고려하세요.

### [🟡 WARNING] `src/forgeflow/scaffold.py:782` - Silent Exception
- **진단**: 'except' 블록에서 예외를 처리하거나 로깅하지 않고 침묵(pass/ellipsis)으로 은폐합니다.
- **개선 제안**: 적절한 로깅을 추가하거나 명시적 예외 처리 또는 상위 재발생(raise)을 고려하세요.

### [🟡 WARNING] `src/forgeflow/scaffold.py:793` - Long Function
- **진단**: 함수 'scaffold_speckit_hybrid'의 길이가 182줄로 기준(50줄)을 초과합니다.
- **개선 제안**: 함수의 단일 책임 원칙(SRP)을 점검하고 보조 헬퍼 메서드로 분할하세요.

### [🟡 WARNING] `src/forgeflow/scaffold.py:793` - High Cognitive Complexity
- **진단**: 함수 'scaffold_speckit_hybrid'의 인지 복잡도(Cognitive Complexity)가 44점으로 기준(15점)을 초과합니다.
- **개선 제안**: 중첩 제어 흐름 및 복합 조건식을 단순화하고 Guard Clause(Early Return)를 도입하거나 보조 서브루틴으로 추출하세요.

### [🟡 WARNING] `src/forgeflow/scaffold.py:935` - I/O in Loop
- **진단**: 루프 내부에서 반복적인 디스크 I/O 함수('script_path.write_text')가 호출되어 심각한 I/O 병목이 발생할 수 있습니다.
- **개선 제안**: 루프 진입 전 데이터를 일괄 로드하거나 메모리 버퍼링 후 한 번에 기록하세요.

### [🟡 WARNING] `src/forgeflow/scaffold.py:954` - I/O in Loop
- **진단**: 루프 내부에서 반복적인 디스크 I/O 함수('tmpl_path.write_text')가 호출되어 심각한 I/O 병목이 발생할 수 있습니다.
- **개선 제안**: 루프 진입 전 데이터를 일괄 로드하거나 메모리 버퍼링 후 한 번에 기록하세요.

### [🟡 WARNING] `src/forgeflow/diagnostics.py:38` - Too Many Parameters
- **진단**: 함수 'log_event'의 매개변수가 9개로 기준(5개)을 초과합니다.
- **개선 제안**: 매개변수를 하나의 DTO/Dataclass 객체로 묶어 전달하는 것을 고려하세요.

### [🟡 WARNING] `src/forgeflow/diagnostics.py:73` - Silent Exception
- **진단**: 'except' 블록에서 예외를 처리하거나 로깅하지 않고 침묵(pass/ellipsis)으로 은폐합니다.
- **개선 제안**: 적절한 로깅을 추가하거나 명시적 예외 처리 또는 상위 재발생(raise)을 고려하세요.

### [🟡 WARNING] `src/forgeflow/diagnostics.py:86` - Deep Nesting
- **진단**: 코드 블록의 중첩 깊이가 4단계로 가독성이 저하됩니다.
- **개선 제안**: Early return(Guard Clause)을 도입하거나 내부 로직을 별도 함수로 추출하세요.

### [🟡 WARNING] `src/forgeflow/diagnostics.py:98` - Silent Exception
- **진단**: 'except' 블록에서 예외를 처리하거나 로깅하지 않고 침묵(pass/ellipsis)으로 은폐합니다.
- **개선 제안**: 적절한 로깅을 추가하거나 명시적 예외 처리 또는 상위 재발생(raise)을 고려하세요.

### [🟡 WARNING] `src/forgeflow/diagnostics.py:109` - Long Function
- **진단**: 함수 'analyze'의 길이가 135줄로 기준(50줄)을 초과합니다.
- **개선 제안**: 함수의 단일 책임 원칙(SRP)을 점검하고 보조 헬퍼 메서드로 분할하세요.

### [🟡 WARNING] `src/forgeflow/diagnostics.py:109` - High Cognitive Complexity
- **진단**: 함수 'analyze'의 인지 복잡도(Cognitive Complexity)가 40점으로 기준(15점)을 초과합니다.
- **개선 제안**: 중첩 제어 흐름 및 복합 조건식을 단순화하고 Guard Clause(Early Return)를 도입하거나 보조 서브루틴으로 추출하세요.

### [🟡 WARNING] `src/forgeflow/diagnostics.py:214` - Deep Nesting
- **진단**: 코드 블록의 중첩 깊이가 4단계로 가독성이 저하됩니다.
- **개선 제안**: Early return(Guard Clause)을 도입하거나 내부 로직을 별도 함수로 추출하세요.

### [🟡 WARNING] `src/forgeflow/diagnostics.py:240` - Silent Exception
- **진단**: 'except' 블록에서 예외를 처리하거나 로깅하지 않고 침묵(pass/ellipsis)으로 은폐합니다.
- **개선 제안**: 적절한 로깅을 추가하거나 명시적 예외 처리 또는 상위 재발생(raise)을 고려하세요.

### [🟡 WARNING] `src/forgeflow/diagnostics.py:276` - Long Function
- **진단**: 함수 'generate_issue_draft'의 길이가 58줄로 기준(50줄)을 초과합니다.
- **개선 제안**: 함수의 단일 책임 원칙(SRP)을 점검하고 보조 헬퍼 메서드로 분할하세요.

### [🟡 WARNING] `src/forgeflow/diagnostics.py:336` - Long Function
- **진단**: 함수 'doctor_main'의 길이가 62줄로 기준(50줄)을 초과합니다.
- **개선 제안**: 함수의 단일 책임 원칙(SRP)을 점검하고 보조 헬퍼 메서드로 분할하세요.

### [🟡 WARNING] `src/forgeflow/diagnostics.py:336` - High Cognitive Complexity
- **진단**: 함수 'doctor_main'의 인지 복잡도(Cognitive Complexity)가 16점으로 기준(15점)을 초과합니다.
- **개선 제안**: 중첩 제어 흐름 및 복합 조건식을 단순화하고 Guard Clause(Early Return)를 도입하거나 보조 서브루틴으로 추출하세요.

### [🔴 CRITICAL] `src/forgeflow/validator.py:1` - File Bloat
- **진단**: 파일의 전체 줄 수가 914줄로 기준(800줄)을 초과하여 God Module 위험이 있습니다.
- **개선 제안**: 패키지 디렉터리로 승격(Package Promotion)하거나 하위 도메인별 모듈로 역할을 분리하세요.

### [🟡 WARNING] `src/forgeflow/validator.py:76` - High Cognitive Complexity
- **진단**: 함수 '_coverage_rows'의 인지 복잡도(Cognitive Complexity)가 19점으로 기준(15점)을 초과합니다.
- **개선 제안**: 중첩 제어 흐름 및 복합 조건식을 단순화하고 Guard Clause(Early Return)를 도입하거나 보조 서브루틴으로 추출하세요.

### [🟡 WARNING] `src/forgeflow/validator.py:173` - Too Many Parameters
- **진단**: 함수 '_validate_version_binding'의 매개변수가 6개로 기준(5개)을 초과합니다.
- **개선 제안**: 매개변수를 하나의 DTO/Dataclass 객체로 묶어 전달하는 것을 고려하세요.

### [🟡 WARNING] `src/forgeflow/validator.py:173` - High Cognitive Complexity
- **진단**: 함수 '_validate_version_binding'의 인지 복잡도(Cognitive Complexity)가 20점으로 기준(15점)을 초과합니다.
- **개선 제안**: 중첩 제어 흐름 및 복합 조건식을 단순화하고 Guard Clause(Early Return)를 도입하거나 보조 서브루틴으로 추출하세요.

### [🟡 WARNING] `src/forgeflow/validator.py:224` - Long Function
- **진단**: 함수 'validate'의 길이가 96줄로 기준(50줄)을 초과합니다.
- **개선 제안**: 함수의 단일 책임 원칙(SRP)을 점검하고 보조 헬퍼 메서드로 분할하세요.

### [🟡 WARNING] `src/forgeflow/validator.py:243` - Deep Nesting
- **진단**: 코드 블록의 중첩 깊이가 4단계로 가독성이 저하됩니다.
- **개선 제안**: Early return(Guard Clause)을 도입하거나 내부 로직을 별도 함수로 추출하세요.

### [🟡 WARNING] `src/forgeflow/validator.py:245` - Deep Nesting
- **진단**: 코드 블록의 중첩 깊이가 5단계로 가독성이 저하됩니다.
- **개선 제안**: Early return(Guard Clause)을 도입하거나 내부 로직을 별도 함수로 추출하세요.

### [🟡 WARNING] `src/forgeflow/validator.py:247` - Silent Exception
- **진단**: 'except' 블록에서 예외를 처리하거나 로깅하지 않고 침묵(pass/ellipsis)으로 은폐합니다.
- **개선 제안**: 적절한 로깅을 추가하거나 명시적 예외 처리 또는 상위 재발생(raise)을 고려하세요.

### [🟡 WARNING] `src/forgeflow/validator.py:255` - Deep Nesting
- **진단**: 코드 블록의 중첩 깊이가 4단계로 가독성이 저하됩니다.
- **개선 제안**: Early return(Guard Clause)을 도입하거나 내부 로직을 별도 함수로 추출하세요.

### [🟡 WARNING] `src/forgeflow/validator.py:257` - Deep Nesting
- **진단**: 코드 블록의 중첩 깊이가 5단계로 가독성이 저하됩니다.
- **개선 제안**: Early return(Guard Clause)을 도입하거나 내부 로직을 별도 함수로 추출하세요.

### [🟡 WARNING] `src/forgeflow/validator.py:259` - Silent Exception
- **진단**: 'except' 블록에서 예외를 처리하거나 로깅하지 않고 침묵(pass/ellipsis)으로 은폐합니다.
- **개선 제안**: 적절한 로깅을 추가하거나 명시적 예외 처리 또는 상위 재발생(raise)을 고려하세요.

### [🟡 WARNING] `src/forgeflow/validator.py:315` - I/O in Loop
- **진단**: 루프 내부에서 반복적인 디스크 I/O 함수('read_bytes')가 호출되어 심각한 I/O 병목이 발생할 수 있습니다.
- **개선 제안**: 루프 진입 전 데이터를 일괄 로드하거나 메모리 버퍼링 후 한 번에 기록하세요.

### [🟡 WARNING] `src/forgeflow/validator.py:315` - I/O in Loop
- **진단**: 루프 내부에서 반복적인 디스크 I/O 함수('read_bytes')가 호출되어 심각한 I/O 병목이 발생할 수 있습니다.
- **개선 제안**: 루프 진입 전 데이터를 일괄 로드하거나 메모리 버퍼링 후 한 번에 기록하세요.

### [🟡 WARNING] `src/forgeflow/validator.py:477` - Long Function
- **진단**: 함수 'parse_oidr_prd'의 길이가 118줄로 기준(50줄)을 초과합니다.
- **개선 제안**: 함수의 단일 책임 원칙(SRP)을 점검하고 보조 헬퍼 메서드로 분할하세요.

### [🟡 WARNING] `src/forgeflow/validator.py:477` - High Cognitive Complexity
- **진단**: 함수 'parse_oidr_prd'의 인지 복잡도(Cognitive Complexity)가 46점으로 기준(15점)을 초과합니다.
- **개선 제안**: 중첩 제어 흐름 및 복합 조건식을 단순화하고 Guard Clause(Early Return)를 도입하거나 보조 서브루틴으로 추출하세요.

### [🟡 WARNING] `src/forgeflow/validator.py:557` - Deep Nesting
- **진단**: 코드 블록의 중첩 깊이가 4단계로 가독성이 저하됩니다.
- **개선 제안**: Early return(Guard Clause)을 도입하거나 내부 로직을 별도 함수로 추출하세요.

### [🟡 WARNING] `src/forgeflow/validator.py:559` - Deep Nesting
- **진단**: 코드 블록의 중첩 깊이가 4단계로 가독성이 저하됩니다.
- **개선 제안**: Early return(Guard Clause)을 도입하거나 내부 로직을 별도 함수로 추출하세요.

### [🟡 WARNING] `src/forgeflow/validator.py:571` - Deep Nesting
- **진단**: 코드 블록의 중첩 깊이가 4단계로 가독성이 저하됩니다.
- **개선 제안**: Early return(Guard Clause)을 도입하거나 내부 로직을 별도 함수로 추출하세요.

### [🟡 WARNING] `src/forgeflow/validator.py:597` - Long Function
- **진단**: 함수 'parse_oidr_qa'의 길이가 102줄로 기준(50줄)을 초과합니다.
- **개선 제안**: 함수의 단일 책임 원칙(SRP)을 점검하고 보조 헬퍼 메서드로 분할하세요.

### [🟡 WARNING] `src/forgeflow/validator.py:597` - High Cognitive Complexity
- **진단**: 함수 'parse_oidr_qa'의 인지 복잡도(Cognitive Complexity)가 40점으로 기준(15점)을 초과합니다.
- **개선 제안**: 중첩 제어 흐름 및 복합 조건식을 단순화하고 Guard Clause(Early Return)를 도입하거나 보조 서브루틴으로 추출하세요.

### [🟡 WARNING] `src/forgeflow/validator.py:707` - Long Function
- **진단**: 함수 'validate'의 길이가 95줄로 기준(50줄)을 초과합니다.
- **개선 제안**: 함수의 단일 책임 원칙(SRP)을 점검하고 보조 헬퍼 메서드로 분할하세요.

### [🟡 WARNING] `src/forgeflow/validator.py:707` - High Cognitive Complexity
- **진단**: 함수 'validate'의 인지 복잡도(Cognitive Complexity)가 31점으로 기준(15점)을 초과합니다.
- **개선 제안**: 중첩 제어 흐름 및 복합 조건식을 단순화하고 Guard Clause(Early Return)를 도입하거나 보조 서브루틴으로 추출하세요.

### [🟡 WARNING] `src/forgeflow/validator.py:764` - Deep Nesting
- **진단**: 코드 블록의 중첩 깊이가 4단계로 가독성이 저하됩니다.
- **개선 제안**: Early return(Guard Clause)을 도입하거나 내부 로직을 별도 함수로 추출하세요.

### [🟡 WARNING] `src/forgeflow/validator.py:803` - Long Function
- **진단**: 함수 'validate_file'의 길이가 112줄로 기준(50줄)을 초과합니다.
- **개선 제안**: 함수의 단일 책임 원칙(SRP)을 점검하고 보조 헬퍼 메서드로 분할하세요.

### [🟡 WARNING] `src/forgeflow/validator.py:803` - High Cognitive Complexity
- **진단**: 함수 'validate_file'의 인지 복잡도(Cognitive Complexity)가 59점으로 기준(15점)을 초과합니다.
- **개선 제안**: 중첩 제어 흐름 및 복합 조건식을 단순화하고 Guard Clause(Early Return)를 도입하거나 보조 서브루틴으로 추출하세요.

### [🟡 WARNING] `src/forgeflow/validator.py:842` - Deep Nesting
- **진단**: 코드 블록의 중첩 깊이가 4단계로 가독성이 저하됩니다.
- **개선 제안**: Early return(Guard Clause)을 도입하거나 내부 로직을 별도 함수로 추출하세요.

### [🟡 WARNING] `src/forgeflow/validator.py:845` - Deep Nesting
- **진단**: 코드 블록의 중첩 깊이가 4단계로 가독성이 저하됩니다.
- **개선 제안**: Early return(Guard Clause)을 도입하거나 내부 로직을 별도 함수로 추출하세요.

### [🟡 WARNING] `src/forgeflow/validator.py:849` - Deep Nesting
- **진단**: 코드 블록의 중첩 깊이가 5단계로 가독성이 저하됩니다.
- **개선 제안**: Early return(Guard Clause)을 도입하거나 내부 로직을 별도 함수로 추출하세요.

### [🟡 WARNING] `src/forgeflow/validator.py:852` - Deep Nesting
- **진단**: 코드 블록의 중첩 깊이가 5단계로 가독성이 저하됩니다.
- **개선 제안**: Early return(Guard Clause)을 도입하거나 내부 로직을 별도 함수로 추출하세요.

### [🟡 WARNING] `src/forgeflow/validator.py:856` - Deep Nesting
- **진단**: 코드 블록의 중첩 깊이가 6단계로 가독성이 저하됩니다.
- **개선 제안**: Early return(Guard Clause)을 도입하거나 내부 로직을 별도 함수로 추출하세요.

### [🟡 WARNING] `src/forgeflow/validator.py:859` - Deep Nesting
- **진단**: 코드 블록의 중첩 깊이가 6단계로 가독성이 저하됩니다.
- **개선 제안**: Early return(Guard Clause)을 도입하거나 내부 로직을 별도 함수로 추출하세요.

### [🟡 WARNING] `src/forgeflow/validator.py:863` - Deep Nesting
- **진단**: 코드 블록의 중첩 깊이가 7단계로 가독성이 저하됩니다.
- **개선 제안**: Early return(Guard Clause)을 도입하거나 내부 로직을 별도 함수로 추출하세요.

### [🟡 WARNING] `src/forgeflow/validator.py:865` - Deep Nesting
- **진단**: 코드 블록의 중첩 깊이가 7단계로 가독성이 저하됩니다.
- **개선 제안**: Early return(Guard Clause)을 도입하거나 내부 로직을 별도 함수로 추출하세요.

### [🟡 WARNING] `src/forgeflow/validator.py:869` - Deep Nesting
- **진단**: 코드 블록의 중첩 깊이가 7단계로 가독성이 저하됩니다.
- **개선 제안**: Early return(Guard Clause)을 도입하거나 내부 로직을 별도 함수로 추출하세요.

### [🟡 WARNING] `src/forgeflow/validator.py:873` - Deep Nesting
- **진단**: 코드 블록의 중첩 깊이가 7단계로 가독성이 저하됩니다.
- **개선 제안**: Early return(Guard Clause)을 도입하거나 내부 로직을 별도 함수로 추출하세요.

### [🟡 WARNING] `src/forgeflow/validator.py:877` - Deep Nesting
- **진단**: 코드 블록의 중첩 깊이가 8단계로 가독성이 저하됩니다.
- **개선 제안**: Early return(Guard Clause)을 도입하거나 내부 로직을 별도 함수로 추출하세요.

### [🟡 WARNING] `src/forgeflow/validator.py:879` - Deep Nesting
- **진단**: 코드 블록의 중첩 깊이가 8단계로 가독성이 저하됩니다.
- **개선 제안**: Early return(Guard Clause)을 도입하거나 내부 로직을 별도 함수로 추출하세요.

### [🟡 WARNING] `src/forgeflow/validator.py:882` - Deep Nesting
- **진단**: 코드 블록의 중첩 깊이가 8단계로 가독성이 저하됩니다.
- **개선 제안**: Early return(Guard Clause)을 도입하거나 내부 로직을 별도 함수로 추출하세요.

### [🟡 WARNING] `src/forgeflow/validator.py:886` - Deep Nesting
- **진단**: 코드 블록의 중첩 깊이가 9단계로 가독성이 저하됩니다.
- **개선 제안**: Early return(Guard Clause)을 도입하거나 내부 로직을 별도 함수로 추출하세요.

### [🟡 WARNING] `src/forgeflow/validator.py:892` - Deep Nesting
- **진단**: 코드 블록의 중첩 깊이가 9단계로 가독성이 저하됩니다.
- **개선 제안**: Early return(Guard Clause)을 도입하거나 내부 로직을 별도 함수로 추출하세요.

### [🟡 WARNING] `src/forgeflow/validator.py:896` - Deep Nesting
- **진단**: 코드 블록의 중첩 깊이가 9단계로 가독성이 저하됩니다.
- **개선 제안**: Early return(Guard Clause)을 도입하거나 내부 로직을 별도 함수로 추출하세요.

### [🟡 WARNING] `src/forgeflow/validator.py:900` - Deep Nesting
- **진단**: 코드 블록의 중첩 깊이가 10단계로 가독성이 저하됩니다.
- **개선 제안**: Early return(Guard Clause)을 도입하거나 내부 로직을 별도 함수로 추출하세요.

### [🟡 WARNING] `src/forgeflow/validator.py:902` - Deep Nesting
- **진단**: 코드 블록의 중첩 깊이가 10단계로 가독성이 저하됩니다.
- **개선 제안**: Early return(Guard Clause)을 도입하거나 내부 로직을 별도 함수로 추출하세요.

### [🟡 WARNING] `src/forgeflow/validator.py:905` - Deep Nesting
- **진단**: 코드 블록의 중첩 깊이가 10단계로 가독성이 저하됩니다.
- **개선 제안**: Early return(Guard Clause)을 도입하거나 내부 로직을 별도 함수로 추출하세요.

### [🟡 WARNING] `src/forgeflow/validator.py:908` - Deep Nesting
- **진단**: 코드 블록의 중첩 깊이가 11단계로 가독성이 저하됩니다.
- **개선 제안**: Early return(Guard Clause)을 도입하거나 내부 로직을 별도 함수로 추출하세요.

### [🔴 CRITICAL] `src/forgeflow/harness.py:1` - File Bloat
- **진단**: 파일의 전체 줄 수가 1821줄로 기준(800줄)을 초과하여 God Module 위험이 있습니다.
- **개선 제안**: 패키지 디렉터리로 승격(Package Promotion)하거나 하위 도메인별 모듈로 역할을 분리하세요.

### [🟡 WARNING] `src/forgeflow/harness.py:140` - Long Function
- **진단**: 함수 'validate_attestation'의 길이가 75줄로 기준(50줄)을 초과합니다.
- **개선 제안**: 함수의 단일 책임 원칙(SRP)을 점검하고 보조 헬퍼 메서드로 분할하세요.

### [🟡 WARNING] `src/forgeflow/harness.py:140` - High Cognitive Complexity
- **진단**: 함수 'validate_attestation'의 인지 복잡도(Cognitive Complexity)가 39점으로 기준(15점)을 초과합니다.
- **개선 제안**: 중첩 제어 흐름 및 복합 조건식을 단순화하고 Guard Clause(Early Return)를 도입하거나 보조 서브루틴으로 추출하세요.

### [🟡 WARNING] `src/forgeflow/harness.py:256` - Long Function
- **진단**: 함수 'validate'의 길이가 57줄로 기준(50줄)을 초과합니다.
- **개선 제안**: 함수의 단일 책임 원칙(SRP)을 점검하고 보조 헬퍼 메서드로 분할하세요.

### [🟡 WARNING] `src/forgeflow/harness.py:256` - High Cognitive Complexity
- **진단**: 함수 'validate'의 인지 복잡도(Cognitive Complexity)가 55점으로 기준(15점)을 초과합니다.
- **개선 제안**: 중첩 제어 흐름 및 복합 조건식을 단순화하고 Guard Clause(Early Return)를 도입하거나 보조 서브루틴으로 추출하세요.

### [🟡 WARNING] `src/forgeflow/harness.py:346` - Silent Exception
- **진단**: 'except' 블록에서 예외를 처리하거나 로깅하지 않고 침묵(pass/ellipsis)으로 은폐합니다.
- **개선 제안**: 적절한 로깅을 추가하거나 명시적 예외 처리 또는 상위 재발생(raise)을 고려하세요.

### [🟡 WARNING] `src/forgeflow/harness.py:395` - Large Class
- **진단**: 클래스 'HarnessEngine'의 메서드가 44개로 지나치게 많습니다.
- **개선 제안**: 클래스의 책임을 단일화하고 일부 역할을 컴포지션으로 분리하세요.

### [🟡 WARNING] `src/forgeflow/harness.py:401` - High Cognitive Complexity
- **진단**: 함수 '_release_dir'의 인지 복잡도(Cognitive Complexity)가 22점으로 기준(15점)을 초과합니다.
- **개선 제안**: 중첩 제어 흐름 및 복합 조건식을 단순화하고 Guard Clause(Early Return)를 도입하거나 보조 서브루틴으로 추출하세요.

### [🟡 WARNING] `src/forgeflow/harness.py:428` - Long Function
- **진단**: 함수 'check_release'의 길이가 89줄로 기준(50줄)을 초과합니다.
- **개선 제안**: 함수의 단일 책임 원칙(SRP)을 점검하고 보조 헬퍼 메서드로 분할하세요.

### [🟡 WARNING] `src/forgeflow/harness.py:428` - High Cognitive Complexity
- **진단**: 함수 'check_release'의 인지 복잡도(Cognitive Complexity)가 32점으로 기준(15점)을 초과합니다.
- **개선 제안**: 중첩 제어 흐름 및 복합 조건식을 단순화하고 Guard Clause(Early Return)를 도입하거나 보조 서브루틴으로 추출하세요.

### [🟡 WARNING] `src/forgeflow/harness.py:471` - Deep Nesting
- **진단**: 코드 블록의 중첩 깊이가 4단계로 가독성이 저하됩니다.
- **개선 제안**: Early return(Guard Clause)을 도입하거나 내부 로직을 별도 함수로 추출하세요.

### [🟡 WARNING] `src/forgeflow/harness.py:518` - Long Function
- **진단**: 함수 '_check_module_bloat_strict'의 길이가 60줄로 기준(50줄)을 초과합니다.
- **개선 제안**: 함수의 단일 책임 원칙(SRP)을 점검하고 보조 헬퍼 메서드로 분할하세요.

### [🟡 WARNING] `src/forgeflow/harness.py:518` - High Cognitive Complexity
- **진단**: 함수 '_check_module_bloat_strict'의 인지 복잡도(Cognitive Complexity)가 19점으로 기준(15점)을 초과합니다.
- **개선 제안**: 중첩 제어 흐름 및 복합 조건식을 단순화하고 Guard Clause(Early Return)를 도입하거나 보조 서브루틴으로 추출하세요.

### [🟡 WARNING] `src/forgeflow/harness.py:529` - Deep Nesting
- **진단**: 코드 블록의 중첩 깊이가 4단계로 가독성이 저하됩니다.
- **개선 제안**: Early return(Guard Clause)을 도입하거나 내부 로직을 별도 함수로 추출하세요.

### [🟡 WARNING] `src/forgeflow/harness.py:537` - Deep Nesting
- **진단**: 코드 블록의 중첩 깊이가 4단계로 가독성이 저하됩니다.
- **개선 제안**: Early return(Guard Clause)을 도입하거나 내부 로직을 별도 함수로 추출하세요.

### [🟡 WARNING] `src/forgeflow/harness.py:547` - I/O in Loop
- **진단**: 루프 내부에서 반복적인 디스크 I/O 함수('p.read_text')가 호출되어 심각한 I/O 병목이 발생할 수 있습니다.
- **개선 제안**: 루프 진입 전 데이터를 일괄 로드하거나 메모리 버퍼링 후 한 번에 기록하세요.

### [🟡 WARNING] `src/forgeflow/harness.py:548` - Silent Exception
- **진단**: 'except' 블록에서 예외를 처리하거나 로깅하지 않고 침묵(pass/ellipsis)으로 은폐합니다.
- **개선 제안**: 적절한 로깅을 추가하거나 명시적 예외 처리 또는 상위 재발생(raise)을 고려하세요.

### [🟡 WARNING] `src/forgeflow/harness.py:563` - I/O in Loop
- **진단**: 루프 내부에서 반복적인 디스크 I/O 함수('full_p.read_text')가 호출되어 심각한 I/O 병목이 발생할 수 있습니다.
- **개선 제안**: 루프 진입 전 데이터를 일괄 로드하거나 메모리 버퍼링 후 한 번에 기록하세요.

### [🟡 WARNING] `src/forgeflow/harness.py:565` - Deep Nesting
- **진단**: 코드 블록의 중첩 깊이가 4단계로 가독성이 저하됩니다.
- **개선 제안**: Early return(Guard Clause)을 도입하거나 내부 로직을 별도 함수로 추출하세요.

### [🟡 WARNING] `src/forgeflow/harness.py:570` - Deep Nesting
- **진단**: 코드 블록의 중첩 깊이가 5단계로 가독성이 저하됩니다.
- **개선 제안**: Early return(Guard Clause)을 도입하거나 내부 로직을 별도 함수로 추출하세요.

### [🟡 WARNING] `src/forgeflow/harness.py:575` - Silent Exception
- **진단**: 'except' 블록에서 예외를 처리하거나 로깅하지 않고 침묵(pass/ellipsis)으로 은폐합니다.
- **개선 제안**: 적절한 로깅을 추가하거나 명시적 예외 처리 또는 상위 재발생(raise)을 고려하세요.

### [🟡 WARNING] `src/forgeflow/harness.py:579` - Long Function
- **진단**: 함수 'check_all_releases'의 길이가 76줄로 기준(50줄)을 초과합니다.
- **개선 제안**: 함수의 단일 책임 원칙(SRP)을 점검하고 보조 헬퍼 메서드로 분할하세요.

### [🟡 WARNING] `src/forgeflow/harness.py:579` - High Cognitive Complexity
- **진단**: 함수 'check_all_releases'의 인지 복잡도(Cognitive Complexity)가 26점으로 기준(15점)을 초과합니다.
- **개선 제안**: 중첩 제어 흐름 및 복합 조건식을 단순화하고 Guard Clause(Early Return)를 도입하거나 보조 서브루틴으로 추출하세요.

### [🟡 WARNING] `src/forgeflow/harness.py:605` - Deep Nesting
- **진단**: 코드 블록의 중첩 깊이가 4단계로 가독성이 저하됩니다.
- **개선 제안**: Early return(Guard Clause)을 도입하거나 내부 로직을 별도 함수로 추출하세요.

### [🟡 WARNING] `src/forgeflow/harness.py:613` - Deep Nesting
- **진단**: 코드 블록의 중첩 깊이가 4단계로 가독성이 저하됩니다.
- **개선 제안**: Early return(Guard Clause)을 도입하거나 내부 로직을 별도 함수로 추출하세요.

### [🟡 WARNING] `src/forgeflow/harness.py:615` - Silent Exception
- **진단**: 'except' 블록에서 예외를 처리하거나 로깅하지 않고 침묵(pass/ellipsis)으로 은폐합니다.
- **개선 제안**: 적절한 로깅을 추가하거나 명시적 예외 처리 또는 상위 재발생(raise)을 고려하세요.

### [🟡 WARNING] `src/forgeflow/harness.py:664` - Long Function
- **진단**: 함수 'check_lifecycle_evidence'의 길이가 82줄로 기준(50줄)을 초과합니다.
- **개선 제안**: 함수의 단일 책임 원칙(SRP)을 점검하고 보조 헬퍼 메서드로 분할하세요.

### [🟡 WARNING] `src/forgeflow/harness.py:664` - High Cognitive Complexity
- **진단**: 함수 'check_lifecycle_evidence'의 인지 복잡도(Cognitive Complexity)가 17점으로 기준(15점)을 초과합니다.
- **개선 제안**: 중첩 제어 흐름 및 복합 조건식을 단순화하고 Guard Clause(Early Return)를 도입하거나 보조 서브루틴으로 추출하세요.

### [🟡 WARNING] `src/forgeflow/harness.py:829` - Too Many Parameters
- **진단**: 함수 'lifecycle_advance'의 매개변수가 9개로 기준(5개)을 초과합니다.
- **개선 제안**: 매개변수를 하나의 DTO/Dataclass 객체로 묶어 전달하는 것을 고려하세요.

### [🟡 WARNING] `src/forgeflow/harness.py:829` - High Cognitive Complexity
- **진단**: 함수 'lifecycle_advance'의 인지 복잡도(Cognitive Complexity)가 17점으로 기준(15점)을 초과합니다.
- **개선 제안**: 중첩 제어 흐름 및 복합 조건식을 단순화하고 Guard Clause(Early Return)를 도입하거나 보조 서브루틴으로 추출하세요.

### [🟡 WARNING] `src/forgeflow/harness.py:900` - Silent Exception
- **진단**: 'except' 블록에서 예외를 처리하거나 로깅하지 않고 침묵(pass/ellipsis)으로 은폐합니다.
- **개선 제안**: 적절한 로깅을 추가하거나 명시적 예외 처리 또는 상위 재발생(raise)을 고려하세요.

### [🟡 WARNING] `src/forgeflow/harness.py:910` - Long Function
- **진단**: 함수 'lifecycle_seal'의 길이가 58줄로 기준(50줄)을 초과합니다.
- **개선 제안**: 함수의 단일 책임 원칙(SRP)을 점검하고 보조 헬퍼 메서드로 분할하세요.

### [🟡 WARNING] `src/forgeflow/harness.py:910` - High Cognitive Complexity
- **진단**: 함수 'lifecycle_seal'의 인지 복잡도(Cognitive Complexity)가 20점으로 기준(15점)을 초과합니다.
- **개선 제안**: 중첩 제어 흐름 및 복합 조건식을 단순화하고 Guard Clause(Early Return)를 도입하거나 보조 서브루틴으로 추출하세요.

### [🟡 WARNING] `src/forgeflow/harness.py:1031` - Long Function
- **진단**: 함수 'lifecycle_complete'의 길이가 69줄로 기준(50줄)을 초과합니다.
- **개선 제안**: 함수의 단일 책임 원칙(SRP)을 점검하고 보조 헬퍼 메서드로 분할하세요.

### [🟡 WARNING] `src/forgeflow/harness.py:1031` - High Cognitive Complexity
- **진단**: 함수 'lifecycle_complete'의 인지 복잡도(Cognitive Complexity)가 22점으로 기준(15점)을 초과합니다.
- **개선 제안**: 중첩 제어 흐름 및 복합 조건식을 단순화하고 Guard Clause(Early Return)를 도입하거나 보조 서브루틴으로 추출하세요.

### [🟡 WARNING] `src/forgeflow/harness.py:1053` - Silent Exception
- **진단**: 'except' 블록에서 예외를 처리하거나 로깅하지 않고 침묵(pass/ellipsis)으로 은폐합니다.
- **개선 제안**: 적절한 로깅을 추가하거나 명시적 예외 처리 또는 상위 재발생(raise)을 고려하세요.

### [🟡 WARNING] `src/forgeflow/harness.py:1069` - Deep Nesting
- **진단**: 코드 블록의 중첩 깊이가 4단계로 가독성이 저하됩니다.
- **개선 제안**: Early return(Guard Clause)을 도입하거나 내부 로직을 별도 함수로 추출하세요.

### [🟡 WARNING] `src/forgeflow/harness.py:1071` - Silent Exception
- **진단**: 'except' 블록에서 예외를 처리하거나 로깅하지 않고 침묵(pass/ellipsis)으로 은폐합니다.
- **개선 제안**: 적절한 로깅을 추가하거나 명시적 예외 처리 또는 상위 재발생(raise)을 고려하세요.

### [🟡 WARNING] `src/forgeflow/harness.py:1082` - Deep Nesting
- **진단**: 코드 블록의 중첩 깊이가 4단계로 가독성이 저하됩니다.
- **개선 제안**: Early return(Guard Clause)을 도입하거나 내부 로직을 별도 함수로 추출하세요.

### [🟡 WARNING] `src/forgeflow/harness.py:1084` - Silent Exception
- **진단**: 'except' 블록에서 예외를 처리하거나 로깅하지 않고 침묵(pass/ellipsis)으로 은폐합니다.
- **개선 제안**: 적절한 로깅을 추가하거나 명시적 예외 처리 또는 상위 재발생(raise)을 고려하세요.

### [🟡 WARNING] `src/forgeflow/harness.py:1101` - Long Function
- **진단**: 함수 'lifecycle_close'의 길이가 96줄로 기준(50줄)을 초과합니다.
- **개선 제안**: 함수의 단일 책임 원칙(SRP)을 점검하고 보조 헬퍼 메서드로 분할하세요.

### [🟡 WARNING] `src/forgeflow/harness.py:1101` - High Cognitive Complexity
- **진단**: 함수 'lifecycle_close'의 인지 복잡도(Cognitive Complexity)가 18점으로 기준(15점)을 초과합니다.
- **개선 제안**: 중첩 제어 흐름 및 복합 조건식을 단순화하고 Guard Clause(Early Return)를 도입하거나 보조 서브루틴으로 추출하세요.

### [🟡 WARNING] `src/forgeflow/harness.py:1159` - Deep Nesting
- **진단**: 코드 블록의 중첩 깊이가 4단계로 가독성이 저하됩니다.
- **개선 제안**: Early return(Guard Clause)을 도입하거나 내부 로직을 별도 함수로 추출하세요.

### [🟡 WARNING] `src/forgeflow/harness.py:1223` - Deep Nesting
- **진단**: 코드 블록의 중첩 깊이가 4단계로 가독성이 저하됩니다.
- **개선 제안**: Early return(Guard Clause)을 도입하거나 내부 로직을 별도 함수로 추출하세요.

### [🟡 WARNING] `src/forgeflow/harness.py:1228` - Deep Nesting
- **진단**: 코드 블록의 중첩 깊이가 4단계로 가독성이 저하됩니다.
- **개선 제안**: Early return(Guard Clause)을 도입하거나 내부 로직을 별도 함수로 추출하세요.

### [🟡 WARNING] `src/forgeflow/harness.py:1235` - Deep Nesting
- **진단**: 코드 블록의 중첩 깊이가 4단계로 가독성이 저하됩니다.
- **개선 제안**: Early return(Guard Clause)을 도입하거나 내부 로직을 별도 함수로 추출하세요.

### [🟡 WARNING] `src/forgeflow/harness.py:1237` - Deep Nesting
- **진단**: 코드 블록의 중첩 깊이가 5단계로 가독성이 저하됩니다.
- **개선 제안**: Early return(Guard Clause)을 도입하거나 내부 로직을 별도 함수로 추출하세요.

### [🟡 WARNING] `src/forgeflow/harness.py:1239` - Deep Nesting
- **진단**: 코드 블록의 중첩 깊이가 6단계로 가독성이 저하됩니다.
- **개선 제안**: Early return(Guard Clause)을 도입하거나 내부 로직을 별도 함수로 추출하세요.

### [🟡 WARNING] `src/forgeflow/harness.py:1242` - Deep Nesting
- **진단**: 코드 블록의 중첩 깊이가 6단계로 가독성이 저하됩니다.
- **개선 제안**: Early return(Guard Clause)을 도입하거나 내부 로직을 별도 함수로 추출하세요.

### [🟡 WARNING] `src/forgeflow/harness.py:1244` - Deep Nesting
- **진단**: 코드 블록의 중첩 깊이가 7단계로 가독성이 저하됩니다.
- **개선 제안**: Early return(Guard Clause)을 도입하거나 내부 로직을 별도 함수로 추출하세요.

### [🟡 WARNING] `src/forgeflow/harness.py:1287` - High Cognitive Complexity
- **진단**: 함수 '_validate_lifecycle_state_for_audit'의 인지 복잡도(Cognitive Complexity)가 36점으로 기준(15점)을 초과합니다.
- **개선 제안**: 중첩 제어 흐름 및 복합 조건식을 단순화하고 Guard Clause(Early Return)를 도입하거나 보조 서브루틴으로 추출하세요.

### [🟡 WARNING] `src/forgeflow/harness.py:1356` - High Cognitive Complexity
- **진단**: 함수 '_parse_evidence_v2'의 인지 복잡도(Cognitive Complexity)가 18점으로 기준(15점)을 초과합니다.
- **개선 제안**: 중첩 제어 흐름 및 복합 조건식을 단순화하고 Guard Clause(Early Return)를 도입하거나 보조 서브루틴으로 추출하세요.

### [🟡 WARNING] `src/forgeflow/harness.py:1382` - High Cognitive Complexity
- **진단**: 함수 '_validate_evidence_v2'의 인지 복잡도(Cognitive Complexity)가 37점으로 기준(15점)을 초과합니다.
- **개선 제안**: 중첩 제어 흐름 및 복합 조건식을 단순화하고 Guard Clause(Early Return)를 도입하거나 보조 서브루틴으로 추출하세요.

### [🟡 WARNING] `src/forgeflow/harness.py:1456` - High Cognitive Complexity
- **진단**: 함수 '_validate_v2_package_evidence'의 인지 복잡도(Cognitive Complexity)가 27점으로 기준(15점)을 초과합니다.
- **개선 제안**: 중첩 제어 흐름 및 복합 조건식을 단순화하고 Guard Clause(Early Return)를 도입하거나 보조 서브루틴으로 추출하세요.

### [🟡 WARNING] `src/forgeflow/harness.py:1489` - Silent Exception
- **진단**: 'except' 블록에서 예외를 처리하거나 로깅하지 않고 침묵(pass/ellipsis)으로 은폐합니다.
- **개선 제안**: 적절한 로깅을 추가하거나 명시적 예외 처리 또는 상위 재발생(raise)을 고려하세요.

### [🟡 WARNING] `src/forgeflow/harness.py:1505` - Long Function
- **진단**: 함수 '_candidate_disallowed_paths'의 길이가 67줄로 기준(50줄)을 초과합니다.
- **개선 제안**: 함수의 단일 책임 원칙(SRP)을 점검하고 보조 헬퍼 메서드로 분할하세요.

### [🟡 WARNING] `src/forgeflow/harness.py:1505` - High Cognitive Complexity
- **진단**: 함수 '_candidate_disallowed_paths'의 인지 복잡도(Cognitive Complexity)가 21점으로 기준(15점)을 초과합니다.
- **개선 제안**: 중첩 제어 흐름 및 복합 조건식을 단순화하고 Guard Clause(Early Return)를 도입하거나 보조 서브루틴으로 추출하세요.

### [🟡 WARNING] `src/forgeflow/harness.py:1561` - Deep Nesting
- **진단**: 코드 블록의 중첩 깊이가 4단계로 가독성이 저하됩니다.
- **개선 제안**: Early return(Guard Clause)을 도입하거나 내부 로직을 별도 함수로 추출하세요.

### [🟡 WARNING] `src/forgeflow/harness.py:1563` - Deep Nesting
- **진단**: 코드 블록의 중첩 깊이가 4단계로 가독성이 저하됩니다.
- **개선 제안**: Early return(Guard Clause)을 도입하거나 내부 로직을 별도 함수로 추출하세요.

### [🟡 WARNING] `src/forgeflow/harness.py:1565` - Deep Nesting
- **진단**: 코드 블록의 중첩 깊이가 4단계로 가독성이 저하됩니다.
- **개선 제안**: Early return(Guard Clause)을 도입하거나 내부 로직을 별도 함수로 추출하세요.

### [🟡 WARNING] `src/forgeflow/harness.py:1577` - High Cognitive Complexity
- **진단**: 함수 '_parse_evidence_block'의 인지 복잡도(Cognitive Complexity)가 18점으로 기준(15점)을 초과합니다.
- **개선 제안**: 중첩 제어 흐름 및 복합 조건식을 단순화하고 Guard Clause(Early Return)를 도입하거나 보조 서브루틴으로 추출하세요.

### [🟡 WARNING] `src/forgeflow/harness.py:1634` - Long Function
- **진단**: 함수 '_validate_evidence'의 길이가 61줄로 기준(50줄)을 초과합니다.
- **개선 제안**: 함수의 단일 책임 원칙(SRP)을 점검하고 보조 헬퍼 메서드로 분할하세요.

### [🟡 WARNING] `src/forgeflow/harness.py:1634` - High Cognitive Complexity
- **진단**: 함수 '_validate_evidence'의 인지 복잡도(Cognitive Complexity)가 44점으로 기준(15점)을 초과합니다.
- **개선 제안**: 중첩 제어 흐름 및 복합 조건식을 단순화하고 Guard Clause(Early Return)를 도입하거나 보조 서브루틴으로 추출하세요.

### [🟡 WARNING] `src/forgeflow/harness.py:1730` - Long Function
- **진단**: 함수 '_has_candidate_binding'의 길이가 54줄로 기준(50줄)을 초과합니다.
- **개선 제안**: 함수의 단일 책임 원칙(SRP)을 점검하고 보조 헬퍼 메서드로 분할하세요.

### [🟡 WARNING] `src/forgeflow/harness.py:34` - Unused Import
- **진단**: 임포트된 식별자 'CoreLifecycleValidationError'이 모듈 내부에서 한 번도 사용되지 않았습니다.
- **개선 제안**: 불필요한 임포트를 제거하여 코드 위생과 로딩 성능을 개선하세요.

### [🟡 WARNING] `src/forgeflow/harness.py:36` - Unused Import
- **진단**: 임포트된 식별자 'core_state_digest'이 모듈 내부에서 한 번도 사용되지 않았습니다.
- **개선 제안**: 불필요한 임포트를 제거하여 코드 위생과 로딩 성능을 개선하세요.

---

## 🧠 2축 심층 감사 가이드 (Stage 2: LLM Axis)
- **Standards Axis**: Fowler 12종 리팩토링 스멜 및 리포지토리 코딩 규약 준수 검증.
- **Spec Axis**: PRD/명세 대비 요구사항 누락, 스코프 초과, 오구현 검증.