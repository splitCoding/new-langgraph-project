import json

from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from src.review.models import models
from src.review.prompts import prompts
from src.review.state.state import State

llm_model = models['gpt_o_4_mini']


def check_summary_quality_node(state: State) -> dict:
    """요약 품질을 검증하는 노드"""
    print("\n--- 요약 품질 검사 시작 ---")

    # 상태에서 필요한 데이터 가져오기
    summaries = state.get("results", [])
    aggregated_best_reviews = state.get("aggregated_best_reviews", [])

    if len(summaries) == 0:
        print("검증할 요약이 없습니다.")
        return {"quality_check_passed": True, "validation_results": []}

    # 원본 리뷰 텍스트 준비
    original_reviews_text = ""
    for review in aggregated_best_reviews:
        original_reviews_text += f"ID: {review.get('id', 'N/A')}\n"
        original_reviews_text += f"내용: {review.get('text', 'N/A')}\n\n"

    # 생성된 요약 JSON 준비 - ReviewSummary 구조에 맞게 수정
    summaries_for_validation = []
    for summary in summaries:
        if isinstance(summary, dict) and 'id' in summary and 'results' in summary:
            # ReviewSummary 구조의 경우
            for result in summary['results']:
                summaries_for_validation.append({
                    "id": summary['id'],
                    "title": result.get('title', ''),
                    "summary": result.get('summary', '')
                })

    generated_summaries_json = json.dumps({"summaries": summaries_for_validation}, ensure_ascii=False, indent=2)

    # 검증 프롬프트 포맷팅
    print("LLM을 통한 요약 품질 검증 중...")

    try:
        # LLM 호출 - JSON 응답만 받도록 간단히 처리
        prompt_template = ChatPromptTemplate.from_messages([
            ("system", prompts["summary_validate"].system),
            ("user", prompts["summary_validate"].user)
        ])

        model_kwargs = {"model": llm_model.name}
        if llm_model.temperature is not None:
            model_kwargs["temperature"] = llm_model.temperature
        model = ChatOpenAI(**model_kwargs)

        chain = prompt_template | model
        print(f"original_reviews_text: {original_reviews_text}")
        print(f"generated_summaries: {generated_summaries_json}")
        response = chain.invoke({
            "original_reviews": original_reviews_text,
            "generated_summaries": generated_summaries_json
        })
        response_content = response.content
        print(f"검증 완료 - {response_content}")

        # JSON 응답 파싱
        validation_result = json.loads(response_content)

        # 검증 결과 출력
        overall_pass = validation_result.get("overall_pass", False)
        total_valid = validation_result.get("total_valid", 0)
        total_invalid = validation_result.get("total_invalid", 0)

        print(f"검증 완료 - 전체 통과: {overall_pass}")
        print(f"유효한 요약: {total_valid}개, 무효한 요약: {total_invalid}개")

        # 문제가 있는 요약들에 대한 상세 정보 출력
        validation_results = validation_result.get("validation_results", [])
        for result in validation_results:
            if not result.get("is_valid", True):
                review_id = result.get("id", "N/A")
                title_issues = result.get("title_issues", [])
                summary_issues = result.get("summary_issues", [])
                print(f"ID {review_id} 문제점:")

                # title_issues 처리 - 새로운 형식과 기존 형식 모두 지원
                if title_issues:
                    if isinstance(title_issues[0], dict):
                        # 새로운 형식: 객체 배열
                        for issue in title_issues:
                            print(f"  제목: {issue.get('reason', '문제 있음')}")
                    else:
                        # 기존 형식: 문자열 배열
                        print(f"  제목: {', '.join(title_issues)}")

                # summary_issues 처리 - 새로운 형식과 기존 형식 모두 지원
                if summary_issues:
                    if isinstance(summary_issues[0], dict):
                        # 새로운 형식: 객체 배열
                        for issue in summary_issues:
                            print(f"  요약: {issue.get('reason', '문제 있음')}")
                    else:
                        # 기존 형식: 문자열 배열
                        print(f"  요약: {', '.join(summary_issues)}")

        # 수정된 제목, 요약을 results 에 반영
        updated_summaries = []
        print(f"검증 결과 개수: {len(validation_results)}")
        print(f"원본 요약 개수: {len(summaries)}")
        
        for summary in summaries:
            if isinstance(summary, dict) and 'id' in summary and 'results' in summary:
                updated_summary = {
                    "id": summary['id'],
                    "results": []
                }
                
                print(f"처리 중인 요약 ID: {summary['id']}")
                
                # 해당 ID의 모든 검증 결과 찾기
                validation_results_for_id = [vr for vr in validation_results if vr.get("id") == summary['id']]
                
                if validation_results_for_id:
                    print(f"ID {summary['id']}에 대한 검증 결과 {len(validation_results_for_id)}개 발견")
                else:
                    print(f"ID {summary['id']}에 대한 검증 결과 없음")
                
                # 각 결과에 대해 수정사항 적용
                for result_idx, result in enumerate(summary['results']):
                    updated_result = result.copy()
                    print(f"  결과 {result_idx}: 제목='{result.get('title')}', 요약='{result.get('summary')}'")
                    
                    # 모든 검증 결과를 확인해서 현재 결과와 매칭되는 것 찾기
                    result_modified = False
                    for validation_result in validation_results_for_id:
                        if not validation_result.get("is_valid", True):
                            print(f"    검증 결과 확인 중...")
                            
                            # title_issues에서 현재 제목과 일치하는 개선 제안 찾기
                            title_issues = validation_result.get("title_issues", [])
                            for title_issue in title_issues:
                                if isinstance(title_issue, dict):
                                    original_title = title_issue.get("title", "")
                                    suggestion = title_issue.get("suggestion", "")
                                    reason = title_issue.get("reason", "")
                                    
                                    # 원본 제목과 일치하는 경우에만 수정
                                    if original_title == result.get('title') and suggestion:
                                        updated_result["title"] = suggestion
                                        print(f"    제목 수정: {original_title} → {suggestion}")
                                        print(f"    사유: {reason}")
                                        result_modified = True
                                        break
                            
                            # summary_issues에서 현재 요약과 일치하는 개선 제안 찾기
                            summary_issues = validation_result.get("summary_issues", [])
                            for summary_issue in summary_issues:
                                if isinstance(summary_issue, dict):
                                    original_summary = summary_issue.get("summary", "")
                                    suggestion = summary_issue.get("suggestion", "")
                                    reason = summary_issue.get("reason", "")
                                    
                                    # 원본 요약과 일치하는 경우에만 수정
                                    if original_summary == result.get('summary') and suggestion:
                                        updated_result["summary"] = suggestion
                                        print(f"    요약 수정: {original_summary} → {suggestion}")
                                        print(f"    사유: {reason}")
                                        result_modified = True
                                        break
                            
                            # 현재 결과가 수정되었으면 더 이상 다른 검증 결과 확인하지 않음
                            if result_modified:
                                break
                    
                    if not result_modified:
                        print(f"    수정사항 없음")
                    
                    updated_summary["results"].append(updated_result)
                
                updated_summaries.append(updated_summary)
            else:
                # ReviewSummary 구조가 아닌 경우 그대로 유지
                print(f"ReviewSummary 구조가 아닌 요약: {summary}")
                updated_summaries.append(summary)

        print(f"수정된 요약 개수: {updated_summaries}")
        return {
            # "quality_check_passed": overall_pass,
            # "validation_results": validation_results,
            # "quality_summary": {
            #     "total_valid": total_valid,
            #     "total_invalid": total_invalid,
            #     "overall_pass": overall_pass
            # },
            "results": updated_summaries  # 수정된 요약들을 반환
        }

    except json.JSONDecodeError as e:
        print(f"LLM 응답 JSON 파싱 오류: {e}")
        return {}

    except Exception as e:
        print(f"요약 품질 검증 오류: {e}")
        return {}


__all__ = ["check_summary_quality_node"]
