from __future__ import annotations

from langgraph.graph import StateGraph

from .nodes import (
    # 리뷰 수집
    fetch_reviews_node,
    # 후보 선택
    use_llm_node, llm1_select, llm2_select, llm3_select, check_review_exist,
    # 집계 및 재고
    aggregate_best_node, check_inventory_node,
    # 재순위 매기기
    rerank_node,
    # 생성 작업
    generate_summary_node, generate_image_node,
    # DB 업데이트
    update_db_node, check_summary_quality_node
)
from .state import State
from .util import check_summary_quality_with_retry_limit

nodes = {
    "fetch_reviews": {
        "node": fetch_reviews_node,
        "node_name": "DB에서 리뷰 조회"
    },
    "use_llm": {
        "node": use_llm_node,
        "node_name": "AI 모델을 사용하여 BEST 리뷰 후보 선택"
    },
    "llm1_select": {
        "node": llm1_select,
        "node_name": "o4-mini 모델로 후보 선택"
    },
    "llm2_select": {
        "node": llm2_select,
        "node_name": "4.1-nano 모델로 후보 선택"
    },
    "llm3_select": {
        "node": llm3_select,
        "node_name": "4.1-mini 모델로 후보 선택"
    },
    "aggregate_best": {
        "node": aggregate_best_node,
        "node_name": "후보들중 BEST 리뷰 선정"
    },
    "check_inventory": {
        "node": check_inventory_node,
        "node_name": "재고 현황 반영"
    },
    "rerank_auto": {
        "node": rerank_node,
        "node_name": "BEST 리뷰 검증"
    },
    "generate_summary": {
        "node": generate_summary_node,
        "node_name": "BEST 리뷰 요약 생성"
    },
    "check_summary_quality": {
        "node": check_summary_quality_node,
        "node_name": "요약 품질 검증"
    },
    "generate_image_from_review": {
        "node": generate_image_node,
        "node_name": "generate_image_from_review"
    },
    "update_db": {
        "node": update_db_node,
        "node_name": "DB 업데이트"
    },
    "end": {
        "node": lambda state: state,
        "node_name": "프로세스 종료"
    }
}


def create_review_graph():
    print(f"🔧 그래프 생성 중...")

    graph_builder = StateGraph(State)

    for key, value in nodes.items():
        graph_builder.add_node(value["node_name"], value["node"])

    graph_builder.set_entry_point(nodes["fetch_reviews"]["node_name"])
    graph_builder.add_conditional_edges(
        nodes["fetch_reviews"]["node_name"],
        check_review_exist,
        {
            True: nodes["use_llm"]["node_name"],
            False: nodes["end"]["node_name"]
        }
    )
    graph_builder.add_edge(nodes["fetch_reviews"]["node_name"], nodes["use_llm"]["node_name"])
    graph_builder.add_edge(nodes["use_llm"]["node_name"], nodes["llm1_select"]["node_name"])
    graph_builder.add_edge(nodes["use_llm"]["node_name"], nodes["llm2_select"]["node_name"])
    graph_builder.add_edge(nodes["use_llm"]["node_name"], nodes["llm3_select"]["node_name"])
    graph_builder.add_edge(nodes["llm1_select"]["node_name"], nodes["aggregate_best"]["node_name"])
    graph_builder.add_edge(nodes["llm2_select"]["node_name"], nodes["aggregate_best"]["node_name"])
    graph_builder.add_edge(nodes["llm3_select"]["node_name"], nodes["aggregate_best"]["node_name"])
    # graph_builder.add_edge(nodes["aggregate_best"]["node_name"], nodes["check_inventory"]["node_name"])
    graph_builder.add_edge(nodes["aggregate_best"]["node_name"], nodes["generate_summary"]["node_name"])
    # graph_builder.add_conditional_edges(
    #     "aggregate_best",
    #     lambda state: state["apply_stock_bonus"],
    #     {True: "check_inventory", False: "rerank_auto"}
    # )
    # graph_builder.add_edge(nodes["check_inventory"]["node_name"], nodes["rerank_auto"]["node_name"])
    # graph_builder.add_conditional_edges(
    #     nodes["rerank_auto"]["node_name"],
    #     check_confidence_with_retry_limit,
    #     {
    #         "high_confidence": nodes["generate_summary"]["node_name"],
    #         "low_confidence": nodes["fetch_reviews"]["node_name"]
    #     }
    # )
    graph_builder.add_edge(nodes["generate_summary"]["node_name"], nodes["check_summary_quality"]["node_name"])
    graph_builder.add_conditional_edges(
        nodes["check_summary_quality"]["node_name"],
        lambda s: "pass_and_gen" if check_summary_quality_with_retry_limit(s) == 'pass' and s.get('generate_image',
                                                                                                  False) else \
            "pass_and_skip" if check_summary_quality_with_retry_limit(s) == 'pass' and not s.get('generate_image',
                                                                                                 False) else \
                "fail",
        {
            # "pass_and_gen": nodes["generate_image_from_review"]["node_name"],
            "pass_and_skip": nodes["update_db"]["node_name"],
            "fail": nodes["generate_summary"]["node_name"]
        }
    )
    # graph_builder.add_edge(nodes["generate_image_from_review"]["node_name"], nodes["update_db"]["node_name"])
    graph_builder.add_edge(nodes["update_db"]["node_name"], nodes["end"]["node_name"])
    graph_builder.set_finish_point(nodes["end"]["node_name"])
    return graph_builder.compile()
