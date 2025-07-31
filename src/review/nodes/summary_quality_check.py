from src.review.state.state import State


def check_summary_quality_node(state: State) -> dict:
    print("\n--- 요약 품질 검사 지점 통과 ---")
    # 이 노드는 상태를 변경하지 않음. 단지 조건 분기 전의 경유지 역할.
    return {}


__all__ = ["check_summary_quality_node"]
