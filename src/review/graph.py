from dataclasses import dataclass, field
import logging
import asyncio
import concurrent.futures
import time
from typing import Any, Callable

from src.util.graph_generator import create_graph
from src.review.states import State, Review

def get_logger(name: str) -> logging.Logger:
    """로거 인스턴스를 반환합니다.

    Args:
        name: 로거 이름

    Returns:
        로거 인스턴스
    """
    return logging.getLogger(name)


logger = get_logger(__name__)

perspectives = [
    "QUALITY_PERSPECTIVE_PROMPT",
    "AUTHENTICITY_PERSPECTIVE_PROMPT",
    "HELPFULNESS_PERSPECTIVE_PROMPT"
]


@dataclass
class ConditionalEdge:
    """조건부 엣지 타입 정의."""
    condition_checker: Callable[[Any], Any]  # 조건을 확인하는 함수
    destinations: dict[Any, str]  # 조건에 따른 목적지 노드 이름들


@dataclass
class AugmentedNode:
    """노드에 추가 정보를 포함하는 타입 정의."""
    name: str
    implementation: Callable[[State], Any] | None = None  # 노드 구현 함수
    is_start: bool = False  # 시작 노드 여부
    is_end: bool = False  # 종료 노드 여부
    conditional_edge: ConditionalEdge | None = None  # 조건부 엣지 정보
    destinations: list[str] = field(default_factory=list)  # 목적지 노드 이름들

    @classmethod
    def start(cls, name: str, implementation: Callable[[State], Any], destinations: list[str] | None = None,
              conditional_edge: ConditionalEdge | None = None) -> "AugmentedNode":
        """시작 노드를 생성하는 팩토리 메서드."""
        return cls(
            name=name,
            implementation=implementation,
            is_start=True,
            destinations=destinations or [],
            conditional_edge=conditional_edge
        )

    @classmethod
    def end(cls, name: str, implementation: Callable[[State], Any]) -> "AugmentedNode":
        """종료 노드를 생성하는 팩토리 메서드."""
        return cls(
            name=name,
            implementation=implementation,
            is_end=True
        )

    @classmethod
    def of(cls, name: str, implementation: Callable[[State], Any], destinations: list[str] | None = None,
           conditional_edge: ConditionalEdge | None = None) -> "AugmentedNode":
        """일반 노드를 생성하는 팩토리 메서드."""
        return cls(
            name=name,
            implementation=implementation,
            destinations=destinations or [],
            conditional_edge=conditional_edge
        )


def fuse_candidates_implementation(state):
    """후보들을 병합하고 Human review 처리를 위해 준비합니다."""
    candidates = state.get("candidates", [])
    approved_candidates = state.get("approved_candidates", [])
    
    # Human feedback이 처리된 경우 approved_candidates 사용
    if approved_candidates:
        candidates = approved_candidates
        logger.info(f"Using human-approved candidates: {len(candidates)}")
    
    # 각 후보의 점수 정보 로깅
    if not candidates:
        logger.info("No candidates to process.")
        return {"selected_candidates": []}
    else:
        # 각 후보의 평균 점수 계산
        for candidate in candidates:
            scores = candidate.get("score", [])
            avg_score = sum(s["score"] for s in scores) / len(scores) if scores else 0
            candidate["avg_score"] = avg_score

        # 평균 점수 기준 내림차순 정렬 후 상위 10개 선택
        top_candidates = sorted(candidates, key=lambda c: c.get("avg_score", 0), reverse=True)[:10]
        logger.info(f"Selected top {len(top_candidates)} candidates by average score.")
        return {"selected_candidates": top_candidates}


class NodeNames:
    """그래프 노드 이름 상수."""
    LOAD_REVIEWS = "load_reviews"
    FILTER_BY_RULES = "filter_by_rules"
    CHECK_REVIEW_EXISTS = "check_review_exists"
    PICK_CANDIDATES = "pick_candidates"
    QUALITY_PERSPECTIVE = "quality_perspective"
    AUTHENTICITY_PERSPECTIVE = "authenticity_perspective"
    HELPFULNESS_PERSPECTIVE = "helpfulness_perspective"
    FUSE_CANDIDATES = "fuse_candidates"
    GENERATE_TITLE_AND_SUMMARY = "generate_title_and_summary"
    VALIDATE_TITLE_AND_SUMMARY = "validate_title_and_summary"
    SAVE_BEST_REVIEWS = "save_best_reviews"
    END = "end"


def create_perspective_node(criteria_type: str, criteria: list[str]) -> AugmentedNode:
    """동적으로 관점별 노드를 생성합니다."""
    def perspective_implementation(state):
        return {
            "candidates": [
                {"review_id": review["id"], "score": [{"score": 85, "perspective": criteria_type}]}
                for review in state.get("filtered_reviews", [])[:3]  # 최대 3개
            ]
        }
    
    return AugmentedNode.of(
        name=f"{criteria_type.lower()}_perspective",
        implementation=perspective_implementation,
        destinations=[NodeNames.FUSE_CANDIDATES]
    )


def dynamic_fanout_condition(state) -> str:
    """동적 fan-out을 위한 조건 함수."""
    criteria_list = state.get("criteria_by_type", [])
    if not criteria_list:
        return NodeNames.END
    
    # 첫 번째 criteria로 시작
    first_criteria = criteria_list[0]
    return f"{first_criteria['type'].lower()}_perspective"


def process_single_criteria_sync(criteria_item: dict, filtered_reviews: list) -> dict:
    """단일 criteria 타입을 처리하고 모든 리뷰의 점수를 반환합니다."""
    criteria_type = criteria_item["type"]
    criteria = criteria_item["criteria"]
    
    logger.info(f"Processing criteria: {criteria_type}")
    
    # 각 리뷰에 대한 점수를 계산
    review_scores = {}
    for review in filtered_reviews:
        try:
            # LLM을 사용하여 실제 점수를 생성
            score = score_review_with_llm(review, criteria_type, criteria)
            review_scores[review["id"]] = {"score": score, "perspective": criteria_type}
        except Exception as e:
            logger.error(f"Error scoring review {review['id']} for {criteria_type}: {e}")
            # 오류 시 기본 점수 사용
            score = 50  # 중간 점수
            review_scores[review["id"]] = {"score": score, "perspective": criteria_type}
    
    logger.info(f"Completed processing criteria: {criteria_type} ({len(review_scores)} reviews)")
    return {criteria_type: review_scores}


def score_review_with_llm(review: dict, criteria_type: str, criteria: list) -> int:
    """LLM을 사용하여 리뷰에 점수를 매깁니다."""
    from langchain_core.prompts import ChatPromptTemplate
    from langchain_openai import ChatOpenAI
    from langchain_core.output_parsers import StrOutputParser
    import re
    
    # LLM 모델 초기화
    llm = ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0.1,
        max_tokens=100
    )
    
    # 프롬프트 템플릿 생성
    prompt = ChatPromptTemplate.from_template("""
    다음 리뷰를 {criteria_type} 관점에서 평가해주세요.
    평가 기준: {criteria}
    
    리뷰 내용: {review_text}
    
    평가 요청사항:
    1. 위 기준에 따라 0-100점 사이의 점수를 매겨주세요
    2. 점수만 숫자로 응답해주세요 (예: 85)
    
    점수:
    """)
    
    # 체인 생성
    chain = prompt | llm | StrOutputParser()
    
    try:
        # LLM 호출
        response = chain.invoke({
            "criteria_type": criteria_type,
            "criteria": ", ".join(criteria),
            "review_text": review.get("text", "")
        })
        
        # 응답에서 숫자 추출
        numbers = re.findall(r'\d+', response.strip())
        if numbers:
            score = int(numbers[0])
            # 점수 범위 검증 (0-100)
            score = max(0, min(100, score))
            logger.debug(f"LLM scored review {review['id']} as {score} for {criteria_type}")
            return score
        else:
            logger.warning(f"Could not extract score from LLM response: {response}")
            return 50  # 기본값
            
    except Exception as e:
        logger.error(f"LLM scoring failed for review {review['id']}: {e}")
        return 50  # 오류 시 기본값


def process_all_perspectives(state):
    """모든 관점을 병렬로 처리합니다 (ThreadPoolExecutor 사용)."""
    criteria_list = state.get("criteria_by_type", [
        {"type": "품질", "criteria": ["성능", "내구성", "디자인"]},
        {"type": "진정성", "criteria": ["솔직함", "경험 기반", "구체성"]},
        {"type": "유용성", "criteria": ["도움됨", "정보성", "실용성"]}
    ])
    
    filtered_reviews = state.get("filtered_reviews", [])
    
    logger.info(f"Starting parallel processing of {len(criteria_list)} criteria types")
    
    # ThreadPoolExecutor를 사용한 병렬 처리
    with concurrent.futures.ThreadPoolExecutor(max_workers=len(criteria_list)) as executor:
        # 각 criteria를 별도 스레드에서 처리
        future_to_criteria = {
            executor.submit(process_single_criteria_sync, criteria_item, filtered_reviews): criteria_item
            for criteria_item in criteria_list
        }
        
        # 모든 criteria의 결과를 수집
        all_results = {}
        
        # 완료된 작업들의 결과를 수집
        for future in concurrent.futures.as_completed(future_to_criteria):
            criteria_item = future_to_criteria[future]
            try:
                result = future.result()
                all_results.update(result)
                logger.info(f"Successfully processed {criteria_item['type']}")
            except Exception as exc:
                logger.error(f"Error processing {criteria_item['type']}: {exc}")
        
        # 리뷰 ID별로 모든 점수를 조합
        candidates = []
        for review in filtered_reviews:
            review_id = review["id"]
            scores = []
            
            for criteria_type in all_results:
                if review_id in all_results[criteria_type]:
                    scores.append(all_results[criteria_type][review_id])
            
            if scores:  # 점수가 있는 경우에만 후보로 추가
                candidates.append({
                    "review_id": review_id,
                    "score": scores
                })
    
    logger.info(f"Completed parallel processing. Total unique candidates: {len(candidates)}")
    return {"candidates": candidates}


async def process_single_criteria_async(criteria_item: dict, filtered_reviews: list) -> list:
    """단일 criteria 타입을 비동기로 처리합니다."""
    criteria_type = criteria_item["type"]
    criteria = criteria_item["criteria"]
    candidates = []
    
    logger.info(f"Processing criteria asynchronously: {criteria_type}")
    
    # 각 리뷰를 해당 criteria로 평가
    for review in filtered_reviews:
        # 비동기 작업 시뮬레이션 (실제로는 비동기 LLM API 호출 등)
        await asyncio.sleep(0.001)  # 1ms 지연으로 비동기 처리 시뮬레이션
        
        # 여기서 실제로는 LLM을 사용하여 각 criteria에 대해 점수를 매겨야 함
        score = 80 + (hash(f"{review['id']}{criteria_type}") % 20)  # 임시 점수 생성
        
        candidate = {
            "review_id": review["id"],
            "score": [{"score": score, "perspective": criteria_type}]
        }
        candidates.append(candidate)
    
    logger.info(f"Completed async processing criteria: {criteria_type} ({len(candidates)} candidates)")
    return candidates


def process_all_perspectives_async_version(state):
    """모든 관점을 비동기로 병렬 처리합니다 (asyncio 사용)."""
    criteria_list = state.get("criteria_by_type", [
        {"type": "품질", "criteria": ["성능", "내구성", "디자인"]},
        {"type": "진정성", "criteria": ["솔직함", "경험 기반", "구체성"]},
        {"type": "유용성", "criteria": ["도움됨", "정보성", "실용성"]}
    ])
    
    filtered_reviews = state.get("filtered_reviews", [])
    
    async def async_process():
        logger.info(f"Starting async parallel processing of {len(criteria_list)} criteria types")
        
        # 각 criteria를 비동기로 병렬 처리
        tasks = [
            process_single_criteria_async(criteria_item, filtered_reviews)
            for criteria_item in criteria_list
        ]
        
        # 모든 작업을 병렬로 실행하고 결과를 수집
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        all_candidates = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Error processing {criteria_list[i]['type']}: {result}")
            else:
                all_candidates.extend(result)
        
        logger.info(f"Completed async parallel processing. Total candidates: {len(all_candidates)}")
        return all_candidates
    
    # 비동기 함수를 동기 컨텍스트에서 실행
    try:
        # 새 이벤트 루프에서 실행
        all_candidates = asyncio.run(async_process())
    except RuntimeError as e:
        logger.warning(f"AsyncIO error: {e}. Falling back to thread-based processing.")
        # asyncio 실행 실패 시 스레드 기반 처리로 폴백
        return process_all_perspectives(state)
    
    return {"candidates": all_candidates}


augmented_nodes = [
    AugmentedNode.start(
        name=NodeNames.LOAD_REVIEWS,
        implementation=lambda state: {"reviews": [
            Review(
                id=1,
                text="이 제품 정말 좋아요! 사용하기 편하고 성능도 뛰어나요.",
                rating=5,
                created_at="2023-10-01",
                image_exists=True
            )
        ]},
        destinations=[NodeNames.FILTER_BY_RULES]
    ),
    AugmentedNode.of(
        name="asdf",
        implementation=lambda state: {
            # 비속어가 존재하는지 openai moderation 으로 검증
            "filtered_reviews": [
                review for review in state.get("reviews", [])
                if review["rating"] >= 4 and len(review["text"]) > 20 and review["image_exists"]
            ]
        },
    ),
    AugmentedNode.of(
        name=NodeNames.FILTER_BY_RULES,
        implementation=lambda state: {
            # 비속어가 존재하는지 openai moderation 으로 검증
            "filtered_reviews": [
                review for review in state.get("reviews", [])
                if review["rating"] >= 4 and len(review["text"]) > 20 and review["image_exists"]
            ]
        },
        destinations=[NodeNames.CHECK_REVIEW_EXISTS]
    ),
    AugmentedNode.of(
        name=NodeNames.CHECK_REVIEW_EXISTS,
        implementation=lambda state: {
            "exists": len(state.get("filtered_reviews", [])) > 0
        },
        conditional_edge=ConditionalEdge(
            condition_checker=lambda state: state.get("exists", False),
            destinations={
                True: NodeNames.PICK_CANDIDATES,
                False: NodeNames.END
            }
        ),
    ),
    AugmentedNode.of(
        name=NodeNames.PICK_CANDIDATES,
        implementation=process_all_perspectives,
        destinations=[NodeNames.FUSE_CANDIDATES]  # Human review로 이동
    ),
    AugmentedNode.of(
        name=NodeNames.FUSE_CANDIDATES,
        implementation=fuse_candidates_implementation,
        destinations=[NodeNames.END]
    ),
    AugmentedNode.end(
        name=NodeNames.END,
        implementation=lambda state: {
            "status": "BEST 리뷰 후보 선정이 완료되었습니다.",
            "selected_candidates": state.get("selected_candidates", [])
        }
    )
]


def create_review_graph():
    """리뷰 분석 그래프를 생성합니다.

    Returns:
        생성된 LangGraph 인스턴스

    Raises:
        Exception: 그래프 생성 중 오류 발생 시
    """
    try:
        logger.info("리뷰 분석 그래프 생성 시작")

        graph = create_graph(State, nodes=augmented_nodes)

        logger.info("리뷰 분석 그래프 생성 완료")
        return graph

    except Exception as e:
        logger.error(f"그래프 생성 중 오류 발생: {e}")
        raise


# 그래프 인스턴스 생성
graph = create_review_graph()
