"""
리뷰 분석 노드들을 제공하는 패키지

이 패키지에는 다음과 같은 노드들이 포함되어 있습니다:
- fetch_reviews: 리뷰 데이터 수집
- get_candidates: 후보 선택 로직  
- aggregate_best: 최적 결과 집계
- re_rank: 재순위 매기기
- generate: 요약/이미지 생성
- update_reviews: DB 업데이트
"""

# 주요 노드 함수들을 패키지 레벨에서 import 가능하게 함
from .review_fetch import fetch_reviews_node
from .best_review_candidates import (
    use_llm_node,
    llm1_select,
    llm2_select,
    llm3_select,
    check_review_exist
)
from .best_review_selection import aggregate_best_node, check_inventory_node
from .best_review_candidate_re_rank import rerank_node
from .best_review_summary import generate_summary_node, generate_image_node
from .review_update import update_db_node
from .summary_quality_check import check_summary_quality_node

# 공개 API 정의
__all__ = [
    # 리뷰 수집
    "fetch_reviews_node",

    # 후보 선택
    "use_llm_node",
    "llm1_select",
    "llm2_select",
    "llm3_select",
    "check_review_exist",

    # 집계 및 재고
    "aggregate_best_node",
    "check_inventory_node",

    # 재순위 매기기
    "rerank_node",

    # 생성 작업
    "generate_summary_node",
    "generate_image_node",

    # DB 업데이트
    "update_db_node",

    # 요약 품질 검증
    "check_summary_quality_node"
]
