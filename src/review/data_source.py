import os
import mysql.connector
from mysql.connector import Error
from dotenv import load_dotenv

# 환경변수 로드
load_dotenv()

# ------------------- MYSQL 접속 정보 설정 -------------------
# 환경변수에서 데이터베이스 설정을 불러옵니다.
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'user': os.getenv('DB_USER', 'root'),
    'password': os.getenv('DB_PASSWORD', ''),
    'database': os.getenv('DB_DATABASE', 'test'),
    'port': int(os.getenv('DB_PORT', '3306'))
}


def fetch_review(query: str, params: tuple = ()) -> dict:
    data = []
    try:
        # 데이터베이스에 연결
        conn = mysql.connector.connect(**DB_CONFIG)
        if not conn.is_connected():
            raise Error("데이터베이스에 연결할 수 없습니다.")

        # 결과를 딕셔너리 형태로 받기 위해 dictionary=True 설정
        cursor = conn.cursor(dictionary=True)

        # 쿼리 실행
        cursor.execute(query, params)

        # 모든 결과 가져오기
        data = cursor.fetchall()
        # print(f"성공적으로 {len(reviews_data)}개의 리뷰를 가져왔습니다.")

    except Error as e:
        print(f"데이터베이스 연결 또는 쿼리 실행 중 오류 발생: {e}")
        # 오류 발생 시 빈 리스트를 반환하여 이후 노드에서 에러가 나지 않도록 처리
        data = []

    finally:
        # 연결 및 커서 닫기
        if 'conn' in locals() and conn.is_connected():
            cursor.close()
            conn.close()
            print("데이터베이스 연결을 닫았습니다.")

    return {"data": data}
