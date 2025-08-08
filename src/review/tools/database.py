"""Database query tool for review analysis."""

import os
import logging
from typing import List, Dict, Optional, Any
from dataclasses import dataclass
from dotenv import load_dotenv, find_dotenv
import mysql.connector
from mysql.connector import Error
from langchain_core.tools import tool

logger = logging.getLogger(__name__)


# .env 파일을 자동으로 찾아서 로드
dotenv_path = find_dotenv()
if dotenv_path:
    load_dotenv(dotenv_path=dotenv_path)
    logger.info(f"Loaded .env from: {dotenv_path}")
else:
    logger.warning("Could not find .env file")


@dataclass
class DatabaseConfig:
    """Database configuration."""
    host: str
    port: int
    database: str
    username: str
    password: str
    charset: str = "utf8mb4"
    
    @classmethod
    def from_env(cls) -> "DatabaseConfig":
        """Create config from environment variables."""
        # 환경 변수 로딩 확인을 위한 디버깅
        db_host = os.getenv("DB_HOST", "localhost")
        db_port = int(os.getenv("DB_PORT", "3306"))
        db_name = os.getenv("DB_NAME", "reviews")
        db_user = os.getenv("DB_USER", "root")
        db_password = os.getenv("DB_PASSWORD", "")
        db_charset = os.getenv("DB_CHARSET", "utf8mb4")
        
        logger.info(f"DB Config - Host: {db_host}, Port: {db_port}, Database: {db_name}, User: {db_user}")
        
        return cls(
            host=db_host,
            port=db_port,
            database=db_name,
            username=db_user,
            password=db_password,
            charset=db_charset
        )


class DatabaseConnection:
    """MySQL database connection manager."""
    
    def __init__(self, config: DatabaseConfig):
        self.config = config
        self._connection = None
    
    def __enter__(self):
        """Context manager entry."""
        try:
            self._connection = mysql.connector.connect(
                host=self.config.host,
                port=self.config.port,
                database=self.config.database,
                user=self.config.username,
                password=self.config.password,
                charset=self.config.charset,
                autocommit=True
            )
            logger.info(f"Connected to MySQL database: {self.config.database}")
            return self._connection
        except Error as e:
            logger.error(f"Failed to connect to MySQL database: {e}")
            raise
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        if self._connection and self._connection.is_connected():
            self._connection.close()
            logger.info("MySQL database connection closed")


class ReviewDatabaseTool:
    """Tool for querying review data from MySQL database."""
    
    # Predefined queries for common operations
    PREDEFINED_QUERIES = {
        "get_recent_reviews": """
            SELECT 
                review.id, 
                review.text, 
                review.rating, 
                review.createdAt, 
                IF(review_content.id IS NULL, FALSE, TRUE) as image_exists
            FROM 
                select_shop_custom_review review
            JOIN 
                select_shop_custom_review_product review_product ON review.selectShopCustomReviewProductId = review_product.id
            LEFT JOIN 
                select_shop_custom_review_content review_content ON review.id = review_content.selectShopCustomReviewId
            WHERE review.mallId = %s 
              AND review.shopId = %s 
              AND display = TRUE
              AND isDeleted = FALSE
            ORDER BY review.createdAt DESC 
            LIMIT %s
        """,
        "get_high_rated_reviews": """
            SELECT 
                review.id, 
                review.text, 
                review.rating, 
                review.createdAt, 
                IF(review_content.id IS NULL, FALSE, TRUE) as image_exists
            FROM 
                select_shop_custom_review review
            JOIN 
                select_shop_custom_review_product review_product ON review.selectShopCustomReviewProductId = review_product.id
            LEFT JOIN 
                select_shop_custom_review_content review_content ON review.id = review_content.selectShopCustomReviewId
            WHERE review.mallId = %s 
              AND review.shopId = %s 
              AND review.rating >= %s
              AND display = TRUE
              AND isDeleted = FALSE
            ORDER BY review.createdAt DESC, review.rating DESC
        """,
        "get_reviews_with_images": """
            SELECT 
                review.id, 
                review.text, 
                review.rating, 
                review.createdAt, 
                IF(review_content.id IS NULL, FALSE, TRUE) as image_exists
            FROM 
                select_shop_custom_review review
            JOIN 
                select_shop_custom_review_product review_product ON review.selectShopCustomReviewProductId = review_product.id
            JOIN 
                select_shop_custom_review_content review_content ON review.id = review_content.selectShopCustomReviewId
            WHERE review.mallId = %s 
              AND review.shopId = %s 
              AND display = TRUE
              AND isDeleted = FALSE
            ORDER BY review.createdAt DESC, review.rating DESC
        """,
        "get_reviews_by_date_range": """
            SELECT 
                review.id, 
                review.text, 
                review.rating, 
                review.createdAt, 
                IF(review_content.id IS NULL, FALSE, TRUE) as image_exists
            FROM 
                select_shop_custom_review review
            JOIN 
                select_shop_custom_review_product review_product ON review.selectShopCustomReviewProductId = review_product.id
            LEFT JOIN 
                select_shop_custom_review_content review_content ON review.id = review_content.selectShopCustomReviewId
            WHERE review.mallId = %s 
              AND review.shopId = %s 
              AND review.createdAt BETWEEN %s AND %s
              AND display = TRUE
              AND isDeleted = FALSE
            ORDER BY review.createdAt DESC
        """,
        "count_reviews_by_rating": """
            SELECT review.rating, COUNT(*) as count
            FROM select_shop_custom_review review
            JOIN select_shop_custom_review_product review_product ON review.selectShopCustomReviewProductId = review_product.id
            WHERE review.mallId = %s 
              AND review.shopId = %s
              AND display = TRUE
              AND isDeleted = FALSE
            GROUP BY review.rating
            ORDER BY review.rating DESC
        """
    }
    
    def __init__(self, config: Optional[DatabaseConfig] = None):
        self.config = config or DatabaseConfig.from_env()
    
    def execute_predefined_query(self, query_name: str, params: tuple) -> List[Dict[str, Any]]:
        """Execute a predefined query."""
        if query_name not in self.PREDEFINED_QUERIES:
            available_queries = ", ".join(self.PREDEFINED_QUERIES.keys())
            raise ValueError(f"Unknown query: {query_name}. Available queries: {available_queries}")
        
        query = self.PREDEFINED_QUERIES[query_name]
        return self.execute_query(query, params)
    
    def execute_query(self, query: str, params: Optional[tuple] = None) -> List[Dict[str, Any]]:
        """Execute a custom SQL query."""
        try:
            with DatabaseConnection(self.config) as conn:
                cursor = conn.cursor(dictionary=True)
                cursor.execute(query, params or ())
                results = cursor.fetchall()
                cursor.close()
                
                logger.info(f"Query executed successfully, returned {len(results)} rows")
                return results
                
        except Error as e:
            logger.error(f"Database query failed: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error during query execution: {e}")
            raise
    
    def get_recent_reviews(self, mall_id: str, shop_id: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Get recent reviews for a shop."""
        return self.execute_predefined_query("get_recent_reviews", (mall_id, shop_id, limit))
    
    def get_high_rated_reviews(self, mall_id: str, shop_id: str, min_rating: int = 4) -> List[Dict[str, Any]]:
        """Get reviews with rating >= min_rating."""
        return self.execute_predefined_query("get_high_rated_reviews", (mall_id, shop_id, min_rating))
    
    def get_reviews_with_images(self, mall_id: str, shop_id: str) -> List[Dict[str, Any]]:
        """Get reviews that have images."""
        return self.execute_predefined_query("get_reviews_with_images", (mall_id, shop_id))


# LangGraph tool definitions
@tool
def query_reviews_by_rating(mall_id: str, shop_id: str, min_rating: int = 4, limit: int = 100) -> List[Dict[str, Any]]:
    """
    Query reviews by minimum rating from MySQL database.
    
    Args:
        mall_id: Mall identifier
        shop_id: Shop identifier  
        min_rating: Minimum rating (1-5)
        limit: Maximum number of reviews to return
        
    Returns:
        List of review dictionaries with id, text, rating, created_at, image_exists
    """
    try:
        db_tool = ReviewDatabaseTool()
        
        # Use custom query for rating with limit
        query = """
            SELECT 
                review.id, 
                review.text, 
                review.rating, 
                review.createdAt, 
                IF(review_content.id IS NULL, FALSE, TRUE) as image_exists
            FROM 
                select_shop_custom_review review
            JOIN 
                select_shop_custom_review_product review_product ON review.selectShopCustomReviewProductId = review_product.id
            LEFT JOIN 
                select_shop_custom_review_content review_content ON review.id = review_content.selectShopCustomReviewId
            WHERE review.mallId = %s
              AND review.shopId = %s
              AND review.rating >= %s
              AND display = TRUE
              AND isDeleted = FALSE
            ORDER BY review.createdAt DESC, review.rating DESC
            LIMIT %s
        """
        
        return db_tool.execute_query(query, (mall_id, shop_id, min_rating, limit))
    
    except Exception as e:
        logger.error(f"Failed to query reviews by rating: {e}")
        return []


@tool
def query_reviews_with_images(mall_id: str, shop_id: str, limit: int = 100) -> List[Dict[str, Any]]:
    """
    Query reviews that have images from MySQL database.
    
    Args:
        mall_id: Mall identifier
        shop_id: Shop identifier
        limit: Maximum number of reviews to return
        
    Returns:
        List of review dictionaries with id, text, rating, created_at, image_exists
    """
    try:
        db_tool = ReviewDatabaseTool()
        
        # Use custom query for reviews with images and limit
        query = """
            SELECT 
                review.id, 
                review.text, 
                review.rating, 
                review.createdAt, 
                IF(review_content.id IS NULL, FALSE, TRUE) as image_exists
            FROM 
                select_shop_custom_review review
            JOIN 
                select_shop_custom_review_product review_product ON review.selectShopCustomReviewProductId = review_product.id
            JOIN 
                select_shop_custom_review_content review_content ON review.id = review_content.selectShopCustomReviewId
            WHERE review.mallId = %s
              AND review.shopId = %s
              AND display = TRUE
              AND isDeleted = FALSE
            ORDER BY review.createdAt DESC, review.rating DESC
            LIMIT %s
        """

        return db_tool.execute_query(query, (mall_id, shop_id, limit))

    except Exception as e:
        logger.error(f"Failed to query reviews with images: {e}")
        return []


@tool
def query_reviews_custom(query: str, params: tuple = ()) -> List[Dict[str, Any]]:
    """
    Execute a custom SQL query on the reviews database.
    
    Args:
        query: SQL query string with placeholders (%s)
        params: Tuple of parameters to bind to the query
        
    Returns:
        List of dictionaries representing query results
    """
    try:
        db_tool = ReviewDatabaseTool()
        
        # Basic security check - only allow SELECT queries
        query_stripped = query.strip().upper()
        if not query_stripped.startswith('SELECT'):
            raise ValueError("Only SELECT queries are allowed")
        
        # Prevent dangerous operations
        dangerous_keywords = ['DROP', 'DELETE', 'INSERT', 'UPDATE', 'TRUNCATE', 'ALTER']
        if any(keyword in query_stripped for keyword in dangerous_keywords):
            raise ValueError(f"Query contains forbidden keywords: {dangerous_keywords}")
        
        return db_tool.execute_query(query, params)
    
    except Exception as e:
        logger.error(f"Failed to execute custom query: {e}")
        return []


@tool
def get_review_statistics(mall_id: str, shop_id: str) -> Dict[str, Any]:
    """
    Get review statistics for a shop.
    
    Args:
        mall_id: Mall identifier
        shop_id: Shop identifier
        
    Returns:
        Dictionary with review statistics
    """
    try:
        db_tool = ReviewDatabaseTool()
        
        # Get rating distribution
        rating_stats = db_tool.execute_predefined_query("count_reviews_by_rating", (mall_id, shop_id))
        
        # Get total count and average rating
        total_query = """
            SELECT 
                COUNT(*) as total_reviews,
                AVG(review.rating) as average_rating,
                MIN(review.createdAt) as first_review_date,
                MAX(review.createdAt) as last_review_date,
                COUNT(review_content.id) as reviews_with_images
            FROM 
                select_shop_custom_review review
            JOIN 
                select_shop_custom_review_product review_product ON review.selectShopCustomReviewProductId = review_product.id
            LEFT JOIN 
                select_shop_custom_review_content review_content ON review.id = review_content.selectShopCustomReviewId
            WHERE review.mallId = %s 
              AND review.shopId = %s
              AND display = TRUE
              AND isDeleted = FALSE
        """
        
        total_stats = db_tool.execute_query(total_query, (mall_id, shop_id))
        
        result = {
            "rating_distribution": rating_stats,
            "total_statistics": total_stats[0] if total_stats else {}
        }
        
        return result
    
    except Exception as e:
        logger.error(f"Failed to get review statistics: {e}")
        return {}