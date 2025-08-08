# Util Package

LangGraph 그래프 생성과 공통 유틸리티 기능을 제공하는 패키지입니다.

## 📁 구조

```
util/
├── __init__.py
└── graph_generator.py     # LangGraph 그래프 생성 유틸리티
```

## 🎯 주요 기능

### 🏗️ 그래프 자동 생성
- **노드 기반 그래프 구성**: 함수를 노드로 자동 변환
- **엣지 자동 연결**: 노드 간 의존성 기반 자동 연결
- **조건부 라우팅**: 복잡한 분기 로직 지원
- **시각적 디버깅**: LangGraph Studio 호환 구조

### 🔄 유연한 노드 시스템
- **시작 노드**: 그래프 진입점 정의
- **종료 노드**: 그래프 종료점 정의
- **중간 노드**: 비즈니스 로직 처리
- **조건부 노드**: 동적 라우팅 지원

## 🚀 사용법

### 기본 그래프 생성
```python
from src.util.graph_generator import create_graph, AugmentedNode

# 노드 정의
def process_data(state):
    return {"processed": True}

def validate_data(state):
    return {"valid": state.get("processed", False)}

# 그래프 구성
nodes = [
    AugmentedNode.start("process", process_data, ["validate"]),
    AugmentedNode.end("validate", validate_data)
]

# 그래프 생성
graph = create_graph(nodes, state_schema=MyState)
```

### 조건부 라우팅
```python
from src.util.graph_generator import ConditionalEdge

def route_condition(state):
    return "success" if state.get("valid") else "error"

conditional_node = AugmentedNode(
    name="process",
    implementation=process_data,
    conditional_edge=ConditionalEdge(
        condition_checker=route_condition,
        destinations={"success": "next_step", "error": "error_handler"}
    )
)
```

## 🏗️ AugmentedNode 클래스

### 노드 타입별 생성

#### 시작 노드
```python
start_node = AugmentedNode.start(
    name="entry_point",
    implementation=entry_function,
    destinations=["next_node"]
)
```

#### 종료 노드
```python
end_node = AugmentedNode.end(
    name="final_step", 
    implementation=final_function
)
```

#### 조건부 노드
```python
conditional_node = AugmentedNode(
    name="decision_point",
    implementation=decision_function,
    conditional_edge=ConditionalEdge(
        condition_checker=lambda state: "path_a" if state.get("condition") else "path_b",
        destinations={"path_a": "node_a", "path_b": "node_b"}
    )
)
```

## 🔧 ConditionalEdge 시스템

### 조건 함수 정의
```python
def smart_routing(state):
    """상태 기반 지능형 라우팅"""
    if state.get("error"):
        return "error_handling"
    elif state.get("needs_validation"):
        return "validation"
    else:
        return "continue"

conditional_edge = ConditionalEdge(
    condition_checker=smart_routing,
    destinations={
        "error_handling": "error_node",
        "validation": "validate_node", 
        "continue": "next_node"
    }
)
```

### 복잡한 조건 로직
```python
def complex_condition(state):
    """복합 조건 기반 라우팅"""
    score = state.get("score", 0)
    user_type = state.get("user_type", "guest")
    
    if score > 90 and user_type == "premium":
        return "premium_path"
    elif score > 70:
        return "standard_path"
    else:
        return "basic_path"
```

## 📊 그래프 생성 과정

### 1. 노드 등록
```python
# 그래프 생성 시 자동으로 수행되는 과정
📌 노드 추가 시작...
├── ✅ 노드 추가: load_data
├── ✅ 노드 추가: process_data  
├── ✅ 노드 추가: validate_data
├── ✅ 노드 추가: save_results
```

### 2. 엔트리 포인트 설정
```python
🚪 엔트리 포인트 설정 시작...
├── 엔트리 포인트 설정: load_data
```

### 3. 엣지 연결
```python
➡️ 엣지 추가 시작...
├── 일반 엣지 추가: load_data -> process_data
├── 일반 엣지 추가: process_data -> validate_data
├── 🔀조건부 엣지 추가: validate_data -> ['save_results', 'error_handler']
```

### 4. 종료 포인트 설정
```python
🏁 종료 포인트 설정 시작...
├── ✅ 종료 포인트 설정: save_results
├── ✅ 종료 포인트 설정: error_handler
```

## 🎯 실제 사용 예시

### Review 그래프 생성
```python
from src.util.graph_generator import create_graph, AugmentedNode
from src.review.states import State

# 리뷰 분석 노드들
def load_reviews(state): 
    # 리뷰 로딩 로직
    pass

def filter_reviews(state):
    # 필터링 로직
    pass

def pick_candidates(state):
    # 후보 선정 로직
    pass

# 그래프 구성
review_nodes = [
    AugmentedNode.start("load_reviews", load_reviews, ["filter_reviews"]),
    AugmentedNode("filter_reviews", filter_reviews, destinations=["pick_candidates"]),
    AugmentedNode.end("pick_candidates", pick_candidates)
]

# 그래프 생성
review_graph = create_graph(review_nodes, state_schema=State)
```

### Title Summary 그래프 생성
```python
from src.title_summary.states import State as TitleState

def validate_input(state):
    return {"validated": True}

def generate_titles(state):
    # 제목 생성 로직
    pass

def generate_summaries(state):
    # 요약 생성 로직  
    pass

def needs_summaries(state):
    return "summaries" if state.get("summary_required_reviews") else "finalize"

title_nodes = [
    AugmentedNode.start("validate_input", validate_input, ["generate_titles"]),
    AugmentedNode("generate_titles", generate_titles, 
                  conditional_edge=ConditionalEdge(
                      condition_checker=needs_summaries,
                      destinations={"summaries": "generate_summaries", "finalize": "finalize_results"}
                  )),
    AugmentedNode("generate_summaries", generate_summaries, ["finalize_results"]),
    AugmentedNode.end("finalize_results", lambda state: {"status": "완료"})
]

title_graph = create_graph(title_nodes, state_schema=TitleState)
```

## 🔍 디버깅 기능

### 그래프 생성 로그
```python
# 자동으로 생성되는 상세 로그
🔧 그래프 생성 중...
   📌 노드 추가 시작...
   ├── ✅ 노드 추가: validate_input
   ├── ✅ 노드 추가: generate_titles
   ├── ✅ 노드 추가: generate_summaries
   ├── ✅ 노드 추가: finalize_results
   🚪 엔트리 포인트 설정 시작...
   ├── 엔트리 포인트 설정: validate_input
   ➡️ 엣지 추가 시작...
   ├── 일반 엣지 추가: validate_input -> generate_titles
   ├── 🔀조건부 엣지 추가: generate_titles -> ['generate_summaries', 'finalize_results']
   ├── 일반 엣지 추가: generate_summaries -> finalize_results
   🏁 종료 포인트 설정 시작...
     ✅ 종료 포인트 설정: finalize_results
✅ 그래프 생성 완료!
```

### 그래프 구조 검증
```python
# 그래프 생성 후 자동 검증
- 시작 노드 존재 확인
- 종료 노드 도달 가능성 확인  
- 무한 루프 방지 검증
- 조건부 엣지 유효성 검증
```

## 📋 Dependencies

```python
# 핵심 의존성
"langgraph>=0.6.3",           # 그래프 실행 엔진
"typing-extensions>=4.14.1",  # 타입 힌트 확장

# 유틸리티
"dataclasses",                # 데이터클래스 (Python 3.7+)
"enum",                       # 열거형
```

## 🎨 확장 가능성

### 커스텀 노드 타입
```python
class CustomNode(AugmentedNode):
    """특별한 기능을 가진 커스텀 노드"""
    
    def __init__(self, name: str, implementation: callable, **kwargs):
        super().__init__(name, implementation, **kwargs)
        self.custom_property = kwargs.get("custom_property")
```

### 그래프 템플릿
```python
def create_analysis_graph(nodes: List[AugmentedNode], state_schema):
    """분석용 그래프 템플릿"""
    # 공통 전처리 노드 자동 추가
    preprocessing_node = AugmentedNode.start("preprocess", preprocess_data, [nodes[0].name])
    all_nodes = [preprocessing_node] + nodes
    
    return create_graph(all_nodes, state_schema)
```

### 동적 그래프 생성
```python
def create_dynamic_graph(config: dict):
    """설정 기반 동적 그래프 생성"""
    nodes = []
    for node_config in config["nodes"]:
        node = AugmentedNode(
            name=node_config["name"],
            implementation=get_function_by_name(node_config["function"]),
            destinations=node_config.get("destinations", [])
        )
        nodes.append(node)
    
    return create_graph(nodes, config["state_schema"])
```

## ⚠️ 주의사항

1. **노드 이름 중복**: 같은 이름의 노드는 생성할 수 없음
2. **순환 참조**: 무한 루프를 방지하기 위한 검증 필요
3. **상태 스키마**: 모든 노드가 동일한 상태 스키마를 사용해야 함
4. **메모리 관리**: 복잡한 그래프는 메모리 사용량 주의
5. **에러 처리**: 노드 함수 내부에서 발생하는 예외 처리 필요

## 🚀 성능 최적화

### 지연 로딩
```python
# 노드 함수를 필요할 때만 로드
def lazy_load_function(function_name: str):
    def wrapper(state):
        func = import_function(function_name)
        return func(state)
    return wrapper
```

### 병렬 처리
```python
# 독립적인 노드들의 병렬 실행 (향후 지원)
parallel_nodes = [
    AugmentedNode("task_a", task_a_function, parallel=True),
    AugmentedNode("task_b", task_b_function, parallel=True)
]
```

## 🎯 사용 권장사항

1. **단순함 유지**: 복잡한 로직은 노드 내부에서 처리
2. **상태 불변성**: 노드에서 상태를 직접 수정하지 말고 새 상태 반환
3. **에러 전파**: 예외 발생 시 적절한 에러 상태로 전환
4. **테스트 가능성**: 각 노드 함수를 독립적으로 테스트 가능하게 설계
5. **문서화**: 복잡한 조건부 로직은 충분한 주석 제공
