"""UI에서 사용하는 데이터 타입 정의."""

from typing import TypedDict, List
from enum import Enum


class Review(TypedDict):
    """리뷰 데이터 모델."""
    id: int  # 리뷰 고유 ID
    text: str  # 리뷰 내용
    rating: int  # 평점 (1~5)
    created_at: str  # 작성일
    image_exists: bool  # 이미지 존재 여부


class CandidateScore(TypedDict):
    """후보 평점 데이터 모델."""
    score: int  # 점수 (0~100)
    perspective: str  # 관점 (예: "품질", "가격", "서비스")


class Candidate(TypedDict):
    """후보 리뷰 데이터 모델."""
    review_id: int  # 리뷰 ID
    score: list[CandidateScore]  # 후보 평점 목록


class ReviewTitleAndSummary(TypedDict):
    id: int
    title: str
    summary: str


class GeneratedReviewInfo(TypedDict):
    review_id: int
    infos: list[ReviewTitleAndSummary]


class InfoValidation(TypedDict):
    is_valid: bool
    validated_result: str
    suggestion: str | None


class GeneratedReviewInfoValidation(TypedDict):
    info_id: int
    title: InfoValidation
    summary: InfoValidation


class BestReview(Candidate):
    """BEST 리뷰 데이터 모델."""
    generated_infos: list[ReviewTitleAndSummary]
    validated_infos: list[GeneratedReviewInfoValidation]


class CriteriaByReviewType(TypedDict):
    """리뷰 타입별 고려 항목 데이터 모델."""
    type: str  # 리뷰 타입 (예: "품질", "가격")
    criteria: list[str]  # 고려 항목 목록


class ChatState(Enum):
    """채팅 상태 관리."""
    GREETING = "greeting"
    SELECT_REVIEW_TYPE = "select_review_type"
    CUSTOM_INPUT = "custom_input"
    CONFIRM_SELECTION = "confirm_selection"
    SHOW_CRITERIA = "show_criteria"
    ASK_ADDITIONAL = "ask_additional"
    ADDITIONAL_INPUT = "additional_input"
    FINAL_CRITERIA = "final_criteria"
    SELECTING_REVIEWS = "selecting_reviews"
    SHOW_CANDIDATE_REVIEWS = "show_candidate_reviews"
    USER_SELECT_REVIEWS = "user_select_reviews"
    NO_SELECTION_RETRY = "no_selection_retry"
    SHOW_SELECTED_REVIEWS = "show_selected_reviews"
    SELECT_TITLE_STYLE = "select_title_style"
    CONFIRM_TITLE_STYLE = "confirm_title_style"
    GENERATING_TITLES = "generating_titles"
    SHOW_GENERATED_TITLES = "show_generated_titles"
    REGENERATING_TITLES = "regenerating_titles"
    ASK_SUMMARY = "ask_summary"
    SELECT_SUMMARY_REVIEWS = "select_summary_reviews"
    SELECT_SUMMARY_STYLE = "select_summary_style"
    GENERATING_SUMMARIES = "generating_summaries"
    SHOW_FINAL_RESULTS = "show_final_results"
    SAVE_TO_DB = "save_to_db"


# 세션 상태 기본값 설정
SESSION_STATE_DEFAULTS = {
    "chat_state": {"name": "chat_state", "default_value": ChatState.GREETING},
    "messages": {"name": "messages", "default_value": []},
    "selected_types": {"name": "selected_types", "default_value": []},
    "custom_type": {"name": "custom_type", "default_value": ""},
    "additional_criteria": {"name": "additional_criteria", "default_value": []},
    "candidate_reviews": {"name": "candidate_reviews", "default_value": []},
    "selected_reviews": {"name": "selected_reviews", "default_value": []},
    "title_style": {"name": "title_style", "default_value": ""},
    "summary_style": {"name": "summary_style", "default_value": ""},
    "summary_required_reviews": {"name": "summary_required_reviews", "default_value": []},
    "final_titles": {"name": "final_titles", "default_value": []},
    "final_summaries": {"name": "final_summaries", "default_value": []},
    "criteria_by_type": {"name": "criteria_by_type", "default_value": []},
    "available_assistants": {"name": "available_assistants", "default_value": {}},
    "mall_id": {"name": "mall_id", "default_value": "test_mall"},
    "shop_id": {"name": "shop_id", "default_value": "test_shop"},
    "selected_store_name": {"name": "selected_store_name", "default_value": ""},
}


def _add_candidates(left: list[Candidate], right: list[Candidate]) -> list[Candidate]:
    """
    State의 selected_reviews 필드를 업데이트하는 리듀서 함수.
    두 개의 리뷰 리스트(기존 리스트, 새 리스트)를 하나로 병합합니다.
    """
    if not isinstance(left, list) or not isinstance(right, list):
        # 초기 상태 또는 빈 상태를 처리하기 위한 방어 코드
        return (left or []) + (right or [])
    return left + right
