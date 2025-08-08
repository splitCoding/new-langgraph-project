# Review Package

LangGraph 기반 리뷰 분석 및 점수 매기기 에이전트

## 구조

```
src/review/
├── __init__.py
├── config.py           # 설정 및 구성
├── graph.py            # 기존 그래프 (레거시)
├── graph_refactored.py # 리팩토링된 그래프
├── states.py           # 상태 정의
├── nodes/              # 노드 구현
│   ├── __init__.py
│   ├── data_loader.py  # 데이터 로딩
│   ├── filters.py      # 필터링
│   ├── fusion.py       # 후보 병합
│   └── scoring.py      # 점수 매기기
├── tools/              # LLM 도구
│   ├── __init__.py
│   ├── database.py     # MySQL 데이터베이스 도구
│   └── moderation.py   # OpenAI 컨텐츠 모더레이션
└── utils/              # 유틸리티
    ├── __init__.py
    └── logging.py      # 로깅 설정
```

## 기능

### 1. 데이터베이스 도구 (tools/database.py)

MySQL에서 리뷰 데이터를 조회하는 도구:

- 환경변수 기반 DB 설정
- 미리 정의된 쿼리 및 커스텀 쿼리 지원
- 안전한 쿼리 실행 (SELECT만 허용)
- LangGraph 도구로 사용 가능

**환경변수:**
```bash
DB_HOST=localhost
DB_PORT=3306
DB_NAME=reviews
DB_USER=root
DB_PASSWORD=your_password
DB_CHARSET=utf8mb4
```

**사용 가능한 도구:**
- `query_reviews_by_rating`: 평점별 리뷰 조회
- `query_reviews_with_images`: 이미지 있는 리뷰 조회
- `query_reviews_custom`: 커스텀 쿼리 실행
- `get_review_statistics`: 리뷰 통계 조회

### 2. 컨텐츠 모더레이션 도구 (tools/moderation.py)

OpenAI Moderation API와 커스텀 룰을 사용한 컨텐츠 필터링:

- OpenAI Moderation API 통합
- 한국어 비속어 및 스팸 패턴 감지
- 호출 제한 관리 (기본 60회/분)
- 배치 처리 지원

**사용 가능한 도구:**
- `moderate_text`: 단일 텍스트 모더레이션
- `moderate_review_batch`: 리뷰 배치 모더레이션  
- `filter_safe_reviews`: 안전한 리뷰만 필터링
- `get_moderation_stats`: 모더레이션 통계 조회

### 3. 리팩토링된 구조

#### 노드 모듈 (nodes/)

- **data_loader.py**: 데이터베이스 또는 샘플 데이터 로딩
- **filters.py**: 비즈니스 룰 및 컨텐츠 모더레이션 필터링
- **scoring.py**: LLM을 사용한 다중 관점 점수 매기기
- **fusion.py**: 후보 병합 및 최종 선택

#### 설정 기반 그래프 생성

`config.py`에서 설정을 관리하고 노드 구현을 동적으로 선택:

```python
from src.review.graph_refactored import create_review_graph
from src.review.config import ReviewConfig

# 설정 생성
config = ReviewConfig(
    use_database=True,
    enable_content_moderation=True,
    use_async_processing=False,
    max_candidates=10
)

# 그래프 생성
graph = create_review_graph(config)
```

## 사용법

### 기본 사용

```python
from src.review.graph_refactored import graph

# 상태 정의
initial_state = {
    "mall_id": "mall_123",
    "shop_id": "shop_456",
    "criteria_by_type": [
        {"type": "품질", "criteria": ["성능", "내구성", "디자인"]},
        {"type": "진정성", "criteria": ["솔직함", "경험 기반", "구체성"]},
        {"type": "유용성", "criteria": ["도움됨", "정보성", "실용성"]}
    ]
}

# 그래프 실행
result = graph.invoke(initial_state)
print(result["selected_candidates"])
```

### 도구 직접 사용

```python
from src.review.tools.database import query_reviews_by_rating
from src.review.tools.moderation import moderate_text

# 데이터베이스에서 리뷰 조회
reviews = query_reviews_by_rating("mall_123", "shop_456", min_rating=4)

# 컨텐츠 모더레이션
moderation_result = moderate_text("이 제품 정말 좋아요!", use_openai=True)
print(f"안전한 컨텐츠: {moderation_result['is_safe']}")
```

## 의존성

```toml
dependencies = [
    "langgraph>=0.2.6",
    "langchain-core>=0.1.0", 
    "langchain-openai>=0.1.0",
    "mysql-connector-python>=8.0.0",
    "openai>=1.0.0",
    # ... 기타
]
```