"""Refactored review analysis graph."""

import logging
from typing import Any, Callable
from dataclasses import dataclass, field

from src.util.graph_generator import create_graph
from src.review.states import State
from src.review.config import NodeNames, ReviewConfig, get_node_implementation

logger = logging.getLogger(__name__)


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


def dynamic_fanout_condition(state) -> str:
    """동적 fan-out을 위한 조건 함수."""
    criteria_list = state.get("criteria_by_type", [])
    if not criteria_list:
        return NodeNames.END
    
    # 첫 번째 criteria로 시작
    first_criteria = criteria_list[0]
    return f"{first_criteria['type'].lower()}_perspective"


def create_augmented_nodes(config: ReviewConfig = None) -> list[AugmentedNode]:
    """Create augmented nodes based on configuration."""
    config = config or ReviewConfig()
    
    return [
        AugmentedNode.start(
            name=NodeNames.LOAD_REVIEWS,
            implementation=get_node_implementation(NodeNames.LOAD_REVIEWS, config),
            destinations=[NodeNames.FILTER_BY_RULES]
        ),
        AugmentedNode.of(
            name=NodeNames.FILTER_BY_RULES,
            implementation=get_node_implementation(NodeNames.FILTER_BY_RULES, config),
            destinations=[NodeNames.CHECK_REVIEW_EXISTS]
        ),
        AugmentedNode.of(
            name=NodeNames.CHECK_REVIEW_EXISTS,
            implementation=get_node_implementation(NodeNames.CHECK_REVIEW_EXISTS, config),
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
            implementation=get_node_implementation(NodeNames.PICK_CANDIDATES, config),
            destinations=[NodeNames.FUSE_CANDIDATES]
        ),
        AugmentedNode.of(
            name=NodeNames.FUSE_CANDIDATES,
            implementation=get_node_implementation(NodeNames.FUSE_CANDIDATES, config),
            destinations=[NodeNames.END]
        ),
        AugmentedNode.end(
            name=NodeNames.END,
            implementation=get_node_implementation(NodeNames.END, config)
        )
    ]


def create_review_graph(config: ReviewConfig = None):
    """리뷰 분석 그래프를 생성합니다.

    Args:
        config: 리뷰 분석 설정

    Returns:
        생성된 LangGraph 인스턴스

    Raises:
        Exception: 그래프 생성 중 오류 발생 시
    """
    try:
        logger.info("리뷰 분석 그래프 생성 시작")
        
        config = config or ReviewConfig()
        augmented_nodes = create_augmented_nodes(config)
        graph = create_graph(State, nodes=augmented_nodes)

        logger.info("리뷰 분석 그래프 생성 완료")
        return graph

    except Exception as e:
        logger.error(f"그래프 생성 중 오류 발생: {e}")
        raise


# Default graph instance
graph = create_review_graph()