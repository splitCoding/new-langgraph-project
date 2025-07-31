from enum import Enum
from typing import List

from pydantic import BaseModel, Field

from src.review.cache import get_cache
from src.review.state.state import State

from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI


class BestReviewCandidate(BaseModel):
    id: int
    score: int


class BestReviews(BaseModel):
    """선택된 최적 리뷰들의 ID 목록을 담는 데이터 구조"""
    candidates: List[BestReviewCandidate] = Field(description="주어진 초점에 가장 부합하는 대표 리뷰 3개의 ID, SCORE 목록")


class LLMName(str, Enum):
    GPT_3_5_TURBO = "gpt-3.5-turbo"
    GPT_4_1_NANO = "gpt-4.1-nano"
    GPT_4_1_MINI = "gpt-4.1-mini"
    GPT_o_4_MINI = "o4-mini"


class LLMConfig:
    def __init__(self, model: str, temperature: float | None = 0):
        self.model = model
        self.temperature = temperature


# LLM 설정들
LLM_CONFIGS = {
    LLMName.GPT_3_5_TURBO: LLMConfig("gpt-3.5-turbo", 0),
    LLMName.GPT_4_1_NANO: LLMConfig("gpt-4.1-nano", 0),
    LLMName.GPT_4_1_MINI: LLMConfig("gpt-4.1-mini", 0),
    LLMName.GPT_o_4_MINI: LLMConfig("o4-mini", None),  # temperature 없음
}


# 2. 조회된 리뷰가 존재하는지 확인하는 노드
def check_review_exist(state: State) -> bool:
    """[NODE] 리뷰가 존재하는지 확인하는 노드 (예시)"""
    print("\n--- 리뷰 존재 여부 확인 (check_review_exist) ---")
    if not state['reviews'] or len(state['reviews']) == 0:
        print("-> 리뷰가 없습니다. 프로세스를 중단합니다.")
        return False  # 빈 리뷰 리스트 반환
    print("-> 리뷰가 존재합니다.")
    return True


# 3. 여러개의 LLM으로 FAN-OUT 하는 노드
def use_llm_node(state: State) -> dict:
    print(f"\n--- BEST 리뷰 생성 시작 ---")
    return {}


# 4. LLM BEST 리뷰 후보 선정 노드 생성 함수
def create_llm_selector_node(llm_name: LLMName, focus_instruction: str):
    """[NODE] LLM이 최적 리뷰를 선택하는 과정을 시뮬레이션하는 노드 생성 함수."""

    def llm_selector_node(state: State) -> dict:
        llm_config = LLM_CONFIGS[llm_name]
        print(f"\n--- 2. {llm_name}으로 리뷰 선택 (초점: {focus_instruction[:50]}...) ---")
        reviews = state.get("reviews", [])
        if not reviews:
            return {"selected_reviews": []}

        # 🎯 캐시 확인
        candidate_count = state.get('candidate_count', 3)
        cache = get_cache()
        cached_result = cache.get_cached_result(
            llm_name=llm_config.model,
            reviews=reviews,
            focus_instruction=focus_instruction,
            candidate_count=candidate_count
        )

        if cached_result is not None:
            print(f"✅ 캐시 HIT - 결과 반환 (LLM 호출 생략)")
            return {"selected_reviews": cached_result}

        print(f"🔄 캐시 미스 - LLM 호출 진행")

        prompt = """
            당신은 고객 리뷰 분석 전문가입니다. 주어진 리뷰 목록에서 특정 초점에 맞춰 고객들에게 가장 유용하고 대표적인 리뷰들을 선택해야 합니다.
            선택된 리뷰의 ID, 리뷰의 평가 score 를 JSON 형식으로 반환해 주세요.
            평가 score 는 0에서 100 사이의 정수로, 리뷰의 유용성, 신뢰성, 정보량 등을 종합적으로 평가한 점수입니다.
            당신의 분석 초점은 다음과 같습니다: {focus}

            {format_instructions}
        """
        parser = PydanticOutputParser(pydantic_object=BestReviews)
        prompt = ChatPromptTemplate.from_messages([
            ("system", prompt),
            ("user", "다음은 고객 리뷰 목록입니다:\n\n{review_list}\n\n위 목록에서 당신의 분석 초점에 맞춰 최적의 리뷰 {candidate_count}개를 선택해 주세요.")
        ])
        
        # temperature가 None인 경우 ChatOpenAI에 전달하지 않음
        model_kwargs = {"model": llm_config.model}
        if llm_config.temperature is not None:
            model_kwargs["temperature"] = llm_config.temperature
        
        model = ChatOpenAI(**model_kwargs)
        chain = prompt | model | parser

        review_list_str = "\n".join([
            f"- ID: {r['id']}, 평점: {r['rating']}, 내용: {r['text']}, 이미지 존재 여부 : {r['image_exist']}, 작성일 : {r['createdAt']}"
            for r in reviews
        ])

        try:
            response = chain.invoke({
                "focus": focus_instruction,
                "review_list": review_list_str,
                "candidate_count": candidate_count,
                "format_instructions": parser.get_format_instructions()
            })
            candidates = response.candidates
            print(f"-> {llm_name} 선택 ID: {[c.id for c in candidates]}")

            selected_reviews_map = {r['id']: r for r in reviews}
            final_selected_reviews = [
                {**selected_reviews_map[candidate.id], "score": candidate.score}
                for candidate in candidates if candidate.id in selected_reviews_map
            ]

            # 🎯 결과를 캐시에 저장
            cache.save_result(
                llm_name=llm_config.model,  # 캐시 조회시와 동일한 키 사용
                reviews=reviews,
                focus_instruction=focus_instruction,
                candidate_count=candidate_count,
                result=final_selected_reviews
            )

            # fan-in을 위해 'selected_reviews' 키로 반환
            return {"selected_reviews": final_selected_reviews}
        except Exception as e:
            print(f"LLM({llm_name}) 호출 중 오류 발생: {e}")
            return {"selected_reviews": []}

    return llm_selector_node


# 각기 다른 선택을 하는 3개의 LLM 노드 생성
focus_instruction = """
구매를 망설이는 고객에게 도움이 될 수 있도록,
제품의 장점과 단점을 균형 있게 전달하며,
사진이나 구체적인 사용 예시가 포함되어 있고,
초보자도 이해하기 쉬운 상세한 설명과 성능에 대한 객관적 평가가 담겨 있으며,
내용이 길고 인사이트가 풍부하거나 짧지만 인상적인 핵심 문장이 있고,
여러 사람이 공감할 수 있는 대표적 사용 경험과 최근 작성된 신뢰성 있는 긍정적 리뷰를 우선적으로 선택해 주세요.
"""
llm1_select = create_llm_selector_node(LLMName.GPT_o_4_MINI, focus_instruction)
llm2_select = create_llm_selector_node(LLMName.GPT_4_1_NANO, focus_instruction)
llm3_select = create_llm_selector_node(LLMName.GPT_4_1_MINI, focus_instruction)

__all__ = [
    "check_review_exist",
    "use_llm_node",
    "llm1_select",
    "llm2_select",
    "llm3_select",
]
