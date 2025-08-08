"""리뷰 처리 관련 비즈니스 로직."""

import streamlit as st
from typing import List, Dict, Any

from ..models import SAMPLE_REVIEWS, CriteriaByReviewType
from .api_client import invoke_best_review_select_api


def convert_ui_reviews_to_langgraph_format(ui_reviews: List[Dict]) -> List[Dict[str, Any]]:
    """UI 형식의 리뷰를 LangGraph 형식으로 변환."""
    converted_reviews = []
    for review in ui_reviews:
        converted_review = {
            "id": review["id"],
            "text": review["content"],  # UI의 content -> LangGraph의 text
            "rating": review["rating"],
            "created_at": "2024-01-01",  # 기본값
            "image_exists": review["has_image"]  # UI의 has_image -> LangGraph의 image_exists
        }
        converted_reviews.append(converted_review)
    return converted_reviews


def real_review_selection() -> List[Dict[str, Any]]:
    """리뷰 선정 - 실제 LangGraph API 호출."""
    print("실제 리뷰 선정 호출")
    try:
        # LangGraph API 입력 형식
        input_data = {
            "mall_id": st.session_state.get("mall_id", "test_mall"),
            "shop_id": st.session_state.get("shop_id", "test_shop"), 
            "criteria_by_type": st.session_state.get("criteria_by_type", {}),
        }
        
        # LangGraph API 호출
        result = invoke_best_review_select_api(input_data)
        if result and "error" not in result:
            # API 응답에서 리뷰 데이터 추출)
            state = result.get("state", {})
            values = state.get("values", {})
            filtered_reviews = values.get("filtered_reviews", [])
            selected_candidates = values.get("selected_candidates", [])
            print("리뷰:", filtered_reviews)
            print("선택된 후보:", selected_candidates)
            
            if selected_candidates:
                # LangGraph 응답을 UI 형식으로 변환
                ui_reviews = [] 
                for candidate in selected_candidates:
                    review_id = candidate.get("review_id", None)
                    # 원본 리뷰 찾기
                    original_review = next((r for r in filtered_reviews if r["id"] == review_id), None)
                    if original_review:
                        ui_reviews.append({
                            "review": original_review,
                            "avg_score": candidate.get("avg_score", 0),
                            "scores": candidate.get("score", [])
                        })

                return ui_reviews if ui_reviews else simulate_review_selection()
            else:
                # API 응답이 비어있으면 폴백
                st.warning("API에서 빈 응답을 받았습니다. 샘플 데이터를 사용합니다.")
                return simulate_review_selection()
        else:
            # API 에러 시 폴백
            error_msg = result.get("error", "알 수 없는 오류") if result else "API 응답 없음"
            st.warning(f"API 호출 실패: {error_msg}. 샘플 데이터를 사용합니다.")
            return simulate_review_selection()
            
    except Exception as e:
        st.error(f"API 호출 중 오류 발생: {str(e)}")
        return simulate_review_selection()


def simulate_review_selection() -> List[Dict[str, Any]]:
    """리뷰 선정 시뮬레이션 (폴백)."""
    selected_reviews = []

    if "포토 리뷰" in st.session_state.selected_types:
        selected_reviews.extend([r for r in SAMPLE_REVIEWS if r["image_exists"]])

    if "긍정적인 리뷰" in st.session_state.selected_types:
        selected_reviews.extend([r for r in SAMPLE_REVIEWS if r["rating"] >= 4])

    # 중복 제거
    seen_ids = set()
    unique_reviews = []
    for review in selected_reviews:
        if review["id"] not in seen_ids:
            unique_reviews.append({"review": review, "avg_score": 85.0, "scores": []})
            seen_ids.add(review["id"])

    return unique_reviews[:3]  # 최대 3개 반환


def format_criteria_text(criteria_dict: Dict[str, List[str]]) -> str:
    """기준을 마크다운 형식으로 포맷팅."""
    text = "각 타입별로 고려할 항목들입니다.\n\n"
    for type_name, criteria in criteria_dict.items():
        text += f"- **{type_name}**\n"
        for criterion in criteria:
            text += f"  - {criterion}\n"
        text += "\n"
    return text


def format_criteria_list_text(criteria_list: List[CriteriaByReviewType]) -> str:
    """CriteriaByReviewType 리스트를 마크다운 형식으로 포맷팅."""
    text = "각 타입별로 고려할 항목들입니다.\n\n"
    for criteria in criteria_list:
        criteria_type = criteria.get("type", "")
        criteria_items = criteria.get("criteria", [])
        text += f"- **{criteria_type}**\n"
        for criterion in criteria_items:
            text += f"  - {criterion}\n"
        text += "\n"
    return text
