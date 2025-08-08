"""LangGraph API 클라이언트."""

import json
import time
import requests
import streamlit as st
from typing import List, Dict, Any


# API Base URL
LANGGRAPH_API_BASE = "http://localhost:2024"


def create_thread_and_run(assistant_id: str, input_data: Dict[str, Any]) -> Dict[str, Any]:
    """Thread를 생성하고 run을 실행하는 공통 메서드"""
    try:
        # 스레드 생성
        thread_response = requests.post(
            f"{LANGGRAPH_API_BASE}/threads", 
            json={},
            timeout=10
        )
        
        if thread_response.status_code != 200:
            return {"error": f"스레드 생성 실패: {thread_response.status_code}", "thread_id": None, "run_id": None}
        
        thread_id = thread_response.json()["thread_id"]
        
        # 그래프 실행
        run_url = f"{LANGGRAPH_API_BASE}/threads/{thread_id}/runs"
        run_data = {
            "assistant_id": assistant_id,
            "input": input_data
        }
        
        run_response = requests.post(
            run_url, 
            json=run_data,
            timeout=30
        )
        
        if run_response.status_code != 200:
            return {"error": f"그래프 실행 실패: {run_response.status_code} - {run_response.text}", "thread_id": thread_id, "run_id": None}
        
        # run_id 추출
        run_result = run_response.json()
        run_id = run_result.get("run_id", "")
        if not run_id:
            return {"error": "그래프 실행 실패: run_id를 찾을 수 없습니다.", "thread_id": thread_id, "run_id": None}
        
        return {"thread_id": thread_id, "run_id": run_id, "error": None}
    
    except Exception as e:
        return {"error": f"Thread/Run 생성 중 오류: {str(e)}", "thread_id": None, "run_id": None}


def get_available_assistants() -> Dict[str, str]:
    """LangGraph 서버에서 사용 가능한 assistant들을 조회합니다.
    
    Returns:
        Dict[str, str]: assistant 이름을 key로 하고 ID를 value로 하는 딕셔너리
    """
    try:
        # LangGraph API 문서에 따른 올바른 assistant 조회 엔드포인트 사용
        response = requests.post(
            f"{LANGGRAPH_API_BASE}/assistants/search",
            json={
                "limit": 100,
                "offset": 0
            },
            timeout=10
        )
        
        if response.status_code == 200:
            assistants_data = response.json()
            assistants_dict = {}
            
            # print(f"Assistant 조회 응답: {assistants_data}")  # 디버깅용
            
            # assistants 데이터에서 정보 추출
            if isinstance(assistants_data, list):
                for assistant in assistants_data:
                    if isinstance(assistant, dict):
                        name = assistant.get("name", "Untitled")
                        assistant_id = assistant.get("assistant_id", "")
                        graph_id = assistant.get("graph_id", "")
                        
                        # 이름이 비어있으면 graph_id 사용
                        display_name = name if name and name != "Untitled" else graph_id
                        if display_name:
                            assistants_dict[display_name] = assistant_id
            
            if assistants_dict:
                return assistants_dict
        
        # API 호출이 실패하면 기본값 반환
        # print("Assistant 조회 실패, 기본값 사용")
        return {
            "리뷰 선정 Agent": "review_agent",
            "기준 생성 Agent": "preference_agent", 
            "제목/요약 Agent": "title_summary_agent"
        }
            
    except requests.exceptions.RequestException as e:
        # print(f"Assistant 조회 실패: {str(e)}")
        return {
            "리뷰 선정 Agent": "review_agent",
            "기준 생성 Agent": "preference_agent", 
            "제목/요약 Agent": "title_summary_agent"
        }
    except Exception as e:
        # print(f"예상치 못한 오류: {str(e)}")
        return {
            "리뷰 선정 Agent": "review_agent",
            "기준 생성 Agent": "preference_agent", 
            "제목/요약 Agent": "title_summary_agent"
        }


def check_langgraph_server_status() -> bool:
    """LangGraph 서버 상태를 확인합니다."""
    try:
        # API 문서에 따른 올바른 엔드포인트 사용
        response = requests.post(
            f"{LANGGRAPH_API_BASE}/assistants/search",
            json={"limit": 1},
            timeout=5
        )
        return response.status_code == 200
    except:
        return False


def invoke_review_preference_api(selected_types: List[str], additional_criteria: List[str] = None) -> Dict[str, Any]:
    """Review Preference API를 호출하여 리뷰 타입별 고려 항목을 생성합니다."""
    try:
        # preference 그래프에 해당하는 assistant ID 찾기
        assistant_id = None
        if hasattr(st.session_state, 'available_assistants'):
            for name, aid in st.session_state.available_assistants.items():
                if 'review_preference' == name.lower():
                    assistant_id = aid
                    break
        
        if not assistant_id:
            return {"error": "preference 그래프의 assistant를 찾을 수 없습니다."}
        
        # 입력 데이터 준비
        input_data = {
            "selected_review_types": selected_types,
            "additional_criteria": additional_criteria or []
        }
        
        # Thread와 Run 생성
        result = create_thread_and_run(assistant_id, input_data)
        if result["error"]:
            return {"error": result["error"]}
        
        thread_id = result["thread_id"]
        run_id = result["run_id"]

        # 그래프 실행 완료 대기
        run_status_url = f"{LANGGRAPH_API_BASE}/threads/{thread_id}/runs/{run_id}"
        max_retry = 6
        current_try = 0
        
        while current_try < max_retry:
            response = requests.get(run_status_url, timeout=30)
            if response.status_code == 200:
                status_data = response.json()
                status = status_data.get("status", "unknown")
                # print(f"기준 생성 상태 확인: {current_try + 1}/{max_retry}, status: {status}")
                
                if status == "success":
                    break
                elif status == "error":
                    return {"error": f"기준 생성 오류: {status_data.get('error', 'Unknown error')}"}
            
            if current_try < max_retry - 1:
                time.sleep(5)
            current_try += 1
        
        # 최종 상태 조회
        state_url = f"{LANGGRAPH_API_BASE}/threads/{thread_id}/state"
        state_response = requests.get(state_url, timeout=30)

        if state_response.status_code != 200:
            return {"error": f"상태 조회 실패: {state_response.status_code}"}

        state_data = state_response.json()
        values = state_data.get("values", {})
        criterias = values.get("criteria_by_type", [])
        
        return {
            "criteria_by_type": criterias,
        }
    
    except requests.exceptions.ConnectionError:
        return {"error": "서버에 연결할 수 없습니다. 'langgraph dev' 명령으로 서버를 시작하세요."}
    except requests.exceptions.Timeout:
        return {"error": "요청 시간이 초과되었습니다."}
    except Exception as e:
        return {"error": f"예상치 못한 오류: {str(e)}"}


def invoke_best_review_select_api(input_data: Dict[str, Any]) -> Dict[str, Any]:
    """LangGraph API를 호출합니다."""
    print("LangGraph API 호출:", input_data)
    try:
        # review 그래프의 assistant ID를 사용
        # 선택된 assistant가 있으면 해당 ID 사용, 없으면 기본값
        assistant_id = None
        for name, aid in st.session_state.get('available_assistants', {}).items():
            if 'review' == name.lower():
                assistant_id = aid
                break
        
        if not assistant_id:
            return {"error": "적절한 assistant를 찾을 수 없습니다."}

        # Thread와 Run 생성
        result = create_thread_and_run(assistant_id, input_data)
        if result["error"]:
            return {"error": result["error"]}
        
        thread_id = result["thread_id"]
        run_id = result["run_id"]

        # 그래프 실행 완료 대기
        run_status_url = f"{LANGGRAPH_API_BASE}/threads/{thread_id}/runs/{run_id}"
        max_retry = 6
        current_try = 0
        
        while current_try < max_retry:
            response = requests.get(run_status_url, timeout=30)
            if response.status_code == 200:
                status_data = response.json()
                status = status_data.get("status", "unknown")
                # print(f"그래프 실행 상태 확인: {current_try + 1}/{max_retry}, status: {status}")
                
                if status == "success":
                    break
                elif status == "error":
                    return {"error": f"그래프 실행 오류: {status_data.get('error', 'Unknown error')}"}
            
            if current_try < max_retry - 1:
                time.sleep(5)
            current_try += 1
        
        # 최종 상태 조회
        state_url = f"{LANGGRAPH_API_BASE}/threads/{thread_id}/state"
        state_response = requests.get(state_url, timeout=30)

        if state_response.status_code != 200:
            return {"error": f"상태 조회 실패: {state_response.status_code}"}

        return {"state": state_response.json()}
    
    except requests.exceptions.ConnectionError:
        return {"error": "서버에 연결할 수 없습니다. 'langgraph dev' 명령으로 서버를 시작하세요."}
    except requests.exceptions.Timeout:
        return {"error": "요청 시간이 초과되었습니다."}
    except Exception as e:
        return {"error": f"예상치 못한 오류: {str(e)}"}


def invoke_title_summary_api(selected_reviews: List[Dict], summary_required_reviews: List[Dict] = None, 
                            title_style: str = "간결한", summary_style: str = "상세한",
                            title_custom_requirements: str = "", regenerate_requirements: str = "") -> Dict[str, Any]:
    """Title Summary API를 호출하여 제목과 요약을 생성합니다."""
    try:
        # title_summary 그래프에 해당하는 assistant ID 찾기
        assistant_id = None
        if hasattr(st.session_state, 'available_assistants'):
            for name, aid in st.session_state.available_assistants.items():
                if 'title' in name.lower() or 'summary' in name.lower():
                    assistant_id = aid
                    break
        
        if not assistant_id:
            return {"error": "title_summary 그래프의 assistant를 찾을 수 없습니다."}
        
        # 입력 데이터 준비
        input_data = {
            "selected_reviews": selected_reviews,
            "summary_required_reviews": summary_required_reviews or [],
            "title_style": title_style,
            "summary_style": summary_style,
            "title_custom_requirements": title_custom_requirements,
            "regenerate_requirements": regenerate_requirements
        }
        
        # Thread와 Run 생성
        result = create_thread_and_run(assistant_id, input_data)
        if result["error"]:
            return {"error": result["error"]}
        
        thread_id = result["thread_id"]
        run_id = result["run_id"]

        # 그래프 실행 완료 대기
        run_status_url = f"{LANGGRAPH_API_BASE}/threads/{thread_id}/runs/{run_id}"
        max_retry = 6
        current_try = 0
        
        while current_try < max_retry:
            response = requests.get(run_status_url, timeout=30)
            if response.status_code == 200:
                status_data = response.json()
                status = status_data.get("status", "unknown")
                # print(f"제목/요약 생성 상태 확인: {current_try + 1}/{max_retry}, status: {status}")
                
                if status == "success":
                    break
                elif status == "error":
                    return {"error": f"제목/요약 생성 오류: {status_data.get('error', 'Unknown error')}"}
            
            if current_try < max_retry - 1:
                time.sleep(5)
            current_try += 1
        
        # 최종 상태 조회
        state_url = f"{LANGGRAPH_API_BASE}/threads/{thread_id}/state"
        state_response = requests.get(state_url, timeout=30)

        if state_response.status_code != 200:
            return {"error": f"상태 조회 실패: {state_response.status_code}"}

        state_data = state_response.json()
        values = state_data.get("values", {})
        
        return {
            "final_results": values.get("final_results", {}),
            "status": values.get("status", "완료")
        }
    
    except requests.exceptions.ConnectionError:
        return {"error": "서버에 연결할 수 없습니다. 'langgraph dev' 명령으로 서버를 시작하세요."}
    except requests.exceptions.Timeout:
        return {"error": "요청 시간이 초과되었습니다."}
    except Exception as e:
        return {"error": f"예상치 못한 오류: {str(e)}"}
