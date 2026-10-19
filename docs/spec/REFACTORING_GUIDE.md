# 🏛️ ForgeFlow 리팩토링 표준 가이드 (REFACTORING_GUIDE.md)

이 문서는 ForgeFlow 프레임워크 코어 및 ForgeFlow를 채택한 프로젝트에서 코드 품질, 인지 부하 제어, 아키텍처 지속 가능성을 담보하기 위해 준수해야 하는 최상위 리팩토링 표준 규격이다.

---

## 1. 핵심 설계 철학: Deep Module & Anti-Overengineering

우리는 스탠퍼드 대학 존 오스터하우트(John Ousterhout) 교수의 *A Philosophy of Software Design*과 마틴 파울러(Martin Fowler)의 *Refactoring*, SonarSource의 *Cognitive Complexity* 모델을 기반으로 단일하고 일관된 설계 철학을 고수한다.

### 1.1 Deep Modules (깊은 모듈 원칙)
- **깊은 모듈(Deep Module)**: 작고 단순하며 직관적인 공개 인터페이스(Interface) 뒤에 강력하고 풍부하며 완성도 높은 구현(Implementation)을 은닉(Information Hiding)한다.
- **얕은 모듈(Shallow Module) 분할 금지**: 단순히 파일이나 함수의 줄 수를 줄이겠다는 명목으로 5~10줄짜리 껍데기 함수나 1회성 헬퍼 파일로 과도하게 파편화하지 않는다. 이는 시스템의 인터페이스 수와 결합도만 급증시켜 전체적인 인지 부하(Cognitive Load)를 가중시킨다.
- **진짜 리팩토링 대상**: 파일이 긴 것 자체가 문제가 아니라, **인터페이스가 복잡하고 내부 추상화가 뒤섞여 있거나(Shallow), 한 번에 이해할 수 없을 만큼 인지 복잡도(Cognitive Complexity)가 높을 때** 리팩토링을 수행한다.

### 1.2 Anti-Overengineering 3대 수칙
1. **No Fragmented Shallow Modules**: 의미 없는 1회성 헬퍼를 위해 별도 파일을 양산하지 않고 응집된 단일 모듈을 유지한다.
2. **Rule of Three**: 최소 3회 이상의 실질적 중복이나 상이한 구현 요구가 발생하기 전까지 섣부른 조기 추상화(ABC/디자인 패턴 남용)를 배격한다.
3. **No Pass-through**: 단순히 인자를 다음 계층으로 넘겨주기만 하는 불필요한 중간 계층(Middle Man / Passthrough Methods)을 만들지 않는다.

---

## 2. 정량적 소스 관리 및 리팩토링 임계치 (Thresholds)

ForgeFlow 정적 분석 엔진(`smell_detector.py`)은 Python 3.10+ 표준 라이브러리(`ast`)만으로 다음 정량적 임계치를 검증한다.

### 2.1 모듈/파일 레벨 (File LOC)
| 구분 | 파일 줄 수 (LOC) | 판정 및 조치 가이드 |
|---|---|---|
| **Healthy Zone** | **≤ 400 LOC** | 정상: 단일 관심사와 명확한 인터페이스를 품은 건강한 Deep Module |
| **Soft Warning** | **> 500 LOC** | **리팩토링 권고 (Warning)**: 단일 책임 원칙(SRP) 점검 및 응집된 하위 모듈 분할 검토 |
| **Critical Gate** | **> 800 LOC** | **아키텍처 승인 필요 (Critical)**: God Module 위험. 패키지 디렉터리로 승격(Package Promotion)하거나 Gate 증적(`DESIGN.md`) 내 `Architecture Exception` 승인 사유 기록 강제 |

### 2.2 함수/메서드 레벨 (Complexity & Metrics)
| 메트릭 | 임계치 | 위반 시 위험 및 조치 가이드 |
|---|---|---|
| **Function LOC** | **> 50 LOC** | Long Function 경고. 단일 책임 원칙 점검 및 논리적 서브루틴 분할 검토 |
| **Cognitive Complexity** | **> 15** | SonarQube 표준 인지 복잡도 초과. 중첩 제어 흐름 및 복합 조건식을 단순화하여 가독성 개선 |
| **Nesting Depth** | **≥ 4단계** | Deep Nesting 경고. Early Return / Guard Clause를 도입하여 들여쓰기 1~2단계로 평탄화 |
| **Parameter Count** | **> 5개** | Too Many Parameters 경고. Dataclass / DTO 파라미터 객체로 번들링 권장 |

### 2.3 클래스 레벨
- **Method Count > 15개**: Large Class 경고 (역할 분리 및 컴포지션 검토).

---

## 3. 리팩토링 실전 패턴 (Best Practices)

### 3.1 Pattern 1: Guard Clause (Early Return)를 통한 평탄화
중첩된 `if` 문을 조기 반환(`return`, `continue`, `break`, `raise`)으로 평탄화하여 중첩 깊이와 인지 복잡도를 낮춘다.

```python
# 🔴 Bad: Deep Nesting (Nesting Depth 3+, High Cognitive Complexity)
def process_item(item):
    if item is not None:
        if item.is_valid():
            if not item.is_processed():
                item.run()

# 🟢 Good: Guard Clause (Early Return)
def process_item(item):
    if item is None or not item.is_valid():
        return
    if item.is_processed():
        return
    item.run()
```

### 3.2 Pattern 2: DTO / Parameter Object 번들링
5개 이상의 독립 파라미터가 함수에 전달될 경우, 불변 Dataclass나 명시적 DTO로 묶어 인터페이스를 깊고 단순하게 만든다.

### 3.3 Pattern 3: Subpackage Promotion (800 LOC 초과 시)
단일 파일 모듈이 800줄을 초과하여 여러 책임을 안게 될 경우, 단일 파일을 패키지 디렉터리로 승격한다:
```text
src/forgeflow/module.py (1,200줄)
  └── 승격 ➔
src/forgeflow/module/
    ├── __init__.py      # 파사드(Facade): 기존 외부 인터페이스 100% 보존
    ├── core.py          # 핵심 도메인 로직
    ├── parser.py        # 파싱 로직
    └── validator.py     # 검증 로직
```
패키지 승격 시 기존 임포트 경로(`from forgeflow.module import ...`)를 `__init__.py`에서 re-export하여 외부 호출부의 하위 호환성을 100% 유지해야 한다.

---

## 4. Stage 4 격리 구현 및 자가 치유(Loop 2/3) 체크리스트

1. **사전 검사**: 새 기능 작성 시 `forgeflow review`를 실행하여 새로 도입된 함수가 인지 복잡도 15점을 넘지 않는지 확인한다.
2. **비대화 억제**: 수정된 파일이 500줄을 초과하면 리팩토링 가능성을 점검하고, 800줄을 초과할 경우 `DESIGN.md`에 명시적 예외 사유가 기록되어 있는지 확인한다.
3. **무결성 유지**: 리팩토링 진행 전후로 단위 테스트(`python3 -m unittest`)를 실행하여 동작 불변성을 엄격히 보장한다.
