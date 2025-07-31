from src.review.data_source import fetch_review
from src.review.state.state import State


def fetch_reviews_node(state: State) -> dict:
    """[NODE] MySQL DB에서 리뷰를 직접 조회하여 가져옵니다."""
    print("\n--- 1. 리뷰 수집 (fetch_reviews) ---")
    print("MySQL 데이터베이스에 연결하여 리뷰를 가져옵니다...")
    mallId = state.get('mallId', None)
    shopId = state.get('shopId', None)
    if (not mallId or not shopId):
        print("-> mallId 또는 shopId가 제공되지 않았습니다. 리뷰를 가져올 수 없습니다.")
        return {
            "reviews": [],
        }
    search_review_max_count = state.get('search_review_max_count', 100)

    query = """
            SELECT review.id,
                   review.text,
                   review.rating,
                   review.createdAt,
                   IF(review_content.id is null, FALSE, TRUE) as 'image_exist'
            FROM select_shop_custom_review review
                     JOIN select_shop_custom_review_product review_product
                          ON review.selectShopCustomReviewProductId = review_product.id
                     LEFT JOIN select_shop_custom_review_content review_content
                               ON review.id = review_content.selectShopCustomReviewId
            WHERE review.mallId = %s
              AND review.shopId = %s
              AND rating = 5
              AND display = TRUE
              AND isDeleted = FALSE
            ORDER BY review.createdAt DESC
            LIMIT %s
            """

    reviews = fetch_review(query, (mallId, shopId, search_review_max_count))
    print(f"-> {len(reviews['data'])}개의 리뷰를 성공적으로 가져왔습니다.")
    return {
        "reviews": reviews['data'],
    }


__all__ = ["fetch_reviews_node"]
