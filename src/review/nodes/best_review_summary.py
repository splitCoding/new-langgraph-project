from typing import List

from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field

from src.review.nodes.best_review_candidates import LLMName
from src.review.state.state import State


class ReviewSummary(BaseModel):
    id: str = Field(description="리뷰의 고유 ID")
    title: str = Field(description="리뷰의 핵심 내용을 한 줄로 요약한 제목")
    summary: str = Field(description="리뷰의 주요 내용을 1개의 문장으로 요약한 내용")


class ReviewSummaries(BaseModel):
    """리뷰 요약 결과를 담는 데이터 구조"""
    summaries: List[ReviewSummary] = Field(description="각 리뷰에 대한 제목과 요약 목록")


def generate_summary_node(state: State) -> dict:
    """[NODE] 최상위 리뷰들을 바탕으로 요약문을 생성합니다."""
    print("\n--- 6. 요약문 생성 (generate_summary) ---")
    best_reviews = state['aggregated_best_reviews']
    retry_count = state.get('result_generate_retry_count', 0)

    if retry_count >= 2:
        print("-> 이전에 생성된 요약문 사용")
        return {
            "results": state['results'],
        }

    if not best_reviews or len(best_reviews) == 0:
        print("-> 요약할 리뷰가 없습니다.")
        return {
            "results": [],
            "result_generate_retry_count": retry_count + 1
        }

    # LLM을 사용하여 리뷰 요약 생성
    prompt = """
당신은 고객 리뷰 요약 전문가입니다. 주어진 리뷰들을 분석하여 각각에 대해 제목과 요약을 생성해야 합니다.

응답은 반드시 다음 JSON 형식으로만 제공해주세요:
{{
  "summaries": [
    {{
      "id": "리뷰1의 ID",
      "title": "리뷰1의 핵심 내용을 한 줄로 요약한 제목",
      "summary": "title 을 뒷밤침하는 간단한 부연 설명이나 요약"
    }},
    {{
      "id": "리뷰2의 ID",
      "title": "리뷰2의 핵심 내용을 한 줄로 요약한 제목", 
      "summary": "title 을 뒷밤침하는 간단한 부연 설명이나 요약"
    }}
  ]
}}

요약할 때는 다음 사항을 고려해주세요:
- 고객이 가장 중요하게 언급한 부분을 우선적으로 포함
- 긍정적 의견 위주로 반영
- 구체적인 사용 경험이나 특징을 포함
- 요약의 결과가 다른 구매자들에게 정보를 전달하는 느낌의 친숙한 내용으로 작성

반드시 유효한 JSON 형식으로만 응답해주세요.

ex. {{
        "summaries": [
        {{
            "id": "12345",
            "title": "모두가 써봤으면 싶어 리뷰 남겨요",
            "summary": "좁쌀과 요철에 효과적이고 피부 장벽이 튼튼해지는게 느껴져요"
        }},
        {{
            "id": "67890",
            "title": "발랐을 때 윤기가 달라요",
            "summary": "남편도 자꾸 제꺼 발라요. 향도 좋고 무겁지 않아서 좋아요"
        }}
    }}
"""

    parser = PydanticOutputParser(pydantic_object=ReviewSummaries)
    prompt_template = ChatPromptTemplate.from_messages([
        ("system", prompt),
        ("user", "다음 리뷰들을 각각 분석하여 JSON 형식으로 제목과 요약을 생성해주세요:\n\n{review_list}")
    ])

    model = ChatOpenAI(model=LLMName.GPT_4_1_MINI, temperature=0.3)
    chain = prompt_template | model | parser

    # 리뷰 목록을 문자열로 변환
    review_list_str = "\n".join([
        f"리뷰\n ID: {review['id']}\n- 평점: {review['rating']}/5\n- 내용: {review['text']}\n- 작성일: {review.get('createdAt', 'N/A')}\n"
        for i, review in enumerate(best_reviews)
    ])

    try:
        response = chain.invoke({
            "review_list": review_list_str
        })

        # Pydantic 모델에서 딕셔너리로 변환
        results = [
            {
                "id": summary.id,
                "title": summary.title,
                "summary": summary.summary
            }
            for summary in response.summaries
        ]

        print(f"-> 생성된 요약 개수: {len(results)}")
        for i, result in enumerate(results):
            print(f"   리뷰 {i + 1} 제목: {result['title']}")

        return {
            "results": results,
            "result_generate_retry_count": retry_count + 1
        }

    except Exception as e:
        print(f"요약 생성 중 오류 발생: {e}")
        return {
            "results": [],
            "result_generate_retry_count": retry_count + 1
        }


def generate_image_node(state: State) -> dict:
    """[NODE] 리뷰 텍스트나 요약문을 기반으로 이미지를 생성하는 것을 시뮬레이션합니다."""
    # print("\n--- 7. 리뷰 기반 이미지 생성 (generate_image_from_review) ---")
    # summary = state['results']
    # print(f"-> 요약문 기반 이미지 생성 시도: \"{summary[:30]}...\"")
    # time.sleep(2)  # 이미지 생성 시간 시뮬레이션
    # image_url = f"https://image.dummy.com/{hash(summary)}.jpg"
    # print(f"-> 생성된 이미지 URL: {image_url}")
    return {"image_url": ""}


__all__ = ["generate_summary_node", "generate_image_node"]
