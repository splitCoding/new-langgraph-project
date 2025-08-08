# Title Summary Package

선정된 BEST 리뷰들의 제목과 요약을 AI로 생성하는 패키지입니다.

## 📁 구조

```
title_summary/
├── __init__.py     # 패키지 초기화
├── graph.py        # 제목/요약 생성 그래프
└── states.py       # 상태 정의 및 타입
```

## 🎯 주요 기능

### 🏷️ 지능형 제목 생성
- **다양한 스타일**: 간결한, 창의적인, 전문적인, 감정적인, 설명적인
- **사용자 정의 요구사항**: 제품명 포함, 특정 키워드 강조 등
- **선택적 재생성**: 생성된 제목 중 일부만 다시 생성 가능
- **재생성 요구사항**: 기존 요구사항 + 추가 수정 요청 반영

### 📄 맞춤형 요약 생성
- **스타일 옵션**: 상세한, 간단한, 감정 중심, 기능 중심, 구매 결정 도움
- **핵심 정보 추출**: 리뷰의 장단점, 사용 경험, 추천 포인트
- **가독성 최적화**: 구조화된 요약 형식

### 🔄 고급 재생성 시스템
- **부분 재생성**: 전체가 아닌 선택된 항목만 재생성
- **요구사항 누적**: 기존 + 새로운 요구사항 통합 적용
- **상태 관리**: 재생성 과정의 안전한 상태 전환

## 🚀 사용법

### 기본 사용
```python
from src.title_summary.graph import graph

# 제목과 요약 생성
result = graph.invoke({
    "selected_reviews": [
        {"id": 1, "text": "정말 좋은 제품입니다...", "rating": 5},
        {"id": 2, "text": "배송이 빨라서 만족...", "rating": 4}
    ],
    "summary_required_reviews": [
        {"id": 1, "text": "정말 좋은 제품입니다...", "rating": 5}
    ],
    "title_style": "창의적인",
    "summary_style": "상세한",
    "title_custom_requirements": "제품명을 포함해주세요",
    "regenerate_requirements": ""
})
```

### 재생성 사용
```python
# 특정 제목들만 재생성
result = graph.invoke({
    "selected_reviews": [selected_reviews],  # 재생성할 리뷰들만
    "title_style": "간결한",
    "title_custom_requirements": "제품명 포함",
    "regenerate_requirements": "더 짧게 만들어주세요"
})
```

## 📊 데이터 구조

### State 정의
```python
class State(TypedDict):
    # 입력
    selected_reviews: List[SelectedReview]           # 제목 생성 대상 리뷰
    summary_required_reviews: List[SelectedReview]   # 요약 생성 대상 리뷰
    title_style: str                                 # 제목 스타일
    summary_style: str                               # 요약 스타일
    title_custom_requirements: str                   # 사용자 정의 요구사항
    regenerate_requirements: str                     # 재생성 시 추가 요구사항
    
    # 출력
    generated_titles: List[GeneratedTitle]           # 생성된 제목들
    generated_summaries: List[GeneratedSummary]      # 생성된 요약들
    final_results: Dict[str, Any]                    # 최종 결과
```

### 입력 데이터 형식
```python
{
    "selected_reviews": [
        {
            "id": 1,
            "text": "리뷰 내용...",
            "rating": 5,
            "created_at": "2024-01-01",
            "image_exists": True
        }
    ],
    "title_style": "창의적인",
    "summary_style": "상세한",
    "title_custom_requirements": "제품명을 포함해주세요",
    "regenerate_requirements": "더 짧게 만들어주세요"
}
```

### 출력 데이터 형식
```python
{
    "final_results": {
        "titles": [
            {"review_id": 1, "title": "생성된 제목"}
        ],
        "summaries": [
            {"review_id": 1, "summary": "생성된 요약"}
        ]
    },
    "status": "완료"
}
```

## 🎨 제목 스타일 가이드

| 스타일 | 특징 | 예시 |
|--------|------|------|
| **간결한** | 핵심만 담은 짧은 제목 | "완벽한 가성비 제품" |
| **창의적인** | 재미있고 독창적인 표현 | "이 제품, 내 마음을 훔쳤다!" |
| **전문적인** | 상품의 기능과 성능 중심 | "고성능 프로세서로 업무 효율 극대화" |
| **감정적인** | 감정과 느낌 중심 | "행복한 쇼핑, 만족스러운 경험" |
| **설명적인** | 구체적이고 상세한 설명 | "빠른 배송과 완벽한 포장의 프리미엄 제품" |

## 🔧 설정 및 환경변수

### 필수 환경변수
```bash
OPENAI_API_KEY=your_openai_api_key_here  # GPT-4o-mini API 키
```

### 선택 환경변수
```bash
LANGSMITH_API_KEY=your_langsmith_key     # LangSmith 추적
LANGSMITH_PROJECT=review-agent           # 프로젝트 이름
```

### LLM 설정
- **모델**: GPT-4o-mini (비용 효율성과 성능 균형)
- **Temperature**: 0.3 (일관성 유지)
- **Max Tokens**: 500 (제목/요약에 충분한 길이)

## 📋 Dependencies

```python
# 핵심 의존성
"langchain-openai>=0.3.28",    # OpenAI 모델 연동
"langchain-core>=0.3.72",      # 프롬프트 및 파서
"langgraph>=0.6.3",            # 그래프 실행 엔진

# 데이터 처리
"tiktoken>=0.10.0",            # 토큰 계산
"beautifulsoup4>=4.13.4",      # HTML 정리
```

## 🔍 디버깅 및 모니터링

### 로깅
```python
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 실행 중 로그 확인
logger.info(f"Generating titles for {len(reviews)} reviews")
```

### LangSmith 추적
- 프롬프트 입력/출력 상세 확인
- 토큰 사용량 및 비용 모니터링
- 생성 품질 평가 및 개선

### 수동 테스트
```bash
# 단위 테스트 실행
python -m pytest tests/test_title_summary.py

# 통합 테스트
python -c "
from src.title_summary.graph import graph
test_data = {'selected_reviews': [{'id': 1, 'text': '좋은 제품', 'rating': 5}]}
result = graph.invoke(test_data)
print(result)
"
```

## ⚡ 성능 최적화

### 배치 처리
- 여러 리뷰를 한 번에 처리하여 API 호출 최소화
- 토큰 한도 내에서 최대한 많은 리뷰 처리

### 오류 처리
- API 호출 실패 시 기본 제목/요약으로 폴백
- JSON 파싱 오류 시 안전한 예외 처리
- 네트워크 오류 시 재시도 로직

### 캐싱 (향후 개선)
```python
# 동일한 리뷰에 대한 결과 캐싱으로 비용 절약
@cache
def generate_title(review_text: str, style: str) -> str:
    # 캐싱된 결과 반환
    pass
```

## 🎯 사용 사례

### 1. 이커머스 플랫폼
- BEST 리뷰 제목 자동 생성
- 고객 리뷰 요약으로 구매 결정 지원
- 상품 페이지 콘텐츠 자동화

### 2. 마케팅 자료
- 고객 후기 기반 마케팅 문구 생성
- SNS 콘텐츠용 매력적인 제목 생성
- 광고 카피 아이디어 발굴

### 3. 고객 서비스
- 리뷰 분석을 통한 개선점 도출
- 고객 만족도 핵심 요소 파악
- 제품 강점 요약 자료 생성

## ⚠️ 주의사항

1. **API 비용**: GPT 모델 사용으로 인한 비용 발생
2. **응답 시간**: LLM 호출로 인한 2-5초 지연
3. **한국어 최적화**: 한국어 리뷰에 특화된 프롬프트
4. **토큰 제한**: 매우 긴 리뷰의 경우 자동 요약 후 처리
5. **재생성 제한**: 동일 세션 내에서만 재생성 상태 유지
