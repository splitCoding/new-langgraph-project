from dataclasses import dataclass
from typing import TypedDict, Annotated


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

class SelectedCandidate(TypedDict):
    candidate: Candidate
    selected: bool  # 후보가 선택되었는지 여부

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


def _add_candidates(left: list[Candidate], right: list[Candidate]) -> list[Candidate]:
    """
    State의 selected_reviews 필드를 업데이트하는 리듀서 함수.
    두 개의 리뷰 리스트(기존 리스트, 새 리스트)를 하나로 병합합니다.
    """
    if not isinstance(left, list) or not isinstance(right, list):
        # 초기 상태 또는 빈 상태를 처리하기 위한 방어 코드
        return (left or []) + (right or [])
    return left + right


class State(TypedDict):
    mall_id: str
    shop_id: str
    reviews: list[Review]
    candidates: Annotated[list[Candidate], _add_candidates]
    best_reviews: list[BestReview]
    generated_infos: list[GeneratedReviewInfo]
    validated_infos: list[GeneratedReviewInfoValidation]
    filtered_reviews: list[Review]
    criteria_by_type: list[CriteriaByReviewType]
    selected_candidates: list[SelectedCandidate]
