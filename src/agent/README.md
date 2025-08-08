# Agent Package

기본 LangGraph 에이전트 패키지입니다.

## 📁 구조

```
agent/
├── __init__.py     # 패키지 초기화
└── graph.py        # 기본 에이전트 그래프 정의
```

## 🎯 기능

### `graph.py`
- 기본 LangGraph 에이전트 그래프 구현
- 설정 가능한 파라미터를 통한 동적 응답
- LangGraph Studio와 호환되는 구조

## 🚀 사용법

```python
from src.agent.graph import graph

# 그래프 실행
result = graph.invoke({"input": "Hello"})
```

## 🔧 설정

### Configuration 클래스
- 에이전트의 동작을 제어하는 설정 파라미터
- LangGraph Studio에서 실시간 수정 가능

### 환경변수
- `OPENAI_API_KEY`: OpenAI API 키 (필수)
- `LANGSMITH_API_KEY`: LangSmith 추적용 키 (선택)

## 📋 Dependencies

- `langgraph`: 그래프 실행 엔진
- `langchain`: LLM 체인 관리
- `langchain-openai`: OpenAI 모델 연동

## 🎨 확장 방법

1. **새 노드 추가**: `graph.py`에 새로운 함수 정의
2. **에지 수정**: 노드 간 연결 관계 변경
3. **설정 확장**: `Configuration` 클래스에 새 파라미터 추가

## 📊 LangGraph Studio

이 에이전트는 LangGraph Studio에서 시각적으로 디버깅할 수 있습니다:

1. `langgraph dev` 명령으로 서버 시작
2. Studio UI에서 그래프 구조 확인
3. 각 노드의 상태와 출력 실시간 모니터링
