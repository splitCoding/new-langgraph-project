# BEST 리뷰 분석 시스템 (LangGraph Project)

[![CI](https://github.com/langchain-ai/new-langgraph-project/actions/workflows/unit-tests.yml/badge.svg)](https://github.com/langchain-ai/new-langgraph-project/actions/workflows/unit-tests.yml)
[![Integration Tests](https://github.com/langchain-ai/new-langgraph-project/actions/workflows/integration-tests.yml/badge.svg)](https://github.com/langchain-ai/new-langgraph-project/actions/workflows/integration-tests.yml)

**AI 기반 BEST 리뷰 자동 선정 및 제목/요약 생성 시스템**

LangGraph와 GPT-4를 활용하여 대량의 고객 리뷰 데이터에서 최고 품질의 BEST 리뷰를 자동으로 선정하고, 매력적인 제목과 요약을 생성하는 엔드투엔드 솔루션입니다.

<div align="center">
  <img src="./static/studio_ui.png" alt="Graph view in LangGraph studio UI" width="75%" />
</div>

## 🎯 주요 기능

### 🏆 지능형 BEST 리뷰 선정
- **다차원 평가**: 품질, 상세도, 감정, 경험 등 종합 평가
- **맞춤형 기준**: 사용자 선택 리뷰 타입별 특화 기준 자동 생성
- **AI 점수 매기기**: GPT-4 기반 정교한 리뷰 평가
- **후보 추천**: 상위 10개 후보 리뷰 자동 선별

### 📝 제목/요약 자동 생성
- **다양한 스타일**: 간결한, 창의적인, 전문적인, 감정적인, 설명적인
- **사용자 정의 요구사항**: 제품명 포함, 키워드 강조 등 맞춤 요청
- **선택적 재생성**: 마음에 들지 않는 제목만 부분 재생성
- **재생성 요구사항**: 기존 + 추가 요구사항 통합 반영

### 🎨 직관적인 웹 인터페이스
- **단계별 가이드**: 리뷰 타입 선택부터 DB 저장까지 전 과정
- **실시간 피드백**: 각 단계별 즉시 결과 확인
- **반응형 디자인**: 모바일부터 데스크톱까지 최적화
- **접근성 지원**: 키보드 내비게이션 및 스크린 리더 호환

## 🏗️ 시스템 아키텍처

```
📦 BEST 리뷰 분석 시스템
├── 🎨 UI Layer (Streamlit)
│   ├── 매장 선택 및 관리
│   ├── 대화형 리뷰 분석 워크플로우
│   └── 결과 시각화 및 DB 저장
├── 🤖 AI Processing Layer (LangGraph)
│   ├── 리뷰 선호도 분석 (review_preference)
│   ├── BEST 리뷰 선정 (review)
│   └── 제목/요약 생성 (title_summary)
├── 🛠️ Utility Layer
│   ├── 그래프 자동 생성 (util)
│   └── 공통 유틸리티
└── 🗄️ Data Layer
    ├── MySQL 데이터베이스 연동
    └── 환경변수 기반 설정 관리
```

## 🚀 빠른 시작

### 1. 프로젝트 설치
```bash
git clone <repository-url>
cd new-langgraph-project
pip install -e . "langgraph-cli[inmem]"
```

### 2. 환경 설정
```bash
# 환경 파일 생성
cp .env.example .env

# .env 파일에 실제 값 입력
DB_HOST=your_database_host
DB_PASSWORD=your_database_password
OPENAI_API_KEY=your_openai_api_key
LANGSMITH_API_KEY=your_langsmith_api_key  # 선택사항
```

### 3. LangGraph 서버 시작
```bash
langgraph dev
```

### 4. 웹 인터페이스 실행
```bash
# 새 터미널에서
streamlit run src/ui/apps/review_agent_chat.py --server.port 8501
```

### 5. 브라우저 접속
- **로컬**: http://localhost:8501
- **네트워크**: http://[your-ip]:8501

## 📋 사용 워크플로우

### 1️⃣ 매장 선택
- 사이드바에서 분석할 매장 선택
- DB에서 실시간 매장 목록 로딩

### 2️⃣ 리뷰 타입 선택
- 📷 **포토 리뷰**: 이미지가 포함된 시각적 리뷰
- 💬 **솔직한 리뷰**: 객관적이고 균형잡힌 평가
- 😊 **긍정적인 리뷰**: 만족도가 높은 추천 리뷰
- 👍 **사용경험 리뷰**: 실제 사용 경험이 담긴 리뷰
- ✏️ **커스텀 타입**: 사용자 정의 리뷰 타입

### 3️⃣ AI 기준 생성
- 선택된 리뷰 타입별 맞춤 평가 기준 자동 생성
- 추가 고려사항 입력 가능 (배송, 포장, 서비스 등)

### 4️⃣ BEST 리뷰 후보 확인
- AI가 선정한 상위 10개 후보 리뷰 표시
- 각 리뷰의 종합 점수 및 상세 내용 확인

### 5️⃣ 최종 리뷰 선택
- 후보 중에서 실제 BEST 리뷰로 사용할 리뷰들 선택
- 선택된 리뷰들에 대해 제목 생성 진행

### 6️⃣ 제목 생성 및 커스터마이징
- **스타일 선택**: 간결한, 창의적인, 전문적인, 감정적인, 설명적인
- **추가 요구사항**: 제품명 포함, 특정 키워드 강조 등
- **선택적 재생성**: 마음에 들지 않는 제목만 체크하여 재생성
- **재생성 요구사항**: 더 짧게, 다른 톤으로 등 추가 수정 요청

### 7️⃣ 요약 생성 (선택사항)
- 제목과 함께 요약도 필요한 리뷰 선택
- 요약 스타일 선택: 상세한, 간단한, 감정 중심, 기능 중심, 구매 결정 도움

### 8️⃣ 최종 결과 확인 및 저장
- 생성된 제목과 요약이 포함된 최종 BEST 리뷰 확인
- 데이터베이스에 결과 저장

## 🏗️ 개발 및 커스터마이징

### 📦 패키지 구조
- **[src/agent/](src/agent/)**: 기본 LangGraph 에이전트
- **[src/review/](src/review/)**: BEST 리뷰 선정 엔진
- **[src/review_preference/](src/review_preference/)**: 리뷰 선호도 분석
- **[src/title_summary/](src/title_summary/)**: 제목/요약 생성 시스템
- **[src/ui/](src/ui/)**: Streamlit 웹 인터페이스
- **[src/util/](src/util/)**: 공통 유틸리티 및 그래프 생성기

### 🛠️ 주요 기술 스택
- **LangGraph**: 복잡한 AI 워크플로우 오케스트레이션
- **OpenAI GPT-4/GPT-4o-mini**: 텍스트 분석 및 생성
- **Streamlit**: 반응형 웹 인터페이스
- **MySQL**: 리뷰 데이터 저장 및 관리
- **LangSmith**: AI 모델 추적 및 디버깅

### 🔧 설정 파라미터

#### 환경변수 (.env)
```bash
# 데이터베이스 설정
DB_HOST=your_database_host
DB_PORT=3306
DB_USER=your_username
DB_PASSWORD=your_password
DB_NAME=your_database
DB_CHARSET=utf8mb4

# AI 모델 API
OPENAI_API_KEY=your_openai_api_key

# 모니터링 (선택사항)
LANGSMITH_TRACING="true"
LANGSMITH_API_KEY=your_langsmith_api_key
LANGSMITH_PROJECT="review-agent"
```

#### LLM 모델 설정
- **리뷰 분석**: GPT-4 (정확성 중시)
- **제목/요약 생성**: GPT-4o-mini (비용 효율성)
- **Temperature**: 0.3 (일관성과 창의성 균형)

### 🎨 커스터마이징 가이드

#### 1. 새로운 리뷰 타입 추가
```python
# src/ui/models/data.py
REVIEW_TYPE_CRITERIA = {
    "새로운_타입": ["평가기준1", "평가기준2", "평가기준3"]
}
```

#### 2. 제목 스타일 확장
```python
# src/ui/components/chat_components.py
title_style = st.radio(
    "제목 스타일 선택:",
    ["간결한", "창의적인", "전문적인", "감정적인", "설명적인", "새로운_스타일"]
)
```

#### 3. 평가 기준 조정
```python
# src/review/nodes/scoring.py
# 점수 가중치 및 평가 기준 수정
```

### 🔍 디버깅 및 모니터링

#### LangGraph Studio
```bash
# LangGraph 서버 시작 후
# 브라우저에서 LangGraph Studio 접속
# 실시간 그래프 실행 상황 모니터링
```

#### LangSmith 추적
- 모든 LLM 호출 추적 및 분석
- 토큰 사용량 및 비용 모니터링
- 프롬프트 최적화를 위한 입출력 분석

#### 로컬 디버깅
```bash
# 단위 테스트
python -m pytest tests/

# 통합 테스트
python -m pytest tests/integration_tests/

# 수동 테스트
python -c "
from src.review.graph import graph
result = graph.invoke({'mall_id': 'test', 'shop_id': 'test'})
print(result)
"
```

## 📊 성능 및 제한사항

### ⚡ 성능 특성
- **처리 시간**: 리뷰 100개 기준 약 30-60초
- **동시 사용자**: 10명 내외 권장 (API 비용 고려)
- **메모리 사용**: 평균 500MB, 최대 1GB

### ⚠️ 제한사항
1. **API 비용**: GPT 모델 사용으로 인한 토큰 비용 발생
2. **응답 지연**: LLM 호출로 인한 2-10초 지연
3. **한국어 특화**: 한국어 리뷰 분석에 최적화됨
4. **DB 의존성**: MySQL 연결 필수
5. **토큰 제한**: 매우 긴 리뷰는 자동 요약 후 처리

## 🛡️ 보안 고려사항

### 데이터 보호
- **환경변수**: 모든 민감 정보는 `.env` 파일로 관리
- **Git 보안**: `.env` 파일은 `.gitignore`로 제외
- **DB 접근**: 읽기 전용 계정 사용 권장

### API 보안
- **키 관리**: OpenAI API 키 안전한 보관
- **사용량 제한**: API 사용량 모니터링 및 제한
- **에러 처리**: 민감한 정보 노출 방지

## 🤝 기여 및 지원

### 개발 환경 설정
```bash
# 개발 의존성 설치
pip install -e ".[dev]"

# 코드 스타일 검사
ruff check src/
mypy src/

# 테스트 실행
pytest tests/
```

### 이슈 리포팅
- 버그 리포트: GitHub Issues 사용
- 기능 요청: 상세한 사용 사례와 함께 제출
- 보안 이슈: 비공개로 연락

## 📄 라이선스

이 프로젝트는 MIT 라이선스 하에 배포됩니다. 자세한 내용은 [LICENSE](LICENSE) 파일을 참조하세요.

## 🔗 관련 링크

- **[LangGraph 문서](https://langchain-ai.github.io/langgraph/)**
- **[LangGraph Studio](https://langchain-ai.github.io/langgraph/concepts/langgraph_studio/)**
- **[LangSmith](https://smith.langchain.com/)**
- **[Streamlit 문서](https://docs.streamlit.io/)**
- **[OpenAI API 문서](https://platform.openai.com/docs/)**
