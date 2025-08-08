"""샘플 데이터 정의."""

from .types import Review

# 리뷰 타입별 기준 정의
REVIEW_TYPE_CRITERIA = {
    "포토 리뷰": ["이미지가 반드시 존재하는"],
    "솔직한 리뷰": ["감정이 드러나는", "구체적인", "신뢰성있는"],
    "긍정적인 리뷰": ["긍정적인 톤", "추천 의도가 명확한", "만족도가 높은"],
    "사용경험에 대한 내용이 포함된 리뷰": ["실제 사용 경험이 담긴", "구체적인 사용 상황 설명", "사용 결과에 대한 언급"]
}

# 샘플 리뷰 데이터
SAMPLE_REVIEWS: list[Review] = [
    Review(
        id=1,
        text="이 제품 정말 좋아요! 사용하기 편하고 성능도 뛰어나요.",
        rating=5,
        created_at="2023-10-01",
        image_exists=True
    ),
    Review(
        id=2,
        text="정말 만족스러운 제품입니다!",
        rating=5,
        created_at="2023-10-02",
        image_exists=True
    ),
    Review(
        id=3,
        text="가성비 최고!",
        rating=5,
        created_at="2023-10-03",
        image_exists=False
    ),
    Review(
        id=4,
        text="괜찮긴 한데...",
        rating=3,
        created_at="2023-10-04",
        image_exists=False
    ),
    Review(
        id=5,
        text="일주일 사용 후기",
        rating=4,
        created_at="2023-10-05",
        image_exists=True
    )
]
