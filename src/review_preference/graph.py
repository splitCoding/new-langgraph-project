"""Review Preference Criteria Generator Graph.

사용자가 선택한 리뷰 타입에 대해 LLM이 고려해야 할 항목들을 생성하는 그래프입니다.
"""

from __future__ import annotations

import logging
import os
from typing import List, Dict, TypedDict
from dotenv import load_dotenv
from langchain_core.runnables import RunnableConfig
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END

# .env 파일 로드
load_dotenv()

class CriteriaByReviewType(TypedDict):
    """리뷰 타입별 고려 항목 데이터 모델."""
    type: str  # 리뷰 타입 (예: "품질", "가격")
    criteria: list[str]  # 고려 항목 목록

class Configuration(TypedDict):
    """리뷰 선호도 기준 생성기 설정.

    LLM 모델과 관련된 설정을 정의합니다.
    """
    model_name: str  # 사용할 LLM 모델명 (기본값: "gpt-4o-mini")
    temperature: float  # LLM 온도 설정 (기본값: 0.1)


class State(TypedDict):
    """리뷰 선호도 기준 생성기 상태.

    입력: 사용자가 선택한 리뷰 타입들과 추가 기준
    출력: 각 타입별 고려해야 할 항목들
    """
    # 입력
    selected_review_types: List[str]  # 사용자가 선택한 리뷰 타입들
    additional_criteria: List[str]  # 사용자가 추가한 기준들
    
    # 출력
    criteria_by_type: List[CriteriaByReviewType]  # 타입별 고려 항목들


async def generate_criteria(state: State, config: RunnableConfig) -> Dict[str, any]:
    """LLM을 사용하여 리뷰 타입별 고려 항목들을 생성합니다."""
    
    # 환경변수에서 OpenAI API 키 확인
    openai_api_key = os.getenv("OPENAI_API_KEY")
    if not openai_api_key or openai_api_key == "your_openai_api_key_here":
        raise ValueError("OPENAI_API_KEY 환경변수가 설정되지 않았습니다. .env 파일에 실제 API 키를 설정해주세요.")
    
    # 설정에서 모델 파라미터 추출
    configuration = config.get("configurable", {})
    model_name = configuration.get("model_name", "gpt-4.1-nano")
    temperature = configuration.get("temperature", 0.1)
    
    # LLM 모델 초기화 (환경변수에서 API 키 자동 로드)
    llm = ChatOpenAI(
        model=model_name,
        temperature=temperature,
        api_key=openai_api_key
    )
    
    # 선택된 리뷰 타입들과 추가 기준 추출
    selected_types = state.get("selected_review_types", [])
    if not selected_types or len(selected_types) == 0:
        logging.warning("선택된 리뷰 타입이 없습니다. 기본값을 사용합니다.")
        return {
            "criteria_by_type": []
        }
    additional_criteria = state.get("additional_criteria", [])
    
    # 시스템 프롬프트 작성
    system_prompt = """당신은 전문적인 리뷰 분석 전문가입니다. 
사용자가 선택한 리뷰 타입들에 대해 BEST 리뷰를 선정할 때 고려해야 할 구체적이고 실용적인 항목들을 제안해주세요.

각 리뷰 타입별로 3-5개의 고려 항목을 제안하되, 다음 사항을 고려해주세요:
1. 구체적이고 측정 가능한 기준
2. 실제 리뷰 분석에 도움이 되는 항목
3. 해당 타입의 특성을 잘 반영하는 기준
4. 중복되지 않는 독창적인 항목

응답은 다음 JSON 형식으로 제공해주세요:
{
    "리뷰타입명1": ["고려항목1", "고려항목2", "고려항목3"],
    "리뷰타입명2": ["고려항목1", "고려항목2", "고려항목3"]
}"""

    # 사용자 입력 구성
    user_input_parts = [
        f"선택된 리뷰 타입들: {', '.join(selected_types)}"
    ]
    
    if additional_criteria:
        user_input_parts.append(f"추가로 고려할 기준들: {', '.join(additional_criteria)}")
    
    user_prompt = "\n".join(user_input_parts)
    
    # LLM 호출
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_prompt)
    ]
    
    response = await llm.ainvoke(messages)

    print(f"LLM 응답: {response}")
    
    # 응답 파싱 (JSON 형태로 가정)
    try:
        import json
        # JSON 부분만 추출 (```json 태그가 있을 수 있음)
        response_text = response.content
        if "```json" in response_text:
            json_start = response_text.find("```json") + 7
            json_end = response_text.find("```", json_start)
            json_text = response_text[json_start:json_end].strip()
        elif "{" in response_text and "}" in response_text:
            json_start = response_text.find("{")
            json_end = response_text.rfind("}") + 1
            json_text = response_text[json_start:json_end]
        else:
            json_text = response_text
            
        criteria_dict = json.loads(json_text)
        
        # 딕셔너리를 CriteriaByReviewType 리스트로 변환
        criteria_by_type = []
        for review_type, criteria_list in criteria_dict.items():
            # 추가 기준이 있으면 해당 타입에 추가
            if additional_criteria:
                criteria_list.extend([f"**[사용자 추가] {criteria}**" for criteria in additional_criteria])
            
            criteria_by_type.append(CriteriaByReviewType(
                type=review_type,
                criteria=criteria_list
            ))
        
    except (json.JSONDecodeError, Exception) as e:
        # JSON 파싱 실패 시 기본값 사용
        print(f"LLM 응답 파싱 실패: {e}")
        criteria_by_type = []
        for review_type in selected_types:
            criteria_list = [
                "리뷰 내용의 구체성",
                "정보의 신뢰성",
                "다른 사용자에게 도움이 되는 정도"
            ]
            if additional_criteria:
                criteria_list.extend([f"**[사용자 추가] {criteria}**" for criteria in additional_criteria])
            
            criteria_by_type.append(CriteriaByReviewType(
                type=review_type,
                criteria=criteria_list
            ))
    
    return {
        "criteria_by_type": criteria_by_type,
    }


# 그래프 정의
graph = (
    StateGraph(State, config_schema=Configuration)
    .add_node("generate_criteria", generate_criteria)
    .add_edge("__start__", "generate_criteria")
    .add_edge("generate_criteria", END)
    .compile()
)
