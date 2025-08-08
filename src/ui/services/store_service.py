"""매장 정보 관련 서비스."""

import streamlit as st
import logging
import os
from typing import List, Dict, Tuple, Optional, Any
from dotenv import load_dotenv, find_dotenv

# DB 관련 imports
from ...review.tools.database import DatabaseConfig, DatabaseConnection

# .env 파일을 자동으로 찾아서 로드
dotenv_path = find_dotenv()
if dotenv_path:
    load_dotenv(dotenv_path=dotenv_path)
else:
    # 폴백: 상대 경로로 시도
    load_dotenv()

# 로거 설정
logger = logging.getLogger(__name__)


def get_store_list() -> List[Dict[str, str]]:
    """매장 목록을 조회합니다.
    
    Returns:
        List[Dict[str, str]]: 매장 정보 리스트 (name, mall_id, shop_id)
    """
    try:
        # DB 설정 및 연결
        db_config = DatabaseConfig.from_env()
        
        with DatabaseConnection(db_config) as db:
            # 매장 목록 조회 쿼리 (mall_id, shop_id의 유니크한 조합)
            query = """
                SELECT DISTINCT
                    CONCAT(review.mallId, ' - ', review.shopId) as name,
                    review.mallId as mall_id,
                    review.shopId as shop_id
                FROM select_shop_custom_review review
                WHERE review.display = TRUE
                  AND review.isDeleted = FALSE
                ORDER BY review.mallId, review.shopId
                LIMIT 50
            """
            
            cursor = db.cursor(dictionary=True)
            cursor.execute(query)
            results = cursor.fetchall()
            
            # 결과를 원하는 형태로 변환
            stores = []
            for row in results:
                stores.append({
                    "name": row["name"],
                    "mall_id": row["mall_id"],
                    "shop_id": row["shop_id"]
                })
            
            logger.info(f"매장 목록 조회 완료: {len(stores)}개 매장")
            return stores
            
    except Exception as e:
        logger.error(f"매장 목록 조회 실패: {e}")
        # DB 조회 실패 시 샘플 데이터 반환
        return [
            {"name": "테스트 매장 1", "mall_id": "mall_001", "shop_id": "shop_001"},
            {"name": "테스트 매장 2", "mall_id": "mall_002", "shop_id": "shop_002"},
            {"name": "샘플 스토어", "mall_id": "sample_mall", "shop_id": "sample_shop"},
            {"name": "데모 매장", "mall_id": "demo_mall", "shop_id": "demo_shop"},
        ]


def get_store_by_name(store_name: str) -> Optional[Dict[str, str]]:
    """매장 이름으로 매장 정보를 조회합니다.
    
    Args:
        store_name: 매장 이름
        
    Returns:
        Optional[Dict[str, str]]: 매장 정보 (name, mall_id, shop_id) 또는 None
    """
    stores = get_store_list()
    for store in stores:
        if store["name"] == store_name:
            return store
    return None


def save_best_reviews_to_db(
    mall_id: str,
    shop_id: str,
    selected_reviews: List[Dict],
    final_titles: List[Dict],
    final_summaries: List[Dict],
    candidate_reviews: List[Dict]
) -> bool:
    """BEST 리뷰 정보를 DB에 저장합니다.
    
    Args:
        mall_id: 쇼핑몰 ID
        shop_id: 상점 ID
        selected_reviews: 선택된 리뷰 목록
        final_titles: 생성된 제목 목록
        final_summaries: 생성된 요약 목록
        candidate_reviews: 후보 리뷰 목록 (점수 정보 포함)
        
    Returns:
        bool: 저장 성공 여부
    """
    if not final_titles:
        logger.warning("저장할 BEST 리뷰 데이터가 없습니다.")
        return False

    try:
        # 저장할 데이터 구조 생성
        recommend_reviews = []
        for title_data in final_titles:
            review_id = title_data["review_id"]
            title = title_data["title"]
            
            # 해당 리뷰 찾기
            review = next((r for r in selected_reviews if r["id"] == review_id), None)
            if not review:
                logger.warning(f"리뷰 ID {review_id}에 해당하는 리뷰를 찾을 수 없습니다.")
                continue
                
            # 요약 찾기
            summary_data = next((s for s in final_summaries if s["review_id"] == review_id), None)
            summary = summary_data["summary"] if summary_data else ""
            
            recommend_review = {
                "id": review_id,
                "title": title,
                "summary": summary
            }
            recommend_reviews.append(recommend_review)

        if not recommend_reviews:
            logger.warning("유효한 추천 리뷰 데이터가 없습니다.")
            return False

        # 데이터 유효성 검증
        required_keys = {'id', 'title', 'summary'}
        for i, review in enumerate(recommend_reviews):
            missing_keys = required_keys - set(review.keys())
            if missing_keys:
                raise ValueError(f"인덱스 {i}의 데이터에 필수 키가 없습니다: {missing_keys}")

        # DB 설정 및 연결
        db_config = DatabaseConfig.from_env()
        
        with DatabaseConnection(db_config) as db:
            # INSERT 쿼리
            query = """
                INSERT INTO select_shop_recommend_custom_review
                    (reviewId, title, summary, display)
                VALUES (%s, %s, %s, %s)
            """

            # 딕셔너리를 튜플로 변환
            insert_data = [
                (review['id'], review['title'], review['summary'], True)
                for review in recommend_reviews
            ]

            # 배치 실행
            cursor = db.cursor()
            affected_rows = cursor.executemany(query, insert_data)
            db.commit()
            
            logger.info(f"추천 리뷰 삽입 완료: {cursor.rowcount}개 행 삽입")
            print(f"DB 저장 성공: {mall_id}, {shop_id} - {cursor.rowcount}개 BEST 리뷰 저장됨")
            
            return True
        
    except ValueError as e:
        logger.error(f"데이터 유효성 검증 실패: {e}")
        print(f"DB 저장 실패 (데이터 오류): {str(e)}")
        return False
    except Exception as e:
        logger.error(f"DB 저장 실패: {e}")
        print(f"DB 저장 오류: {str(e)}")
        return False
