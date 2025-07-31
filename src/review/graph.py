"""LangGraph single-node graph template.

Returns a predefined response. Replace logic and configuration as needed.
"""

from __future__ import annotations

from src.review.nodes import (
    # 리뷰 수집
    fetch_reviews_node,
    # 후보 선택
    use_llm_node, llm1_select, llm2_select, llm3_select, check_review_exist,
    # 재순위 매기기
    rerank_node,
    # DB 업데이트
    update_db_node
)
# Define the graph
from src.review.nodes.llm import (
    # 후보 선택
    # 집계 및 재고
    aggregate_best_node, check_inventory_node,
    # 생성 작업
    generate_summary_node, generate_image_node, check_summary_quality_node,
)
from src.review.state import State
from src.review.condition_checker import check_summary_quality_with_retry_limit
from src.util.graph_generator import create_graph

nodes: dict[str, dict] = {
    "fetch_reviews": {
        "is_start": True,
        "node": fetch_reviews_node,
        "node_name": "1.DB에서 리뷰 조회",
        "conditional_edge": {
            "condition_checker": check_review_exist,
            "destinations": {
                True: "use_llm",  # 리뷰가 존재하는 경우 LLM을 사용하여 후보 선택
                False: "end"  # 리뷰가 존재하지 않는 경우 프로세스 종료
            }
        }
    },
    "use_llm": {
        "node": use_llm_node,
        "node_name": "2.AI 모델을 사용하여 BEST 리뷰 후보 선택",
        "destinations": ["llm1_select", "llm2_select", "llm3_select"],
    },
    "llm1_select": {
        "node": llm1_select,
        "node_name": "2-1. o4-mini 모델로 후보 선택",
        "destinations": ["aggregate_best"],
    },
    "llm2_select": {
        "node": llm2_select,
        "node_name": "2-2. 4.1-nano 모델로 후보 선택",
        "destinations": ["aggregate_best"],
    },
    "llm3_select": {
        "node": llm3_select,
        "node_name": "2-3. 4.1-mini 모델로 후보 선택",
        "destinations": ["aggregate_best"],
    },
    "aggregate_best": {
        "node": aggregate_best_node,
        "node_name": "3. 후보들중 BEST 리뷰 선정",
        "destinations": ["generate_summary"],
    },
    "check_inventory": {
        "node": check_inventory_node,
        "node_name": "3-1. 재고 현황 반영"
    },
    "rerank_auto": {
        "node": rerank_node,
        "node_name": "3-2. BEST 리뷰 검증"
    },
    "generate_summary": {
        "node": generate_summary_node,
        "node_name": "4. BEST 리뷰 요약 생성",
        "destinations": ["check_summary_quality"]
    },
    "check_summary_quality": {
        "node": check_summary_quality_node,
        "node_name": "4-1. 요약 품질 검증",
        "conditional_edge": {
            "condition_checker": lambda s: "pass_and_gen" if check_summary_quality_with_retry_limit(
                s) == 'pass' and s.get('generate_image',
                                       False) else \
                "pass_and_skip" if check_summary_quality_with_retry_limit(s) == 'pass' and not s.get('generate_image',
                                                                                                     False) else \
                    "fail",
            "destinations": {
                # 품질이 통과되고 이미지 생성이 필요한 경우
                "pass_and_gen": "generate_image_from_review",
                # 품질이 통과되지만 이미지 생성이 필요하지 않은 경우
                "pass_and_skip": "update_db",
                # 품질이 통과되지 않은 경우 다시 요약 생성
                "fail": "generate_summary"
            }
        }
    },
    "generate_image_from_review": {
        "node": generate_image_node,
        "node_name": "4-2. generate_image_from_review",
        "destinations": ["update_db"]
    },
    "update_db": {
        "node": update_db_node,
        "node_name": "5. DB 업데이트",
        "destinations": ["end"]
    },
    "end": {
        "is_end": True,
        "node": lambda state: state,
        "node_name": "6. 프로세스 종료"
    }
}

graph = (
    create_graph(State, nodes=nodes)
)
