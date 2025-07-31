from typing import Literal

from src.review.state.state import State


def check_confidence_with_retry_limit(state: State) -> str:
    """신뢰도 점수에 따라 분기하고, 재시도 횟수를 제한하는 조건 함수"""
    print(f"\n[CONDITION] 신뢰도 확인 중... (재시도 횟수: {state.get('retry_count', 0)})")
    retry = state.get("retry_count", 0)
    # rerank_node에서 confidence가 생성되었다고 가정
    confidence = state.get("confidence", 1)

    if confidence > 0.75:
        print("-> 결과: 신뢰도 높음 (high_confidence)")
        return "high_confidence"
    elif retry < 2:
        print("-> 결과: 신뢰도 낮음, 재시도 (low_confidence)")
        return "low_confidence"
    else:
        print("-> 결과: 재시도 횟수 초과, 강제 진행 (high_confidence)")
        return "high_confidence"


def check_summary_quality_with_retry_limit(state: State) -> str:
    """요약 품질을 확인하고, 재시도 횟수를 제한하는 조건 함수"""
    retry = state.get("result_generate_retry_count", 0)
    results = state.get("results", [])
    if len(results) == 0:
        print("-> 결과: 요약이 없습니다, 재시도 (fail)")
        return "error"

    print(f"\n[CONDITION] 요약 품질 확인 중... (재시도 횟수: {retry})")

    return "pass"
    # if len(summary.strip()) < 10 and retry < 2:
    #     print(f"-> 결과: 품질 미달 (요약 길이: {len(summary.strip())}), 재시도 (fail)")
    #     return "fail"
    #
    # if len(summary.strip()) < 10 and retry >= 2:
    #     print(f"-> 결과: 품질 미달이지만 재시도 횟수 초과, 통과 (pass)")
    #     return "pass"
    #
    # print(f"-> 결과: 품질 만족, 통과 (pass)")
    # return "pass"


def check_image_generation_required(state: State) -> Literal["generate_image", "skip_image"]:
    """이미지 생성 여부를 결정하는 조건 함수"""
    if state.get("generate_image"):
        print("\n[CONDITION] 이미지 생성 필요 (generate_image)")
        return "generate_image"
    else:
        print("\n[CONDITION] 이미지 생성 불필요 (skip_image)")
        return "skip_image"
