"""Title and Summary Generator State Definitions."""

from typing import TypedDict, List, Dict, Any

class SelectedReview(TypedDict):
    """선택된 리뷰 데이터 모델."""
    id: int
    text: str
    rating: int
    created_at: str
    image_exists: bool

class GeneratedTitle(TypedDict):
    """생성된 제목 데이터 모델."""
    review_id: int
    title: str

class GeneratedSummary(TypedDict):
    """생성된 요약 데이터 모델."""
    review_id: int
    summary: str

class ValidatedTitle(TypedDict):
    """검증된 제목 데이터 모델."""
    review_id: int
    title: str
    is_valid: bool
    validation_message: str

class ValidatedSummary(TypedDict):
    """검증된 요약 데이터 모델."""
    review_id: int
    summary: str
    is_valid: bool
    validation_message: str

class State(TypedDict):
    """제목/요약 생성기 상태."""
    # 입력
    selected_reviews: List[SelectedReview]  # 제목 생성이 필요한 선택된 리뷰들
    summary_required_reviews: List[SelectedReview]  # 요약도 필요한 리뷰들
    title_style: str  # 제목 스타일 (예: "간결한", "창의적인", "전문적인")
    summary_style: str  # 요약 스타일 (예: "상세한", "간단한", "감정 중심")
    title_custom_requirements: str  # 제목 생성 시 사용자 정의 요구사항
    regenerate_requirements: str  # 재생성 시 추가 요구사항
    
    # 중간 결과
    validated: bool  # 입력 검증 완료 여부
    review_count: int  # 처리할 리뷰 수
    generated_titles: List[GeneratedTitle]  # 생성된 제목들
    generated_summaries: List[GeneratedSummary]  # 생성된 요약들
    
    # 최종 결과
    validated_titles: List[ValidatedTitle]  # 검증된 제목들
    validated_summaries: List[ValidatedSummary]  # 검증된 요약들
    final_results: Dict[str, Any]  # 최종 결과
    status: str  # 처리 상태
    error: str  # 에러 메시지 (있는 경우)
