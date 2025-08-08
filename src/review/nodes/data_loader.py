"""Data loading nodes for review processing."""

import logging
from typing import Any, Dict
from ..states import State, Review
from ..tools.database import query_reviews_by_rating, query_reviews_with_images

logger = logging.getLogger(__name__)


def load_reviews_from_db(state: State) -> Dict[str, Any]:
    """Load reviews from database based on state criteria."""
    mall_id = state.get("mall_id", "")
    shop_id = state.get("shop_id", "")
    
    if not mall_id or not shop_id:
        logger.warning("Missing mall_id or shop_id for loading reviews")
        return {"reviews": []}
    
    try:
        # Try to load high-rated reviews with images first
        # .invoke() 메서드로 도구 호출 (키워드 인자 사용 가능)
        reviews = query_reviews_with_images.invoke({
            "mall_id": mall_id,
            "shop_id": shop_id,
            "limit": 1
        })

        # If not enough reviews, load high-rated reviews
        # if len(reviews) < 10:
        #     # .invoke() 메서드로 도구 호출 (키워드 인자 사용 가능)
        #     additional_reviews = query_reviews_by_rating.invoke({
        #         "mall_id": mall_id,
        #         "shop_id": shop_id,
        #         "min_rating": 4,
        #         "limit": 10
        #     })
            
        #     # Merge reviews avoiding duplicates
        #     existing_ids = {review["id"] for review in reviews}
        #     for review in additional_reviews:
        #         if review["id"] not in existing_ids:
        #             reviews.append(review)
        
        logger.info(f"Loaded {len(reviews)} reviews from database")
        logger.info(f"Loaded {reviews} reviews from database")
        return {"reviews": reviews}
        
    except Exception as e:
        logger.error(f"Failed to load reviews from database: {e}")
        # Fallback to sample data
        return load_sample_reviews(state)


def load_sample_reviews(_state: State) -> Dict[str, Any]:
    """Load sample reviews for testing purposes."""
    logger.info("Loading sample reviews")
    
    sample_reviews = [
        Review(
            id=1,
            text="이 제품 정말 좋아요! 사용하기 편하고 성능도 뛰어나요. 강력 추천합니다!",
            rating=5,
            created_at="2023-10-01",
            image_exists=True
        ),
        Review(
            id=2,
            text="가격 대비 만족스러운 제품입니다. 디자인도 예쁘고 기능도 충분해요.",
            rating=4,
            created_at="2023-10-02",
            image_exists=True
        ),
        Review(
            id=3,
            text="배송도 빠르고 제품 질도 좋네요. 다음에도 구매할 의향 있습니다.",
            rating=4,
            created_at="2023-10-03",
            image_exists=False
        ),
        Review(
            id=4,
            text="생각보다 훨씬 좋은 제품이에요. 내구성도 뛰어나고 사용감이 최고입니다!",
            rating=5,
            created_at="2023-10-04",
            image_exists=True
        ),
        Review(
            id=5,
            text="친구 추천으로 구매했는데 정말 만족해요. 성능이 기대 이상입니다.",
            rating=5,
            created_at="2023-10-05",
            image_exists=False
        )
    ]
    
    return {"reviews": sample_reviews}