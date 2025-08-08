"""UI 모델 패키지."""

from .types import (
    Review, Candidate, CriteriaByReviewType, 
    ChatState, SESSION_STATE_DEFAULTS
)
from .data import REVIEW_TYPE_CRITERIA, SAMPLE_REVIEWS

__all__ = [
    # 타입 정의
    'Review', 'Candidate', 'CriteriaByReviewType', 
    'ChatState', 'SESSION_STATE_DEFAULTS',
    
    # 데이터
    'REVIEW_TYPE_CRITERIA', 'SAMPLE_REVIEWS'
]
