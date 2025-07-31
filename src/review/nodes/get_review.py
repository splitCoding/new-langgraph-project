from src.review.state.state import State
from src.review.review_db import review_db


def fetch_reviews_node(state: State) -> dict:
    print("\n--- 1. 리뷰 수집 (fetch_reviews) ---")
    params = get_required_params(state)
    mallId = params['mallId']
    shopId = params['shopId']
    search_review_max_count = params['search_review_max_count']
    if (not mallId or not shopId):
        print("-> mallId 또는 shopId가 제공되지 않았습니다. 리뷰를 가져올 수 없습니다.")
        return {
            "reviews": [],
        }

    reviews = review_db.get_reviews_by_shop(mallId, shopId, 5, search_review_max_count)
    print(f"-> {len(reviews)}개의 리뷰를 성공적으로 가져왔습니다.")
    return {
        "reviews": reviews,
    }


def get_required_params(state: State) -> dict:
    return {
        "mallId": state.get('mallId', None),
        "shopId": state.get('shopId', None),
        "search_review_max_count": state.get('search_review_max_count', 100)
    }


__all__ = ["fetch_reviews_node"]
