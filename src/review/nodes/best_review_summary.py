from typing import List

from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field

from src.review.nodes.best_review_candidates import LLMName
from src.review.prompts import prompts
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
    parser = PydanticOutputParser(pydantic_object=ReviewSummaries)
    prompt_template = ChatPromptTemplate.from_messages([
        ("system", prompts['generate_summary'].system),
        ("user", prompts['generate_summary'].user),
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
