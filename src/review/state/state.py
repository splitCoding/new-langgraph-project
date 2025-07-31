from dataclasses import dataclass
from typing import TypedDict, Annotated


def _add_selected_reviews(left: list[dict], right: list[dict]) -> list[dict]:
    """
    State의 selected_reviews 필드를 업데이트하는 리듀서 함수.
    두 개의 리뷰 리스트(기존 리스트, 새 리스트)를 하나로 병합합니다.
    """
    if not isinstance(left, list) or not isinstance(right, list):
        # 초기 상태 또는 빈 상태를 처리하기 위한 방어 코드
        return (left or []) + (right or [])
    return left + right


@dataclass
class State(TypedDict):
    mallId: str
    shopId: str
    search_review_max_count: int
    candidate_count: int
    best_review_count: int
    apply_stock_bonus: bool
    re_rank_retry_count: int
    result_generate_retry_count: int
    generate_image: bool
    # 상태 저장 필드
    reviews: list[dict]
    selected_reviews: Annotated[list[dict], _add_selected_reviews]
    aggregated_best_reviews: list[dict]
    confidence: float
    image_url: str | None  # 이미지 URL을 저장할 필드 추가
    results: list[dict]
