from src.review.state.state import State


def rerank_node(state: State) -> dict:
    """[NODE] 최종 점수를 기준으로 리뷰 순위를 다시 정하고, 결과에 대한 신뢰도를 계산합니다."""
    print("\n--- 5. 리뷰 순위 재조정 및 신뢰도 계산 (rerank_auto) ---")
    reviews = state['aggregated_best_reviews']

    # 점수(rating)가 높은 순으로 정렬
    reranked_reviews = sorted(reviews, key=lambda r: r.get('rating', 0), reverse=True)
    print(f"-> 재조정된 순위: {[r['id'] for r in reranked_reviews]}")

    # 신뢰도 점수 시뮬레이션
    # 재시도 테스트를 위해 retry_count에 따라 다른 confidence 반환
    retry_count = state.get('re_rank_retry_count', 0)
    confidence = 1 if retry_count == 0 else 1  # 첫 시도는 실패, 두 번째는 성공하도록 설정

    print(f"-> 계산된 신뢰도: {confidence}")

    return {
        "aggregated_best_reviews": reranked_reviews,
        "confidence": confidence,
        "re_rank_retry_count": retry_count + 1  # 다음 재시도를 위해 카운트 증가
    }


__all__ = ["rerank_node"]
