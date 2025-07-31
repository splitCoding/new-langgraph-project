import random
from typing import List

from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field

from src.review.nodes.best_review_candidates import LLMName
from src.review.state.state import State
from collections import defaultdict


class BestReview(BaseModel):
    id: int


class BestReviews(BaseModel):
    """선택된 최적 리뷰들의 ID 목록을 담는 데이터 구조"""
    best_reviews: List[BestReview] = Field(description="주어진 초점에 가장 부합하는 대표 리뷰들의 ID 목록")


def aggregate_best_node(state: State) -> dict:
    """[NODE] 여러 LLM이 선택한 리뷰들을 취합하고 중복을 제거합니다."""
    print("\n--- 3. 최적 리뷰 취합 (aggregate_best) ---")
    all_selected = state['selected_reviews']
    if not all_selected or len(all_selected) == 0:
        print("-> 후보로 선정된 리뷰가 없습니다.")
        return {"aggregated_best_reviews": []}

    review_count = state.get('best_review_count', 3)
    grouped = defaultdict(list)
    for review in all_selected:
        grouped[review['id']].append(review)

    candidates = []
    for id_, reviews in grouped.items():
        avg_rating = sum(r['score'] for r in reviews) / len(reviews)
        merged = reviews[0].copy()
        merged['score'] = avg_rating
        candidates.append(merged)

    # ID를 기준으로 중복 제거
    # unique_reviews = list({review['id']: review for review in all_selected}.values())
    print(f"-> 취합된 리뷰 (중복 제거 후): {[r['id'] for r in candidates]}")

    prompt = """
당신은 고객 리뷰 분석 전문가입니다. 고객들에게 가장 유용하고 대표적인 리뷰 후보들 중 최종 BEST 리뷰를 선택해야 합니다.
score는 0에서 100 사이의 정수로 리뷰의 유용성, 신뢰성, 정보량 등을 종합적으로 평가한 후보 평가 점수입니다.

응답은 반드시 다음 JSON 형식으로만 제공해주세요:
{{
  "best_reviews": [
    {{"id": 선택된리뷰ID1}},
    {{"id": 선택된리뷰ID2}}
  ]
}}

JSON 형식을 정확히 지켜서 응답해주세요.
            """
    parser = PydanticOutputParser(pydantic_object=BestReviews)
    prompt_template = ChatPromptTemplate.from_messages([
        ("system", prompt),
        ("user",
         "다음은 BEST 고객 리뷰 후보로 선택된 리뷰 목록입니다:\n\n{review_list}\n\n위 목록에서 최적의 리뷰 {review_count}개를 선택해 주세요.")
    ])
    model = ChatOpenAI(model=LLMName.GPT_4_1_MINI, temperature=0)
    chain = prompt_template | model | parser

    review_list_str = "\n".join([
        f"- ID: {r['id']}, 평점: {r['rating']}, 후보 평가 점수: {r['score']}, 내용: {r['text']}, 이미지 존재 여부 : {r['image_exist']}, 작성일 : {r['createdAt']}"
        for r in candidates
    ])

    try:
        response = chain.invoke({
            "review_list": review_list_str,
            "review_count": review_count,
        })
        best_reviews = response.best_reviews
        print(f"-> 선택된 BEST 리뷰 ID: {[c.id for c in best_reviews]}")

        all_selected_review_map = {r['id']: r for r in all_selected}
        final_selected_reviews = [all_selected_review_map[best_review.id] for best_review in best_reviews if
                                  best_review.id in all_selected_review_map]

        # fan-in을 위해 'selected_reviews' 키로 반환
        return {"aggregated_best_reviews": final_selected_reviews}
    except Exception as e:
        print(f"BEST 리뷰 선정 중 오류 발생: {e}")
        return {"aggregated_best_reviews": []}


def check_inventory_node(state: State) -> dict:
    """[NODE] 재고 보너스를 적용할지 결정하고, 적용 시 리뷰에 보너스 점수를 추가합니다."""
    print("\n--- 4a. 재고 확인 및 보너스 적용 (check_inventory) ---")
    apply_stock_bonus = state.get('apply_stock_bonus', False)

    if not apply_stock_bonus:
        print("-> 재고 보너스 적용 안 함.")
        return {}

    reviews = state['aggregated_best_reviews']
    for review in reviews:
        # 재고가 있는 상품의 리뷰에 보너스 점수를 부여하는 로직 시뮬레이션
        if random.choice([True, False]):
            review['rating'] += 1
            print(f"-> 리뷰 {review['id']}에 재고 보너스 적용! (새 점수: {review['rating']})")

    return {"aggregated_best_reviews": reviews}


__all__ = ["aggregate_best_node", "check_inventory_node"]
