import os
import mysql.connector
from mysql.connector import Error
from dotenv import load_dotenv
from typing import List, Dict, Any, Optional, Tuple
from contextlib import contextmanager

# 환경변수 로드
load_dotenv()

# ------------------- MYSQL 접속 정보 설정 -------------------
# 환경변수에서 데이터베이스 설정을 불러옵니다.
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'user': os.getenv('DB_USER', 'root'),
    'password': os.getenv('DB_PASSWORD', ''),
    'database': os.getenv('DB_DATABASE', 'test'),
    'port': int(os.getenv('DB_PORT', '3306')),
    'autocommit': False,  # 명시적 트랜잭션 관리
    'charset': 'utf8mb4',  # 한글 지원
    'collation': 'utf8mb4_unicode_ci'
}


class DatabaseManager:
    """데이터베이스 연결 및 쿼리 실행을 관리하는 클래스"""

    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or DB_CONFIG

    @contextmanager
    def get_connection(self):
        """데이터베이스 연결을 관리하는 컨텍스트 매니저"""
        connection = None
        try:
            connection = mysql.connector.connect(**self.config)
            if not connection.is_connected():
                raise Error("데이터베이스에 연결할 수 없습니다.")
            yield connection
        except Error as e:
            if connection and connection.is_connected():
                connection.rollback()
            raise e
        finally:
            if connection and connection.is_connected():
                connection.close()

    def fetch_data(self, query: str, params: Tuple = ()) -> List[Dict[str, Any]]:
        """SELECT 쿼리를 실행하고 결과를 반환합니다."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor(dictionary=True)
                cursor.execute(query, params)
                data = cursor.fetchall()
                cursor.close()
                return data
        except Error as e:
            print(f"데이터 조회 중 오류 발생: {e}")
            return []

    def execute_query(self, query: str, params: Tuple = ()) -> int:
        """INSERT, UPDATE, DELETE 쿼리를 실행하고 영향받은 행 수를 반환합니다."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, params)
                affected_rows = cursor.rowcount
                conn.commit()
                cursor.close()
                return affected_rows
        except Error as e:
            print(f"쿼리 실행 중 오류 발생: {e}")
            raise e

    def execute_many(self, query: str, data_list: List[Tuple]) -> int:
        """여러 개의 동일한 쿼리를 배치로 실행합니다."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.executemany(query, data_list)
                affected_rows = cursor.rowcount
                conn.commit()
                cursor.close()
                return affected_rows
        except Error as e:
            print(f"배치 쿼리 실행 중 오류 발생: {e}")
            raise e

    @contextmanager
    def transaction(self):
        """트랜잭션을 관리하는 컨텍스트 매니저"""
        with self.get_connection() as conn:
            cursor = conn.cursor(dictionary=True)
            try:
                yield cursor
                conn.commit()
            except Exception as e:
                conn.rollback()
                raise e
            finally:
                cursor.close()


# 전역 데이터베이스 매니저 인스턴스
db_manager = DatabaseManager()


def fetch_data(query: str, params: tuple = ()) -> dict:
    """기존 호환성을 위한 래퍼 함수"""
    data = db_manager.fetch_data(query, params)
    return {"data": data}
