"""채팅 UI 컴포넌트."""

import streamlit as st
import time
from typing import Dict, List
import re
from bs4 import BeautifulSoup

from ..models import ChatState, REVIEW_TYPE_CRITERIA, CriteriaByReviewType, SESSION_STATE_DEFAULTS
from ..services import (
    invoke_review_preference_api, invoke_title_summary_api, 
    real_review_selection, format_criteria_text, format_criteria_list_text, save_best_reviews_to_db
)


def clean_html_text(text: str) -> str:
    """BeautifulSoup을 사용하여 HTML 태그를 안전하게 제거하고 텍스트를 읽기 쉽게 포맷팅합니다."""
    if not text:
        return ""
    
    try:
        # BeautifulSoup을 사용하여 HTML 파싱 및 태그 제거
        soup = BeautifulSoup(text, 'html.parser')
        
        # <br> 태그를 줄바꿈으로 변환 (태그 제거 전에)
        for br in soup.find_all('br'):
            br.replace_with('\n')
        
        # <p> 태그는 줄바꿈으로 변환
        for p in soup.find_all('p'):
            p.insert_after('\n')
        
        # <div> 태그도 줄바꿈으로 변환
        for div in soup.find_all('div'):
            div.insert_after('\n')
        
        # 모든 HTML 태그 제거하고 텍스트만 추출
        cleaned_text = soup.get_text(separator=' ', strip=True)
        
        # 연속된 공백을 하나로 줄이기
        cleaned_text = re.sub(r' +', ' ', cleaned_text)
        
        # 연속된 줄바꿈을 최대 2개로 제한
        cleaned_text = re.sub(r'\n\s*\n\s*\n+', '\n\n', cleaned_text)
        
        # 앞뒤 공백 제거
        return cleaned_text.strip()
        
    except Exception as e:
        # BeautifulSoup 파싱 실패 시 기본 정규식 방식으로 폴백
        try:
            # 기본 HTML 태그 제거
            cleaned_text = re.sub(r'<[^>]+>', ' ', text)
            
            # HTML 엔티티 정규화
            cleaned_text = cleaned_text.replace('&nbsp;', ' ')
            cleaned_text = cleaned_text.replace('&lt;', '<')
            cleaned_text = cleaned_text.replace('&gt;', '>')
            cleaned_text = cleaned_text.replace('&amp;', '&')
            cleaned_text = cleaned_text.replace('&#39;', "'")
            cleaned_text = cleaned_text.replace('&quot;', '"')
            
            # 연속된 공백을 하나로 줄이기
            cleaned_text = re.sub(r'\s+', ' ', cleaned_text)
            
            return cleaned_text.strip()
        except Exception:
            # 모든 방법이 실패하면 원본 텍스트 반환
            return text


def format_review_text(text: str, max_length: int = 300) -> str:
    """리뷰 텍스트를 안전하게 포맷팅하고 길이를 제한합니다."""
    if not text:
        return ""
    
    # BeautifulSoup을 사용하여 HTML 클리닝
    cleaned_text = clean_html_text(text)
    
    # 텍스트가 너무 길면 단어 경계에서 축약
    if len(cleaned_text) > max_length:
        # 단어 경계에서 자르기
        truncated = cleaned_text[:max_length]
        last_space = truncated.rfind(' ')
        if last_space > max_length * 0.8:  # 80% 이상 지점에 공백이 있으면 그곳에서 자름
            cleaned_text = truncated[:last_space] + "..."
        else:
            cleaned_text = truncated + "..."
    
    return cleaned_text


def add_message(role: str, content: str):
    """메시지를 채팅에 추가."""
    st.session_state.messages.append({"role": role, "content": content})


def show_loading(message: str):
    """로딩 메시지 표시."""
    with st.spinner(message):
        time.sleep(1)


def render_review_type_selection():
    """리뷰 타입 선택 UI."""
    with st.chat_message("assistant"):
        st.markdown("다음 중에서 원하는 타입을 선택해주세요 (다중 선택 가능):")

        # 폼을 사용하여 상태 관리 개선
        with st.form("review_type_selection"):
            col1, col2 = st.columns(2)

            with col1:
                photo_review = st.checkbox("📷 포토 리뷰", key="photo_review_cb")
                honest_review = st.checkbox("💬 솔직한 리뷰", key="honest_review_cb")

            with col2:
                positive_review = st.checkbox("😊 긍정적인 리뷰", key="positive_review_cb")
                experience_review = st.checkbox("👍 사용경험에 대한 내용이 포함된 리뷰", key="experience_review_cb")

            custom_input = st.checkbox("✏️ 직접 입력할게요", key="custom_input_cb")

            submitted = st.form_submit_button("선택 완료")

        if submitted:
            selected = []
            if photo_review:
                selected.append("포토 리뷰")
            if honest_review:
                selected.append("솔직한 리뷰")
            if positive_review:
                selected.append("긍정적인 리뷰")
            if experience_review:
                selected.append("사용경험에 대한 내용이 포함된 리뷰")

            st.session_state.selected_types = selected

            if custom_input:
                st.session_state.chat_state = ChatState.CUSTOM_INPUT
            else:
                st.session_state.chat_state = ChatState.CONFIRM_SELECTION
            st.rerun()


def render_custom_input():
    """커스텀 리뷰 타입 입력 UI."""
    with st.chat_message("assistant"):
        st.markdown("원하시는 BEST 리뷰 타입을 입력해주세요")

        custom_type = st.text_input("커스텀 리뷰 타입:")

        if st.button("입력 완료"):
            if custom_type.strip():
                st.session_state.custom_type = custom_type.strip()
                st.session_state.selected_types.append(custom_type.strip())
                st.session_state.chat_state = ChatState.CONFIRM_SELECTION
                st.rerun()


def render_criteria_generation():
    """기준 생성 UI."""
    with st.chat_message("assistant"):
        with st.spinner("🤖 AI가 리뷰 타입별 고려 항목을 분석하고 있습니다..."):
            # LLM API 호출
            result = invoke_review_preference_api(
                selected_types=st.session_state.selected_types,
                additional_criteria=st.session_state.additional_criteria
            )
            criteria_text = ""
            if "error" in result:
                st.error(f"기준 생성 실패: {result['error']}")
                # 폴백: 기본 기준 사용
                criteria_dict = {}
                for selected_type in st.session_state.selected_types:
                    if selected_type in REVIEW_TYPE_CRITERIA:
                        criteria_dict[selected_type] = REVIEW_TYPE_CRITERIA[selected_type]
                    else:
                        criteria_dict[selected_type] = ["사용자 정의 기준"]
                
                criteria_text += format_criteria_text(criteria_dict)
            else:
                # LLM이 생성한 기준 사용
                criteria_by_type: list[CriteriaByReviewType] = result.get("criteria_by_type", [])
                st.session_state.criteria_by_type = criteria_by_type
                criteria_text += format_criteria_list_text(criteria_by_type)
            
            add_message("assistant", criteria_text)
            st.session_state.chat_state = ChatState.ASK_ADDITIONAL
            st.rerun()

def render_criteria():
    """기준 생성 UI."""
    with st.chat_message("assistant"):
        criteria_text = ""
        criteria_by_type: list[CriteriaByReviewType] = st.session_state.get("criteria_by_type", [])
        st.session_state.criteria_by_type = criteria_by_type
        criteria_text += format_criteria_list_text(criteria_by_type)
        add_message("assistant", criteria_text)
        st.session_state.chat_state = ChatState.ASK_ADDITIONAL
        st.rerun()


def render_additional_criteria():
    """추가 기준 입력 UI."""
    with st.chat_message("assistant"):
        st.markdown("추가적으로 고려되어야 하는 항목이 있을까요?")

        additional_criteria = st.text_area("추가 항목 (줄바꿈으로 구분):")

        col1, col2 = st.columns(2)
        with col1:
            if st.button("없음"):
                st.session_state.chat_state = ChatState.SELECTING_REVIEWS
                st.rerun()
        with col2:
            if st.button("추가 항목 적용"):
                if additional_criteria.strip():
                    additional_criteria_list = [
                        item.strip() for item in additional_criteria.split('\n')
                        if item.strip()
                    ]
                    st.session_state.additional_criteria = additional_criteria_list
                    # 추가 기준을 줄바꿈으로 나눠서 criteria_by_type에 바로 넣음
                    st.session_state.criteria_by_type.extend([
                        { "type" : item.strip(), "criteria": [] }for item in additional_criteria_list
                    ])
                    # print("추가 기준:", st.session_state.criteria_by_type)
                    st.session_state.chat_state = ChatState.FINAL_CRITERIA
                else:
                    st.session_state.chat_state = ChatState.SELECTING_REVIEWS
                st.rerun()


def render_candidate_reviews():
    """후보 리뷰 선택 UI."""
    with st.chat_message("assistant"):
        st.markdown("선정된 BEST 리뷰 후보들을 보여드립니다. 이 중 맘에 드는 리뷰를 선택해주세요")

        selected_review_ids = []

        for review_data in st.session_state.candidate_reviews:
            review = review_data['review']
            avg_score = review_data.get('avg_score', 0)
            
            with st.expander(f"리뷰 {review['id']} (평균 점수: {avg_score:.1f})", expanded=True):
                st.write(f"⭐ 평점: {review['rating']}/5")
                if review['image_exists']:
                    st.write("📷 이미지 포함")
                
                # HTML 태그 제거 및 포맷팅된 텍스트 표시
                formatted_text = format_review_text(review['text'])
                st.write(f"**내용:**")
                st.text_area(
                    label="리뷰 내용",
                    value=formatted_text,
                    height=100,
                    disabled=True,
                    key=f"review_text_{review['id']}",
                    label_visibility="collapsed"
                )

                if st.checkbox(f"이 리뷰 선택", key=f"select_{review['id']}"):
                    selected_review_ids.append(review['id'])

        col1, col2 = st.columns(2)
        with col1:
            if st.button("선택 완료"):
                if selected_review_ids:
                    # 선택된 리뷰들을 저장
                    st.session_state.selected_reviews = [
                        review_data['review'] for review_data in st.session_state.candidate_reviews
                        if review_data['review']['id'] in selected_review_ids
                    ]
                    st.session_state.chat_state = ChatState.SELECT_TITLE_STYLE
                else:
                    st.session_state.chat_state = ChatState.NO_SELECTION_RETRY
                st.rerun()

        with col2:
            if st.button("다른 리뷰 보기"):
                add_message("assistant", "BEST 리뷰를 재선정하겠습니다.")
                st.session_state.chat_state = ChatState.SELECTING_REVIEWS
                st.rerun()


def render_title_style_selection():
    """제목 스타일 선택 UI."""
    with st.chat_message("assistant"):
        st.markdown("선택하신 리뷰들의 제목을 생성하겠습니다. 원하는 제목 스타일을 선택해주세요:")
        
        with st.form("title_style_selection"):
            title_style = st.radio(
                "제목 스타일 선택:",
                ["간결한", "창의적인", "전문적인", "감정적인", "설명적인"]
            )
            
            # 사용자 정의 요구사항 입력
            st.markdown("### 📝 추가 요구사항 (선택사항)")
            custom_requirements = st.text_area(
                "제목 생성 시 반영하고 싶은 추가 요구사항이 있다면 적어주세요:",
                placeholder="예: 제품명을 포함해주세요, 긍정적인 톤으로 작성해주세요, 특정 키워드를 강조해주세요 등",
                height=80,
                key="title_custom_requirements_style"  # 이 key와
            )
            
            submitted = st.form_submit_button("제목 생성 시작")
            
            if submitted:
                st.session_state.title_style = title_style
                st.session_state.title_custom_requirements = custom_requirements.strip() if custom_requirements else ""
                st.session_state.chat_state = ChatState.GENERATING_TITLES
                st.rerun()


def render_title_generation():
    """제목 생성 UI."""
    with st.chat_message("assistant"):
        with st.spinner("🤖 AI가 선택된 리뷰들의 제목을 생성하고 있습니다..."):
            # 제목 생성 API 호출
            result = invoke_title_summary_api(
                selected_reviews=st.session_state.selected_reviews,
                summary_required_reviews=[],
                title_style=st.session_state.title_style,
                summary_style="",
                title_custom_requirements=st.session_state.get('title_custom_requirements', '')
            )
            
            if "error" in result:
                st.error(f"제목 생성 실패: {result['error']}")
                # 폴백: 기본 제목 생성
                st.session_state.final_titles = [
                    {"review_id": review["id"], "title": f"BEST 리뷰 {review['id']}"}
                    for review in st.session_state.selected_reviews
                ]
            else:
                final_results = result.get("final_results", {})
                st.session_state.final_titles = final_results.get("titles", [])
            
            st.session_state.chat_state = ChatState.SHOW_GENERATED_TITLES
            st.rerun()


def render_generated_titles():
    """생성된 제목 표시 UI."""
    with st.chat_message("assistant"):
        st.markdown("## 📝 생성된 제목들")
        
        # 재생성할 제목 선택을 위한 체크박스
        regenerate_titles = []
        
        for i, title_data in enumerate(st.session_state.final_titles):
            review_id = title_data["review_id"]
            title = title_data["title"]
            original_review = next((r for r in st.session_state.selected_reviews if r["id"] == review_id), None)
            
            if original_review:
                with st.expander(f"리뷰 {review_id}: {title}", expanded=True):
                    col1, col2 = st.columns([4, 1])
                    with col1:
                        st.write(f"**생성된 제목:** {title}")
                    with col2:
                        # 재생성 선택 체크박스
                        regenerate_selected = st.checkbox(
                            "재생성", 
                            key=f"regenerate_title_{review_id}",
                            help="이 제목을 다시 생성하려면 체크하세요"
                        )
                        if regenerate_selected:
                            regenerate_titles.append(title_data)
                    
                    st.write(f"**원본 리뷰:**")
                    formatted_text = format_review_text(original_review['text'], max_length=500)
                    st.text_area(
                        label="원본 리뷰 내용",
                        value=formatted_text,
                        height=80,
                        disabled=True,
                        key=f"generated_title_review_{review_id}",
                        label_visibility="collapsed"
                    )
        
        # 재생성 선택이 있는 경우 재생성 UI 표시
        if regenerate_titles:
            st.markdown("---")
            st.markdown("### 🔄 선택된 제목 재생성")
            st.info(f"{len(regenerate_titles)}개의 제목을 재생성하시겠습니까?")
            
            with st.form("title_regeneration_form"):
                regenerate_requirements = st.text_area(
                    "재생성 시 반영할 추가 요구사항:",
                    placeholder="예: 더 짧게 만들어주세요, 특정 키워드를 포함해주세요, 다른 톤으로 작성해주세요 등",
                    height=80,
                    key="title_regenerate_requirements"
                )
                
                regenerate_submitted = st.form_submit_button("선택된 제목 재생성")
                
                if regenerate_submitted:
                    # 재생성할 제목들의 리뷰 정보 저장
                    st.session_state.regenerate_titles = regenerate_titles
                    st.session_state.regenerate_requirements = regenerate_requirements.strip()
                    st.session_state.chat_state = ChatState.REGENERATING_TITLES
                    st.rerun()
        
        st.markdown("---")
        st.markdown("요약도 생성하고 싶은 리뷰가 있나요?")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("요약도 생성하기"):
                st.session_state.chat_state = ChatState.SELECT_SUMMARY_REVIEWS
                st.rerun()
        with col2:
            if st.button("완료"):
                st.session_state.chat_state = ChatState.SHOW_FINAL_RESULTS
                st.rerun()


def render_summary_review_selection():
    """요약할 리뷰 선택 UI."""
    with st.chat_message("assistant"):
        st.markdown("요약을 생성할 리뷰들을 선택해주세요:")
        
        selected_for_summary = []
        
        for title_data in st.session_state.final_titles:
            review_id = title_data["review_id"]
            title = title_data["title"]
            original_review = next((r for r in st.session_state.selected_reviews if r["id"] == review_id), None)
            
            if original_review:
                if st.checkbox(f"리뷰 {review_id}: {title}", key=f"summary_{review_id}"):
                    selected_for_summary.append(original_review)
        
        if st.button("선택 완료"):
            st.session_state.summary_required_reviews = selected_for_summary
            if selected_for_summary:
                st.session_state.chat_state = ChatState.SELECT_SUMMARY_STYLE
            else:
                st.session_state.chat_state = ChatState.SHOW_FINAL_RESULTS
            st.rerun()


def render_summary_style_selection():
    """요약 스타일 선택 UI."""
    with st.chat_message("assistant"):
        st.markdown("요약 스타일을 선택해주세요:")
        
        with st.form("summary_style_selection"):
            summary_style = st.radio(
                "요약 스타일 선택:",
                ["상세한", "간단한", "감정 중심", "기능 중심", "구매 결정 도움"]
            )
            
            submitted = st.form_submit_button("스타일 선택 완료")
            
            if submitted:
                st.session_state.summary_style = summary_style
                st.session_state.chat_state = ChatState.GENERATING_SUMMARIES
                st.rerun()


def render_summary_generation():
    """요약 생성 UI."""
    with st.chat_message("assistant"):
        with st.spinner("🤖 AI가 선택된 리뷰들의 요약을 생성하고 있습니다..."):
            # 요약 생성 API 호출
            result = invoke_title_summary_api(
                selected_reviews=st.session_state.selected_reviews,
                summary_required_reviews=st.session_state.summary_required_reviews,
                title_style=st.session_state.title_style,
                summary_style=st.session_state.summary_style
            )
            
            if "error" in result:
                st.error(f"요약 생성 실패: {result['error']}")
                # 폴백: 기본 요약 생성
                st.session_state.final_summaries = [
                    {"review_id": review["id"], "summary": f"리뷰 {review['id']}의 요약"}
                    for review in st.session_state.summary_required_reviews
                ]
            else:
                final_results = result.get("final_results", {})
                st.session_state.final_summaries = final_results.get("summaries", [])
            
            st.session_state.chat_state = ChatState.SHOW_FINAL_RESULTS
            st.rerun()


def render_final_results():
    """최종 결과 표시 UI."""
    with st.chat_message("assistant"):
        st.markdown("## 🎉 최종 결과")
        
        for title_data in st.session_state.final_titles:
            review_id = title_data["review_id"]
            title = title_data["title"]
            original_review = next((r for r in st.session_state.selected_reviews if r["id"] == review_id), None)
            summary_data = next((s for s in st.session_state.final_summaries if s["review_id"] == review_id), None)
            
            if original_review:
                with st.expander(f"⭐ BEST 리뷰 {review_id}: {title}", expanded=True):
                    st.write(f"**📝 제목:** {title}")
                    if summary_data:
                        st.write(f"**📄 요약:** {summary_data['summary']}")
                    
                    st.write(f"**💬 원본 리뷰:**")
                    formatted_text = format_review_text(original_review['text'], max_length=500)
                    st.text_area(
                        label="최종 리뷰 내용",
                        value=formatted_text,
                        height=120,
                        disabled=True,
                        key=f"final_review_{review_id}",
                        label_visibility="collapsed"
                    )
                    
                    st.write(f"**⭐ 평점:** {original_review['rating']}/5")
                    if original_review['image_exists']:
                        st.write("**📷 이미지:** 포함")
                    
                    # 후보 리뷰에서 점수 정보 찾기
                    candidate_data = next((c for c in st.session_state.candidate_reviews if c['review']['id'] == review_id), None)
                    if candidate_data:
                        st.write(f"**📊 측정 점수:** {candidate_data.get('avg_score', 0):.1f}")

        st.success("🎉 BEST 리뷰 제목/요약 생성이 완료되었습니다!")
        
        # DB 저장 버튼
        if st.button("💾 DB에 저장하기", type="primary"):
            st.session_state.chat_state = ChatState.SAVE_TO_DB
            st.rerun()


def render_title_regeneration():
    """선택된 제목 재생성 UI."""
    with st.chat_message("assistant"):
        regenerate_titles = st.session_state.get('regenerate_titles', [])
        regenerate_requirements = st.session_state.get('regenerate_requirements', '')
        
        st.markdown(f"## 🔄 제목 재생성 중...")
        st.info(f"{len(regenerate_titles)}개의 제목을 재생성하고 있습니다.")
        
        if regenerate_requirements:
            st.markdown(f"**추가 요구사항:** {regenerate_requirements}")
        
        with st.spinner("🤖 AI가 선택된 제목들을 재생성하고 있습니다..."):
            # 재생성할 리뷰들 추출
            regenerate_reviews = []
            for title_data in regenerate_titles:
                review_id = title_data["review_id"]
                original_review = next((r for r in st.session_state.selected_reviews if r["id"] == review_id), None)
                if original_review:
                    regenerate_reviews.append(original_review)
            
            # 제목 재생성 API 호출
            result = invoke_title_summary_api(
                selected_reviews=regenerate_reviews,
                summary_required_reviews=[],
                title_style=st.session_state.title_style,
                summary_style="",
                title_custom_requirements=st.session_state.get('title_custom_requirements', ''),
                regenerate_requirements=regenerate_requirements
            )
            
            if "error" in result:
                st.error(f"제목 재생성 실패: {result['error']}")
                # 실패 시 원래 상태로 돌아감
                st.session_state.chat_state = ChatState.SHOW_GENERATED_TITLES
                st.rerun()
            else:
                # 재생성된 제목으로 기존 제목들 업데이트
                final_results = result.get("final_results", {})
                regenerated_titles = final_results.get("titles", [])
                
                # 기존 final_titles에서 재생성된 제목들 업데이트
                updated_final_titles = []
                for existing_title_data in st.session_state.final_titles:
                    review_id = existing_title_data["review_id"]
                    # 재생성된 제목 중에서 해당 review_id 찾기
                    regenerated_title_data = next(
                        (t for t in regenerated_titles if t["review_id"] == review_id), 
                        None
                    )
                    
                    if regenerated_title_data:
                        # 재생성된 제목으로 교체
                        updated_final_titles.append(regenerated_title_data)
                    else:
                        # 기존 제목 유지
                        updated_final_titles.append(existing_title_data)
                
                st.session_state.final_titles = updated_final_titles
                
                # 재생성 관련 세션 상태 정리
                if 'regenerate_titles' in st.session_state:
                    del st.session_state.regenerate_titles
                if 'regenerate_requirements' in st.session_state:
                    del st.session_state.regenerate_requirements
                
                st.session_state.chat_state = ChatState.SHOW_GENERATED_TITLES
                st.rerun()


def render_save_to_db():
    """DB 저장 UI."""
    with st.chat_message("assistant"):
        with st.spinner("💾 BEST 리뷰 정보를 DB에 저장하고 있습니다..."):
            try:
                # 실제 DB 저장 호출
                success = save_best_reviews_to_db(
                    mall_id=st.session_state.get("mall_id", ""),
                    shop_id=st.session_state.get("shop_id", ""),
                    selected_reviews=st.session_state.get("selected_reviews", []),
                    final_titles=st.session_state.get("final_titles", []),
                    final_summaries=st.session_state.get("final_summaries", []),
                    candidate_reviews=st.session_state.get("candidate_reviews", [])
                )
                
                if success:
                    st.success("✅ BEST 리뷰 정보가 성공적으로 저장되었습니다!")
                    
                    # 저장 완료 후 초기 상태로 리셋 옵션 제공
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button("🔄 새로운 분석 시작"):
                            for key, config in SESSION_STATE_DEFAULTS.items():
                                field_name = config["name"]
                                default_value = config["default_value"]
                                # 매장 정보는 유지
                                if field_name not in ["mall_id", "shop_id", "selected_store_name"]:
                                    st.session_state[field_name] = default_value
                            st.rerun()
                    with col2:
                        if st.button("📋 결과 다시 보기"):
                            st.session_state.chat_state = ChatState.SHOW_FINAL_RESULTS
                            st.rerun()
                else:
                    st.error("❌ 저장 중 오류가 발생했습니다.")
                    if st.button("🔙 돌아가기"):
                        st.session_state.chat_state = ChatState.SHOW_FINAL_RESULTS
                        st.rerun()
                    
            except Exception as e:
                st.error(f"❌ 저장 중 오류가 발생했습니다: {str(e)}")
                if st.button("🔙 돌아가기"):
                    st.session_state.chat_state = ChatState.SHOW_FINAL_RESULTS
                    st.rerun()
