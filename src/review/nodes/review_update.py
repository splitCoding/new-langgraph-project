from src.review.state.state import State


def update_db_node(state: State) -> dict:
    """[NODE] 최종 결과를 DB에 업데이트하는 것을 시뮬레이션합니다."""
    print("\n--- 8. 데이터베이스 업데이트 (update_db) ---")
    if len(state['reviews']) == 0:
        print("-> 리뷰가 없습니다. 데이터베이스 업데이트를 건너뜁니다.")
        return {}
    final_data = {
        "mallId": state['mallId'],
        "shopId": state['shopId'],
        "title": "고객 리뷰 기반 자동 생성 콘텐츠",  # 제목은 간단히 고정값으로 설정
        "results": state['results'],
        "image_url": state.get('image_url'),
        "best_review_ids": [r['id'] for r in state['aggregated_best_reviews']],
    }
    print("-> DB에 저장될 최종 데이터:")
    print(final_data)
    return {}


__all__ = ["update_db_node"]
