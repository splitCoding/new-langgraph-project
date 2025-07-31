from __future__ import annotations

from typing import TypedDict

from langgraph.graph import StateGraph


def create_graph(state: TypedDict, nodes: dict):
    """노드 구성 정보를 바탕으로 자동으로 그래프를 생성합니다."""
    print(f"🔧 그래프 생성 중...")

    graph_builder = StateGraph(state)
    add_nodes(nodes, graph_builder)  # 1. 모든 노드 추가
    set_entry_point(nodes, graph_builder)  # 2. 엔트리 포인트 설정
    add_edges(nodes, graph_builder)  # 3. 엣지 자동 생성
    set_end_points(nodes, graph_builder)  # 4. 종료 포인트 설정

    print(f"✅ 그래프 생성 완료!")
    return graph_builder.compile()


def add_nodes(nodes: dict, graph_builder: StateGraph):
    print("   📌 노드 추가 시작...")
    if not nodes:
        print("⚠️ 노드가 없습니다. 노드를 확인하세요.")
        raise ValueError("노드가 없습니다. 노드를 확인하세요.")
    for node_id, node_config in nodes.items():
        graph_builder.add_node(node_config["node_name"], node_config["node"])
        print(f"   ├── ✅ 노드 추가: {node_config['node_name']}({node_id})")


def set_entry_point(nodes: dict, graph_builder: StateGraph):
    print("   🚪 엔트리 포인트 설정 시작...")
    if not nodes:
        print("⚠️ 노드가 없습니다. 노드를 확인하세요.")
        raise ValueError("노드가 없습니다. 노드를 확인하세요.")

    start_node = None
    for node_id, node_config in nodes.items():
        if node_config.get("is_start"):
            start_node = node_id
            break

    if start_node:
        graph_builder.set_entry_point(nodes[start_node]["node_name"])
        print(f"   ├──  엔트리 포인트 설정: {start_node}")
    else:
        print("⚠️ 엔트리 포인트가 설정되지 않았습니다. 'is_start'가 True인 노드를 확인하세요.")
        raise ValueError("엔트리 포인트가 설정되지 않았습니다. 'is_start'가 True인 노드를 확인하세요.")


def add_edges(nodes: dict, graph_builder: StateGraph):
    """노드 간의 엣지를 추가합니다."""
    print("   ➡️ 엣지 추가 시작...")
    if not nodes:
        print("⚠️ 노드가 없습니다. 노드를 확인하세요.")
        raise ValueError("노드가 없습니다. 노드를 확인하세요.")
    for node_id, node_config in nodes.items():
        node_name = node_config["node_name"]

        # 조건부 엣지 처리
        if "conditional_edge" in node_config:
            conditional_edge = node_config["conditional_edge"]
            condition_checker = conditional_edge["condition_checker"]
            destinations = conditional_edge["destinations"]

            # 조건부 엣지의 목적지들을 노드 이름으로 변환
            mapped_destinations = {}
            for condition, dest_node_id in destinations.items():
                if dest_node_id in nodes:
                    mapped_destinations[condition] = nodes[dest_node_id]["node_name"]

            graph_builder.add_conditional_edges(
                node_name,
                condition_checker,
                mapped_destinations
            )
            print(f"   ├── 🔀조건부 엣지 추가: {node_name} -> {list(destinations.values())}")

        # 일반 엣지 처리
        elif "destinations" in node_config:
            destinations = node_config["destinations"]
            for dest_node_id in destinations:
                if dest_node_id in nodes:
                    dest_node_name = nodes[dest_node_id]["node_name"]
                    graph_builder.add_edge(node_name, dest_node_name)
                    print(f"   ├── 일반 엣지 추가: {node_name} -> {dest_node_name}")


def set_end_points(nodes: dict, graph_builder: StateGraph):
    print("   🏁 종료 포인트 설정 시작...")
    if not nodes:
        print("⚠️ 노드가 없습니다. 노드를 확인하세요.")
        raise ValueError("노드가 없습니다. 노드를 확인하세요.")

    end_nodes = []

    # 종료 포인트 설정
    for node_id, node_config in nodes.items():
        if node_config.get("is_end"):
            end_nodes.append(node_id)

    if end_nodes:
        # 첫 번째 종료 노드를 finish point로 설정
        finish_node = end_nodes[0]
        graph_builder.set_finish_point(nodes[finish_node]["node_name"])
        print(f"     ✅ 종료 포인트 설정: {finish_node}")
    else:
        print("⚠️ 종료 포인트가 설정되지 않았습니다. 'is_end'가 True인 노드를 확인하세요.")
        raise ValueError("종료 포인트가 설정되지 않았습니다. 'is_end'가 True인 노드를 확인하세요.")
