from src.review.state.state import State
from src.review.review_db import review_db


def update_db_node(state: State) -> dict:
    """[NODE] 최종 결과를 DB에 업데이트합니다."""
    print("\n--- 8. 데이터베이스 업데이트 (update_db) ---")

    # 입력 데이터 검증
    recommend_reviews = state.get('aggregated_best_reviews', [])
    results = state.get('results', [])

    if len(recommend_reviews) == 0:
        print("-> BEST 리뷰가 없습니다. 데이터베이스 업데이트를 건너뜁니다.")
        return {}

    if len(results) == 0:
        print("-> 요약 결과가 없습니다. 데이터베이스 업데이트를 건너뜁니다.")
        return {}

    try:
        print("-> 데이터베이스 업데이트 시작")

        # BEST 리뷰 ID 추출
        print(f"-> BEST 리뷰 ID들: {[review['id'] for review in recommend_reviews]}")

        # BEST 리뷰들을 추천 리뷰 테이블에 저장
        recommend_data = []
        for i, review in enumerate(recommend_reviews):
            review_id = review['id']  # 기본 타입 그대로 사용
            print(f"-> [{i + 1}] BEST 리뷰 처리 중: ID={review_id}")
            print(review)
            print(results)

            # results에서 해당 리뷰의 요약 정보 찾기
            review_results = next((r for r in results if r.get('id') == review_id), None)

            if review_results:
                print(f"   - 해당 리뷰의 요약 결과 찾음: {len(review_results.get('results', []))}개")

                if review_results.get('results'):
                    for j, result in enumerate(review_results['results']):
                        recommend_item = {
                            'id': review_id,
                            'title': result.get('title', ''),
                            'summary': result.get('summary', ''),
                        }
                        recommend_data.append(recommend_item)
                        print(
                            f"   - [{j + 1}] 추천 데이터 추가: 제목='{recommend_item['title']}', 요약='{recommend_item['summary']}'")
                else:
                    print(f"   - ⚠️  요약 결과가 비어있음")
            else:
                print(f"   - ❌ 해당 리뷰 ID({review_id})에 대한 요약 결과를 찾을 수 없음")
                print(f"   - 사용 가능한 results ID들: {[r.get('id') for r in results]}")

        print(f"-> 최종 추천 리뷰 데이터 개수: {len(recommend_data)}")

        # 생성된 데이터 상세 출력
        if recommend_data:
            print("-> 생성된 추천 데이터 상세:")
            for i, data in enumerate(recommend_data):
                print(f"   [{i + 1}] ID: {data['id']}, 제목: '{data['title']}', 요약: '{data['summary']}'")
        else:
            print("-> ❌ 추천 데이터가 하나도 생성되지 않았습니다!")

        # 추천 리뷰 테이블에 BEST 리뷰들 저장
        if recommend_data:
            try:
                insert_count = review_db.insert_recommend_review(recommend_data)
                print(f"-> 추천 리뷰 저장 완료: {insert_count}개 행 삽입")

                # 저장된 데이터 확인 출력
                for i, data in enumerate(recommend_data):
                    print(f"   [{i + 1}] 리뷰ID: {data['id']}, 제목: '{data['title']}', 요약: '{data['summary']}'")

                # 최종 요약 정보
                final_summary = {
                    "mallId": state['mallId'],
                    "shopId": state['shopId'],
                    "recommend_review_count": len(recommend_data),
                }

                print("-> 데이터베이스 업데이트 완료:")
                print(final_summary)

                return {"db_update_success": True, "summary": final_summary}

            except Exception as db_error:
                print(f"-> 추천 리뷰 저장 중 오류: {db_error}")
                return {"db_update_success": False, "error": str(db_error)}
        else:
            print("-> 저장할 추천 리뷰 데이터가 없습니다.")
            return {"db_update_success": False, "error": "저장할 추천 리뷰 데이터가 없습니다."}

    except Exception as e:
        print(f"-> 예상치 못한 오류: {e}")
        return {"db_update_success": False, "error": str(e)}


__all__ = ["update_db_node"]
