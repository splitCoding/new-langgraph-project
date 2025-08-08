from dataclasses import dataclass, field
from typing import TypedDict, Callable, Any

from langgraph.graph import StateGraph


@dataclass
class ConditionalEdge:
    """조건부 엣지 타입 정의."""
    condition_checker: Callable[[Any], Any]  # 조건을 확인하는 함수
    destinations: dict[Any, str]  # 조건에 따른 목적지 노드 이름들


@dataclass
class AugmentedNode:
    """노드에 추가 정보를 포함하는 타입 정의."""
    name: str
    implementation: Callable[[Any], Any] | None = None  # 노드 구현 함수
    is_start: bool = False  # 시작 노드 여부
    is_end: bool = False  # 종료 노드 여부
    conditional_edge: ConditionalEdge | None = None  # 조건부 엣지 정보
    destinations: list[str] = field(default_factory=list)  # 목적지 노드 이름들

    @classmethod
    def start(cls, name: str, implementation: Callable[[Any], Any], destinations: list[str] | None = None,
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
    def end(cls, name: str, implementation: Callable[[Any], Any]) -> "AugmentedNode":
        """종료 노드를 생성하는 팩토리 메서드."""
        return cls(
            name=name,
            implementation=implementation,
            is_end=True
        )

    @classmethod
    def of(cls, name: str, implementation: Callable[[Any], Any], destinations: list[str] | None = None,
           conditional_edge: ConditionalEdge | None = None) -> "AugmentedNode":
        """일반 노드를 생성하는 팩토리 메서드."""
        return cls(
            name=name,
            implementation=implementation,
            destinations=destinations or [],
            conditional_edge=conditional_edge
        )


def create_graph(state: Any, nodes: list[AugmentedNode]):
    """노드 구성 정보를 바탕으로 자동으로 그래프를 생성합니다."""
    print(f"🔧 그래프 생성 중...")

    graph_builder = StateGraph(state)
    add_nodes(nodes, graph_builder)  # 1. 모든 노드 추가
    set_entry_point(nodes, graph_builder)  # 2. 엔트리 포인트 설정
    add_edges(nodes, graph_builder)  # 3. 엣지 자동 생성
    set_end_points(nodes, graph_builder)  # 4. 종료 포인트 설정

    print(f"✅ 그래프 생성 완료!")
    return graph_builder.compile()


def add_nodes(nodes: list[AugmentedNode], graph_builder: StateGraph):
    print("   📌 노드 추가 시작...")
    if not nodes:
        print("⚠️ 노드가 없습니다. 노드를 확인하세요.")
        raise ValueError("노드가 없습니다. 노드를 확인하세요.")
    for node in nodes:
        graph_builder.add_node(node.name, node.implementation)
        print(f"   ├── ✅ 노드 추가: {node.name}")


def set_entry_point(nodes: list[AugmentedNode], graph_builder: StateGraph):
    print("   🚪 엔트리 포인트 설정 시작...")
    if not nodes:
        print("⚠️ 노드가 없습니다. 노드를 확인하세요.")
        raise ValueError("노드가 없습니다. 노드를 확인하세요.")

    start_node = None
    for node in nodes:
        if node.is_start:
            start_node = node
            break

    if start_node:
        graph_builder.set_entry_point(node.name)
        print(f"   ├──  엔트리 포인트 설정: {start_node}")
    else:
        print("⚠️ 엔트리 포인트가 설정되지 않았습니다. 'is_start'가 True인 노드를 확인하세요.")
        raise ValueError("엔트리 포인트가 설정되지 않았습니다. 'is_start'가 True인 노드를 확인하세요.")


def add_edges(nodes: list[AugmentedNode], graph_builder: StateGraph):
    """노드 간의 엣지를 추가합니다."""
    print("   ➡️ 엣지 추가 시작...")
    if not nodes:
        print("⚠️ 노드가 없습니다. 노드를 확인하세요.")
        raise ValueError("노드가 없습니다. 노드를 확인하세요.")
    for node in nodes:
        # 조건부 엣지 처리
        if node.conditional_edge:
            condition_checker = node.conditional_edge.condition_checker
            destinations = node.conditional_edge.destinations

            # 조건부 엣지의 목적지들을 노드 이름으로 변환
            graph_builder.add_conditional_edges(
                node.name,
                condition_checker,
                destinations
            )
            print(f"   ├── 🔀조건부 엣지 추가: {node.name} -> {list(destinations.values())}")

        # 일반 엣지 처리
        elif node.destinations:
            for destination in node.destinations:
                if node in nodes:
                    # nodes 중에 destination 과 동일한 name을 가진 노드를 찾기
                    dest_node = next((n for n in nodes if n.name == destination), None)
                    if dest_node:
                        graph_builder.add_edge(node.name, dest_node.name)
                        print(f"   ├── 일반 엣지 추가: {node.name} -> {dest_node.name}")


def set_end_points(nodes: list[AugmentedNode], graph_builder: StateGraph):
    print("   🏁 종료 포인트 설정 시작...")
    if not nodes:
        print("⚠️ 노드가 없습니다. 노드를 확인하세요.")
        raise ValueError("노드가 없습니다. 노드를 확인하세요.")

    end_node = None

    # 종료 포인트 설정
    for node in nodes:
        if node.is_end:
            if end_node is not None:
                print("⚠️ 종료 포인트가 여러 개 설정되었습니다. 하나의 종료 포인트만 설정해야 합니다.")
                raise ValueError("종료 포인트가 여러 개 설정되었습니다. 하나의 종료 포인트만 설정해야 합니다.")
            end_node = node

    if end_node:
        graph_builder.set_finish_point(end_node.name)
        print(f"     ✅ 종료 포인트 설정: {end_node.name}")
    else:
        print("⚠️ 종료 포인트가 설정되지 않았습니다. 'is_end'가 True인 노드를 확인하세요.")
        raise ValueError("종료 포인트가 설정되지 않았습니다. 'is_end'가 True인 노드를 확인하세요.")
