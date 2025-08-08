# UI Package

BEST 리뷰 분석 시스템의 Streamlit 기반 웹 인터페이스 패키지입니다.

## 📁 구조

```
ui/
├── __init__.py
├── apps/
│   └── review_agent_chat.py    # 메인 Streamlit 앱
├── components/
│   └── chat_components.py      # UI 컴포넌트들
├── models/
│   ├── __init__.py
│   ├── data.py                 # 데이터 모델
│   └── types.py                # 타입 정의
└── services/
    ├── __init__.py
    ├── api_client.py           # LangGraph API 클라이언트
    ├── database.py             # 데이터베이스 연결
    ├── review_service.py       # 리뷰 서비스
    └── store_service.py        # 매장 관리 서비스
```

## 🎯 주요 기능

### 🏪 매장 관리
- **매장 선택**: 드롭다운으로 쉬운 매장 전환
- **동적 로딩**: DB에서 실시간 매장 목록 조회
- **세션 유지**: 선택된 매장 정보 세션 전반 유지

### 🎨 대화형 인터페이스
- **단계별 가이드**: 직관적인 리뷰 분석 프로세스
- **실시간 피드백**: 각 단계별 즉시 결과 확인
- **상태 관리**: ChatState 기반 안정적인 UI 상태 관리

### 📝 리뷰 분석 워크플로우
1. **리뷰 타입 선택**: 포토, 솔직한, 긍정적인, 경험 기반 리뷰
2. **기준 생성**: AI 기반 맞춤형 평가 기준 자동 생성
3. **후보 선정**: 설정된 기준으로 BEST 리뷰 후보 추천
4. **최종 선택**: 사용자가 직접 최종 BEST 리뷰 선택
5. **제목 생성**: 다양한 스타일의 제목 자동 생성
6. **요약 생성**: 선택적 요약 생성 (선택사항)
7. **DB 저장**: 최종 결과를 데이터베이스에 저장

### 🔄 고급 제목 관리
- **사용자 정의 요구사항**: 제목 생성 시 특별 요청 입력
- **선택적 재생성**: 마음에 들지 않는 제목만 다시 생성
- **재생성 요구사항**: 추가 수정 사항을 반영한 재생성

## 🚀 실행 방법

### 1. 환경 설정
```bash
# 가상 환경 활성화
source .venv/bin/activate

# 환경 변수 설정
cp .env.example .env
# .env 파일에 실제 값 입력
```

### 2. LangGraph 서버 시작
```bash
langgraph dev
```

### 3. Streamlit 앱 실행
```bash
streamlit run src/ui/apps/review_agent_chat.py --server.port 8501
```

### 4. 브라우저 접속
- Local: http://localhost:8501
- Network: http://[IP]:8501

## 🎨 UI 컴포넌트

### ChatState 기반 상태 관리
```python
class ChatState(Enum):
    GREETING = "greeting"                    # 시작 화면
    SELECT_REVIEW_TYPE = "select_review_type"  # 리뷰 타입 선택
    GENERATING_TITLES = "generating_titles"    # 제목 생성 중
    REGENERATING_TITLES = "regenerating_titles" # 제목 재생성 중
    SHOW_FINAL_RESULTS = "show_final_results"  # 최종 결과 표시
    # ... 기타 상태들
```

### 주요 UI 컴포넌트
- `render_review_type_selection()`: 리뷰 타입 선택 UI
- `render_title_style_selection()`: 제목 스타일 및 요구사항 입력
- `render_generated_titles()`: 생성된 제목 표시 및 재생성 UI
- `render_title_regeneration()`: 제목 재생성 처리
- `render_final_results()`: 최종 결과 표시

### 데이터 표시 최적화
- **HTML 클리닝**: BeautifulSoup으로 안전한 텍스트 표시
- **길이 제한**: 긴 리뷰 텍스트 자동 요약
- **반응형 레이아웃**: 다양한 화면 크기 지원

## 🔧 설정

### 환경변수
```bash
# 데이터베이스 연결
DB_HOST=your_db_host
DB_PORT=3306
DB_USER=your_username
DB_PASSWORD=your_password
DB_NAME=your_database
DB_CHARSET=utf8mb4

# API 키
OPENAI_API_KEY=your_openai_api_key
LANGSMITH_API_KEY=your_langsmith_api_key

# LangGraph 서버
LANGGRAPH_API_BASE=http://localhost:2024
```

### Streamlit 설정
```python
st.set_page_config(
    page_title="BEST 리뷰 분석 시스템",
    page_icon="🏆",
    layout="wide",
    initial_sidebar_state="expanded"
)
```

## 📊 API 통신

### LangGraph API 클라이언트
```python
# 리뷰 선호도 분석
result = invoke_review_preference_api(
    selected_types=["포토 리뷰", "긍정적인 리뷰"],
    additional_criteria=["배송 속도"]
)

# 제목/요약 생성
result = invoke_title_summary_api(
    selected_reviews=reviews,
    title_style="창의적인",
    title_custom_requirements="제품명 포함",
    regenerate_requirements="더 짧게"
)
```

### 에러 처리
- **연결 실패**: LangGraph 서버 미실행 시 친화적 에러 메시지
- **타임아웃**: 장시간 응답 없을 시 자동 재시도
- **데이터 오류**: 잘못된 응답 형식 시 안전한 폴백

## 🗄️ 데이터베이스 연동

### 매장 관리
```python
# 매장 목록 조회
stores = get_store_list()

# 특정 매장 정보
store = get_store_by_name("매장명")
```

### BEST 리뷰 저장
```python
# 최종 결과 DB 저장
success = save_best_reviews_to_db(
    mall_id="test_mall",
    shop_id="test_shop", 
    selected_reviews=reviews,
    final_titles=titles,
    final_summaries=summaries
)
```

## 🎨 사용자 경험 (UX)

### 직관적인 인터페이스
- **진행 단계 표시**: 현재 위치를 명확히 안내
- **즉시 피드백**: 모든 액션에 대한 즉각적인 반응
- **에러 가이드**: 문제 발생 시 해결 방법 제시

### 접근성 (Accessibility)
- **레이블 가시성**: 모든 입력 필드에 명확한 레이블
- **키보드 내비게이션**: 마우스 없이도 전체 기능 이용 가능
- **색상 대비**: 가독성을 위한 적절한 색상 조합

### 반응형 디자인
- **모바일 대응**: 작은 화면에서도 편리한 사용
- **컬럼 레이아웃**: 화면 크기에 따른 동적 레이아웃
- **스크롤 최적화**: 긴 콘텐츠의 효율적인 표시

## 🔍 디버깅

### 세션 상태 확인
```python
# 개발 모드에서 세션 상태 표시
if st.checkbox("Debug 모드"):
    st.write("Session State:", dict(st.session_state))
```

### 로그 모니터링
```python
import logging
logging.basicConfig(level=logging.INFO)

# 주요 액션 로깅
logger.info(f"User selected review types: {selected_types}")
logger.info(f"Generated titles count: {len(titles)}")
```

### API 응답 확인
```python
# API 응답 디버깅
if "debug" in st.query_params:
    st.json(api_response)
```

## 📋 Dependencies

```python
# UI 프레임워크
"streamlit>=1.48.0",           # 웹 UI 프레임워크
"beautifulsoup4>=4.13.4",      # HTML 처리

# API 통신
"requests>=2.32.4",            # HTTP 클라이언트
"python-dotenv>=1.1.1",        # 환경변수 관리

# 데이터베이스
"mysql-connector-python>=9.4.0",  # MySQL 연결

# 데이터 처리
"pandas>=2.3.1",               # 데이터 분석 (선택적)
"tiktoken>=0.10.0",            # 토큰 계산
```

## 🚀 배포 및 운영

### 로컬 개발
```bash
# 개발 서버 시작 (핫 리로드)
streamlit run src/ui/apps/review_agent_chat.py --server.port 8501 --server.runOnSave true
```

### 프로덕션 배포
```bash
# 프로덕션 모드
streamlit run src/ui/apps/review_agent_chat.py --server.port 80 --server.address 0.0.0.0
```

### 도커 컨테이너
```dockerfile
FROM python:3.11-slim
COPY . /app
WORKDIR /app
RUN pip install -r requirements.txt
EXPOSE 8501
CMD ["streamlit", "run", "src/ui/apps/review_agent_chat.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

## ⚠️ 주의사항

1. **세션 관리**: 브라우저 새로고침 시 모든 상태 초기화
2. **메모리 사용**: 대량 리뷰 처리 시 메모리 사용량 증가
3. **API 의존성**: LangGraph 서버가 실행 중이어야 정상 동작
4. **데이터베이스 연결**: DB 연결 실패 시 일부 기능 제한
5. **브라우저 호환성**: 최신 브라우저 사용 권장

## 🎯 향후 개선 사항

- [ ] **실시간 알림**: WebSocket 기반 실시간 진행 상황 알림
- [ ] **배치 처리**: 대량 리뷰 비동기 처리
- [ ] **결과 내보내기**: Excel, PDF 등 다양한 형식 지원
- [ ] **사용자 설정**: 개인별 기본 설정 저장
- [ ] **다국어 지원**: 영어, 일본어 등 다국어 인터페이스
