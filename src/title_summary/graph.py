"""Title and Summary Generator Graph.

선정된 BEST 리뷰들의 제목과 요약을 생성하는 그래프입니다.
"""

from dataclasses import dataclass, field
import logging
from typing import Any, Callable

from src.util.graph_generator import create_graph
from src.title_summary.states import State, SelectedReview

def get_logger(name: str) -> logging.Logger:
    """로거 인스턴스를 반환합니다."""
    return logging.getLogger(name)

logger = get_logger(__name__)

@dataclass
class ConditionalEdge:
    """조건부 엣지 타입 정의."""
    condition_checker: Callable[[Any], Any]
    destinations: dict[Any, str]

@dataclass
class AugmentedNode:
    """노드에 추가 정보를 포함하는 타입 정의."""
    name: str
    implementation: Callable[[State], Any] | None = None
    is_start: bool = False
    is_end: bool = False
    conditional_edge: ConditionalEdge | None = None
    destinations: list[str] = field(default_factory=list)

    @classmethod
    def start(cls, name: str, implementation: Callable[[State], Any], destinations: list[str] | None = None,
              conditional_edge: ConditionalEdge | None = None) -> "AugmentedNode":
        return cls(
            name=name,
            implementation=implementation,
            is_start=True,
            destinations=destinations or [],
            conditional_edge=conditional_edge
        )

    @classmethod
    def end(cls, name: str, implementation: Callable[[State], Any]) -> "AugmentedNode":
        return cls(
            name=name,
            implementation=implementation,
            is_end=True
        )

    @classmethod
    def of(cls, name: str, implementation: Callable[[State], Any], destinations: list[str] | None = None,
           conditional_edge: ConditionalEdge | None = None) -> "AugmentedNode":
        return cls(
            name=name,
            implementation=implementation,
            destinations=destinations or [],
            conditional_edge=conditional_edge
        )

class NodeNames:
    """그래프 노드 이름 상수."""
    VALIDATE_INPUT = "validate_input"
    GENERATE_TITLES = "generate_titles"
    GENERATE_SUMMARIES = "generate_summaries"
    VALIDATE_RESULTS = "validate_results"
    END = "end"

def validate_input_implementation(state):
    """입력 검증."""
    selected_reviews = state.get("selected_reviews", [])
    summary_required_reviews = state.get("summary_required_reviews", [])
    
    if not selected_reviews:
        logger.warning("No selected reviews provided")
        return {"error": "선택된 리뷰가 없습니다."}
    
    logger.info(f"Processing {len(selected_reviews)} selected reviews")
    logger.info(f"Summary required for {len(summary_required_reviews)} reviews")
    
    return {
        "validated": True,
        "review_count": len(selected_reviews)
    }

def generate_titles_implementation(state):
    """선택된 리뷰들의 제목을 생성합니다."""
    from langchain_core.prompts import ChatPromptTemplate
    from langchain_openai import ChatOpenAI
    from langchain_core.output_parsers import StrOutputParser
    import json
    
    selected_reviews = state.get("selected_reviews", [])
    title_style = state.get("title_style", "간결한")
    title_custom_requirements = state.get("title_custom_requirements", "")
    regenerate_requirements = state.get("regenerate_requirements", "")
    
    logger.info(f"Generating titles for {len(selected_reviews)} reviews with style: {title_style}")
    if title_custom_requirements:
        logger.info(f"Custom requirements: {title_custom_requirements}")
    if regenerate_requirements:
        logger.info(f"Regeneration requirements: {regenerate_requirements}")
    
    # LLM 모델 초기화
    llm = ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0.3,
        max_tokens=500
    )
    
    # 추가 요구사항 텍스트 구성
    additional_requirements = ""
    if title_custom_requirements:
        additional_requirements += f"\n5. 사용자 요구사항: {title_custom_requirements}"
    if regenerate_requirements:
        additional_requirements += f"\n6. 재생성 요구사항: {regenerate_requirements}"
    
    # 프롬프트 템플릿 생성
    prompt = ChatPromptTemplate.from_template("""
    다음 리뷰들에 대해 {title_style} 스타일의 제목을 생성해주세요.
    
    리뷰 목록:
    {reviews_text}
    
    요구사항:
    1. 각 리뷰의 핵심 내용을 반영하는 제목 생성
    2. {title_style} 스타일에 맞게 작성
    3. 10-30자 내외로 작성
    4. 다음 JSON 형식으로 응답:{additional_requirements}
    {{
        "titles": [
            {{"review_id": 1, "title": "생성된 제목1"}},
            {{"review_id": 2, "title": "생성된 제목2"}}
        ]
    }}
    """)
    
    # 리뷰 텍스트 구성
    reviews_text = "\n".join([
        f"리뷰 {review['id']}: {review['text']}"
        for review in selected_reviews
    ])
    
    # 체인 생성 및 실행
    chain = prompt | llm | StrOutputParser()
    
    try:
        response = chain.invoke({
            "title_style": title_style,
            "reviews_text": reviews_text,
            "additional_requirements": additional_requirements
        })
        
        # JSON 파싱
        if "```json" in response:
            json_start = response.find("```json") + 7
            json_end = response.find("```", json_start)
            json_text = response[json_start:json_end].strip()
        elif "{" in response and "}" in response:
            json_start = response.find("{")
            json_end = response.rfind("}") + 1
            json_text = response[json_start:json_end]
        else:
            json_text = response
        
        result = json.loads(json_text)
        generated_titles = result.get("titles", [])
        
        logger.info(f"Successfully generated {len(generated_titles)} titles")
        return {"generated_titles": generated_titles}
        
    except Exception as e:
        logger.error(f"Title generation failed: {e}")
        # 폴백: 기본 제목 생성
        generated_titles = [
            {"review_id": review["id"], "title": f"리뷰 {review['id']} 제목"}
            for review in selected_reviews
        ]
        return {"generated_titles": generated_titles}

def generate_summaries_implementation(state):
    """요약이 필요한 리뷰들의 요약을 생성합니다."""
    from langchain_core.prompts import ChatPromptTemplate
    from langchain_openai import ChatOpenAI
    from langchain_core.output_parsers import StrOutputParser
    import json
    
    summary_required_reviews = state.get("summary_required_reviews", [])
    summary_style = state.get("summary_style", "상세한")
    
    if not summary_required_reviews:
        logger.info("No summaries required")
        return {"generated_summaries": []}
    
    logger.info(f"Generating summaries for {len(summary_required_reviews)} reviews with style: {summary_style}")
    
    # LLM 모델 초기화
    llm = ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0.3,
        max_tokens=1000
    )
    
    # 프롬프트 템플릿 생성
    prompt = ChatPromptTemplate.from_template("""
    다음 리뷰들에 대해 {summary_style} 스타일의 요약을 생성해주세요.
    
    리뷰 목록:
    {reviews_text}
    
    요구사항:
    1. 각 리뷰의 핵심 내용과 감정을 요약
    2. {summary_style} 스타일에 맞게 작성
    3. 50-150자 내외로 작성
    4. 다음 JSON 형식으로 응답:
    {{
        "summaries": [
            {{"review_id": 1, "summary": "생성된 요약1"}},
            {{"review_id": 2, "summary": "생성된 요약2"}}
        ]
    }}
    """)
    
    # 리뷰 텍스트 구성
    reviews_text = "\n".join([
        f"리뷰 {review['id']}: {review['text']}"
        for review in summary_required_reviews
    ])
    
    # 체인 생성 및 실행
    chain = prompt | llm | StrOutputParser()
    
    try:
        response = chain.invoke({
            "summary_style": summary_style,
            "reviews_text": reviews_text
        })
        
        # JSON 파싱
        if "```json" in response:
            json_start = response.find("```json") + 7
            json_end = response.find("```", json_start)
            json_text = response[json_start:json_end].strip()
        elif "{" in response and "}" in response:
            json_start = response.find("{")
            json_end = response.rfind("}") + 1
            json_text = response[json_start:json_end]
        else:
            json_text = response
        
        result = json.loads(json_text)
        generated_summaries = result.get("summaries", [])
        
        logger.info(f"Successfully generated {len(generated_summaries)} summaries")
        return {"generated_summaries": generated_summaries}
        
    except Exception as e:
        logger.error(f"Summary generation failed: {e}")
        # 폴백: 기본 요약 생성
        generated_summaries = [
            {"review_id": review["id"], "summary": f"리뷰 {review['id']} 요약"}
            for review in summary_required_reviews
        ]
        return {"generated_summaries": generated_summaries}

def validate_results_implementation(state):
    """생성된 제목과 요약을 검증합니다."""
    generated_titles = state.get("generated_titles", [])
    generated_summaries = state.get("generated_summaries", [])
    
    # 간단한 검증
    validated_titles = []
    for title_item in generated_titles:
        title = title_item.get("title", "")
        is_valid = len(title) >= 5 and len(title) <= 50
        validated_titles.append({
            "review_id": title_item["review_id"],
            "title": title,
            "is_valid": is_valid,
            "validation_message": "제목이 유효합니다." if is_valid else "제목이 너무 짧거나 깁니다."
        })
    
    validated_summaries = []
    for summary_item in generated_summaries:
        summary = summary_item.get("summary", "")
        is_valid = len(summary) >= 20 and len(summary) <= 200
        validated_summaries.append({
            "review_id": summary_item["review_id"],
            "summary": summary,
            "is_valid": is_valid,
            "validation_message": "요약이 유효합니다." if is_valid else "요약이 너무 짧거나 깁니다."
        })
    
    logger.info(f"Validated {len(validated_titles)} titles and {len(validated_summaries)} summaries")
    
    return {
        "validated_titles": validated_titles,
        "validated_summaries": validated_summaries
    }

# 노드 정의
augmented_nodes = [
    AugmentedNode.start(
        name=NodeNames.VALIDATE_INPUT,
        implementation=validate_input_implementation,
        destinations=[NodeNames.GENERATE_TITLES]
    ),
    AugmentedNode.of(
        name=NodeNames.GENERATE_TITLES,
        implementation=generate_titles_implementation,
        destinations=[NodeNames.GENERATE_SUMMARIES]
    ),
    AugmentedNode.of(
        name=NodeNames.GENERATE_SUMMARIES,
        implementation=generate_summaries_implementation,
        destinations=[NodeNames.VALIDATE_RESULTS]
    ),
    AugmentedNode.of(
        name=NodeNames.VALIDATE_RESULTS,
        implementation=validate_results_implementation,
        destinations=[NodeNames.END]
    ),
    AugmentedNode.end(
        name=NodeNames.END,
        implementation=lambda state: {
            "status": "제목 및 요약 생성이 완료되었습니다.",
            "final_results": {
                "titles": state.get("validated_titles", []),
                "summaries": state.get("validated_summaries", [])
            }
        }
    )
]

def create_title_summary_graph():
    """제목/요약 생성 그래프를 생성합니다."""
    try:
        logger.info("제목/요약 생성 그래프 생성 시작")
        graph = create_graph(State, nodes=augmented_nodes)
        logger.info("제목/요약 생성 그래프 생성 완료")
        return graph
    except Exception as e:
        logger.error(f"그래프 생성 중 오류 발생: {e}")
        raise

# 그래프 인스턴스 생성
graph = create_title_summary_graph()
