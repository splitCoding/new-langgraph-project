"""리뷰 에이전트 채팅 인터페이스."""

import streamlit as st
import time
import sys
import os
from dotenv import load_dotenv

# 환경 변수 로드 (.env 파일)
load_dotenv()

# 프로젝트 루트를 Python 경로에 추가
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

try:
    from ..models import ChatState, SAMPLE_REVIEWS, CriteriaByReviewType, SESSION_STATE_DEFAULTS
    from ..services import real_review_selection, get_available_assistants, check_langgraph_server_status, get_store_list, get_store_by_name
    from ..components import (
        add_message, render_review_type_selection, render_custom_input,
        render_criteria_generation, render_criteria, render_additional_criteria, render_candidate_reviews,
        render_title_style_selection, render_title_generation, render_generated_titles, render_title_regeneration,
        render_summary_review_selection, render_summary_style_selection,
        render_summary_generation, render_final_results, render_save_to_db
    )
except ImportError:
    # 직접 실행할 때 절대 import 사용
    from src.ui.models import ChatState, SAMPLE_REVIEWS, CriteriaByReviewType, SESSION_STATE_DEFAULTS
    from src.ui.services import real_review_selection, get_available_assistants, check_langgraph_server_status, get_store_list, get_store_by_name
    from src.ui.components import (
        add_message, render_review_type_selection, render_custom_input,
        render_criteria_generation, render_criteria, render_additional_criteria, render_candidate_reviews,
        render_title_style_selection, render_title_generation, render_generated_titles, render_title_regeneration,
        render_summary_review_selection, render_summary_style_selection,
        render_summary_generation, render_final_results, render_save_to_db
    )


def initialize_session_state():
    """세션 상태 초기화."""
    for key, config in SESSION_STATE_DEFAULTS.items():
        field_name = config["name"]
        default_value = config["default_value"]
        
        if field_name not in st.session_state:
            st.session_state[field_name] = default_value


def main():
    """메인 애플리케이션."""
    # 페이지 설정
    st.set_page_config(
        page_title="BEST 리뷰 에이전트",
        page_icon="⭐",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    # 세션 상태 초기화
    initialize_session_state()

    # 사이드바
    with st.sidebar:
        # st.markdown("---")
        
        # 현재 상태 표시
        # current_state = st.session_state.chat_state.value if hasattr(st.session_state.chat_state, 'value') else str(st.session_state.chat_state)
        # st.info(f"**현재 상태:** {current_state}")
        
        # 진행 상황 표시
        st.header("📊 진행 상황")
        
        steps = [
            ("리뷰 타입 선택", len(st.session_state.selected_types) > 0),
            ("후보 리뷰 선정", len(st.session_state.candidate_reviews) > 0),
            ("리뷰 선택", len(st.session_state.selected_reviews) > 0),
            ("제목 생성", len(st.session_state.final_titles) > 0),
            ("요약 생성", len(st.session_state.final_summaries) > 0)
        ]
        
        for step_name, completed in steps:
            if completed:
                st.success(f"✅ {step_name}")
            else:
                st.info(f"⏳ {step_name}")
        
        st.markdown("---")
        
        # 통계 정보
        st.subheader("📈 통계")
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric("선택된 타입", len(st.session_state.selected_types))
            st.metric("후보 리뷰", len(st.session_state.candidate_reviews))
        
        with col2:
            st.metric("선택된 리뷰", len(st.session_state.selected_reviews))
            st.metric("생성된 제목", len(st.session_state.final_titles))
        
        st.markdown("---")
        
        # Mall ID와 Shop ID 설정
        st.subheader("🏪 매장 정보")
        
        # 매장 목록 조회
        stores = get_store_list()
        store_names = ["직접 입력"] + [store["name"] for store in stores]
        
        # 매장 선택
        selected_store_name = st.selectbox(
            "매장 선택",
            store_names,
            index=0,
            help="매장을 선택하거나 직접 입력하세요"
        )
        
        if selected_store_name == "직접 입력":
            # 직접 입력 모드
            mall_id = st.text_input(
                "Mall ID",
                value=st.session_state.mall_id,
                help="분석할 쇼핑몰의 ID를 입력하세요"
            )
            shop_id = st.text_input(
                "Shop ID", 
                value=st.session_state.shop_id,
                help="분석할 상점의 ID를 입력하세요"
            )
            
            # 세션 상태 업데이트
            if mall_id != st.session_state.mall_id:
                st.session_state.mall_id = mall_id
            if shop_id != st.session_state.shop_id:
                st.session_state.shop_id = shop_id
            st.session_state.selected_store_name = ""
            
        else:
            # 매장 선택 모드
            if selected_store_name != st.session_state.selected_store_name:
                # 새로운 매장이 선택된 경우
                store_info = get_store_by_name(selected_store_name)
                if store_info:
                    st.session_state.mall_id = store_info["mall_id"]
                    st.session_state.shop_id = store_info["shop_id"]
                    st.session_state.selected_store_name = selected_store_name
            
            # 현재 선택된 매장 정보 표시
            st.info(f"**Mall ID:** {st.session_state.mall_id}")
            st.info(f"**Shop ID:** {st.session_state.shop_id}")
        
        # 현재 설정 표시
        if st.session_state.mall_id and st.session_state.shop_id:
            if st.session_state.selected_store_name:
                st.success(f"📍 {st.session_state.selected_store_name}")
            else:
                st.success(f"📍 {st.session_state.mall_id} > {st.session_state.shop_id}")
        else:
            st.warning("매장 정보를 선택하거나 입력해주세요")
        
        st.markdown("---")
        
        # # 초기화 버튼
        # if st.button("🔄 전체 초기화", type="secondary"):
        #     for key, config in SESSION_STATE_DEFAULTS.items():
        #         field_name = config["name"]
        #         default_value = config["default_value"]
        #         st.session_state[field_name] = default_value
        #     st.rerun()

        # st.markdown("---")

        # Assistant 목록 새로고침 버튼

        st.subheader("⚙️ 설정")
        
        # LangGraph 서버 상태 및 Assistant 선택
        st.subheader("🤖 LangGraph 서버")
        
        # 서버 상태 확인
        server_status = check_langgraph_server_status()
        if server_status:
            st.success("🟢 서버 연결됨")
        else:
            st.error("🔴 서버에 연결할 수 없음")
            st.info("서버를 시작하려면: `langgraph dev`")

        st.markdown("---")

        col1, col2 = st.columns([3, 1])
        with col1:
            if st.button("🔄 Assistant 목록 새로고침", disabled=not server_status):
                with st.spinner("Assistant 목록을 조회하는 중..."):
                    assistants = get_available_assistants()
                    st.session_state.available_assistants = assistants
                    if assistants:
                        st.success(f"{len(assistants)}개의 Assistant를 찾았습니다!")
                    else:
                        st.warning("사용 가능한 Assistant가 없습니다.")
        
        # 저장된 Assistant 목록이 비어있으면 자동으로 조회
        if not st.session_state.available_assistants and server_status:
            with st.spinner("Assistant 목록을 조회하는 중..."):
                assistants = get_available_assistants()
                st.session_state.available_assistants = assistants
        
        # Assistant 선택
        if st.session_state.available_assistants:
            assistant_names = list(st.session_state.available_assistants.keys())
            assistants = st.selectbox(
                "Assistant 조회:",
                assistant_names,
                index=0 if assistant_names else None,
                help="리뷰 분석에 사용할 Assistant를 선택하세요."
            )
            # 선택된 Assistant를 세션 상태에 저장
            st.session_state.selected_assistant = assistants

            # 선택된 Assistant의 정보 표시
            selected_info = st.session_state.available_assistants.get(assistants, {})
            st.markdown("**선택된 Assistant 정보:**")
            st.info(selected_info)
        else:
            st.warning("사용 가능한 Assistant가 없습니다.")
            st.session_state.selected_assistant = ""

    # 헤더
    st.title("⭐ BEST 리뷰 선정 & 제목/요약 생성 에이전트")
    st.markdown("---")

    # 초기 인사말
    if st.session_state.chat_state == ChatState.GREETING:
        st.session_state.messages = []
        add_message("assistant", "안녕하세요! BEST 리뷰를 선정하고 제목과 요약을 생성해드리는 AI 에이전트입니다. 어떤 타입의 BEST 리뷰를 찾고 계신가요?")
        st.session_state.chat_state = ChatState.SELECT_REVIEW_TYPE

    # 이전 메시지들 표시
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # 현재 상태에 따라 적절한 UI 렌더링
    if st.session_state.chat_state == ChatState.SELECT_REVIEW_TYPE:
        render_review_type_selection()
    elif st.session_state.chat_state == ChatState.CUSTOM_INPUT:
        render_custom_input()
    elif st.session_state.chat_state == ChatState.CONFIRM_SELECTION:
        with st.chat_message("assistant"):
            selected_text = "선택하신 리뷰 타입\n\n" + "\n\n".join([f"• {t}" for t in st.session_state.selected_types])
            st.markdown(selected_text)
            col1, col2 = st.columns([1, 1])
            with col1:
                if st.button("✅ 이 선택으로 진행"):
                    add_message("assistant", selected_text)
                    st.session_state.chat_state = ChatState.SHOW_CRITERIA
                    st.rerun()
            with col2:
                if st.button("❌ 다시 선택하기"):
                    st.session_state.chat_state = ChatState.SELECT_REVIEW_TYPE
                    st.rerun()
    elif st.session_state.chat_state == ChatState.SHOW_CRITERIA:
        render_criteria_generation()
    elif st.session_state.chat_state == ChatState.ASK_ADDITIONAL:
        render_additional_criteria()
    elif st.session_state.chat_state == ChatState.FINAL_CRITERIA:
        render_criteria()  # 추가 기준으로 재생성
    elif st.session_state.chat_state == ChatState.SELECTING_REVIEWS:
        with st.chat_message("assistant"):
            with st.spinner("🤖 AI가 리뷰들을 분석하고 BEST 후보들을 선정하고 있습니다..."):
                candidate_reviews = real_review_selection()
                st.session_state.candidate_reviews = candidate_reviews
                st.session_state.chat_state = ChatState.SHOW_CANDIDATE_REVIEWS
                st.rerun()
    elif st.session_state.chat_state == ChatState.SHOW_CANDIDATE_REVIEWS:
        render_candidate_reviews()
    elif st.session_state.chat_state == ChatState.NO_SELECTION_RETRY:
        with st.chat_message("assistant"):
            st.markdown("선택된 리뷰가 없습니다. 다시 선택해주세요.")
            if st.button("다시 선택하기"):
                st.session_state.chat_state = ChatState.SHOW_CANDIDATE_REVIEWS
                st.rerun()
    elif st.session_state.chat_state == ChatState.SELECT_TITLE_STYLE:
        render_title_style_selection()
    elif st.session_state.chat_state == ChatState.GENERATING_TITLES:
        render_title_generation()
    elif st.session_state.chat_state == ChatState.SHOW_GENERATED_TITLES:
        render_generated_titles()
    elif st.session_state.chat_state == ChatState.REGENERATING_TITLES:
        render_title_regeneration()
    elif st.session_state.chat_state == ChatState.SELECT_SUMMARY_REVIEWS:
        render_summary_review_selection()
    elif st.session_state.chat_state == ChatState.SELECT_SUMMARY_STYLE:
        render_summary_style_selection()
    elif st.session_state.chat_state == ChatState.GENERATING_SUMMARIES:
        render_summary_generation()
    elif st.session_state.chat_state == ChatState.SHOW_FINAL_RESULTS:
        render_final_results()
    elif st.session_state.chat_state == ChatState.SAVE_TO_DB:
        render_save_to_db()


if __name__ == "__main__":
    main()
