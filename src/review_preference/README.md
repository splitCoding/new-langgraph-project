# Review Preference Package

사용자의 리뷰 선호도를 분석하고 BEST 리뷰 선정 기준을 생성하는 패키지입니다.

## 📁 구조

```
review_preference/
├── __init__.py     # 패키지 초기화
└── graph.py        # 리뷰 선호도 분석 그래프
```

## 🎯 기능

### 리뷰 타입별 기준 생성
- 사용자가 선택한 리뷰 타입 분석
- AI를 통한 맞춤형 평가 기준 자동 생성
- 다양한 리뷰 타입 지원:
  - 📷 포토 리뷰
  - 💬 솔직한 리뷰  
  - 😊 긍정적인 리뷰
  - 👍 사용경험 리뷰
  - ✏️ 사용자 정의 타입

### 지능형 기준 추천
- GPT-4를 활용한 맥락적 기준 생성
- 리뷰 타입별 특화된 평가 항목 제안
- 사용자 추가 요구사항 반영

## 🚀 사용법

```python
from src.review_preference.graph import graph

# 리뷰 선호도 분석
result = graph.invoke({
    "selected_types": ["포토 리뷰", "긍정적인 리뷰"],
    "additional_criteria": ["빠른 배송", "포장 상태"]
})

print(result["criteria_by_type"])
```

## 📊 입력/출력 형식

### 입력 (State)
```python
{
    "selected_types": ["포토 리뷰", "솔직한 리뷰"],  # 선택된 리뷰 타입
    "additional_criteria": ["배송 속도", "포장"]     # 추가 기준
}
```

### 출력
```python
{
    "criteria_by_type": [
        {
            "type": "포토 리뷰",
            "criteria": ["이미지 품질", "제품 외관", "실제 사용 모습"]
        },
        {
            "type": "솔직한 리뷰", 
            "criteria": ["장단점 균형", "구체적 경험", "실용적 정보"]
        }
    ]
}
```

## 🔧 설정

### 환경변수
```bash
OPENAI_API_KEY=your_openai_api_key_here  # GPT-4 API 키 (필수)
LANGSMITH_API_KEY=your_langsmith_key     # 추적용 (선택)
```

### LLM 설정
- **모델**: GPT-4 (정확한 분석을 위해)
- **Temperature**: 0.3 (일관성과 창의성 균형)
- **Max Tokens**: 1000 (충분한 기준 생성)

## 📋 Dependencies

- `langchain-openai`: OpenAI GPT-4 연동
- `langchain-core`: 프롬프트 및 파서
- `langgraph`: 그래프 실행 엔진

## 🎨 커스터마이징

### 1. 새로운 리뷰 타입 추가
```python
# 기본 기준 사전에 추가
REVIEW_TYPE_CRITERIA = {
    "새로운_타입": ["기준1", "기준2", "기준3"]
}
```

### 2. 프롬프트 최적화
```python
# graph.py의 프롬프트 템플릿 수정
prompt = ChatPromptTemplate.from_template("""
    맞춤형 프롬프트 내용...
""")
```

### 3. 출력 형식 변경
```python
# JSON 스키마 수정으로 출력 구조 변경
output_schema = {
    "type": "object",
    "properties": {
        # 새로운 스키마 정의
    }
}
```

## 🔍 디버깅

### LangSmith 추적
- 프롬프트 입력/출력 확인
- 토큰 사용량 모니터링
- 응답 품질 평가

### 로컬 테스트
```python
# 단위 테스트
python -m pytest tests/test_review_preference.py

# 수동 테스트
python -c "
from src.review_preference.graph import graph
result = graph.invoke({'selected_types': ['포토 리뷰']})
print(result)
"
```

## ⚠️ 주의사항

1. **API 키 필수**: OpenAI API 키 없이는 동작하지 않음
2. **토큰 비용**: GPT-4 사용으로 인한 API 비용 발생
3. **응답 지연**: LLM 호출로 인한 1-3초 응답 지연
4. **한국어 특화**: 한국어 리뷰 분석에 최적화됨
