"""Filter nodes for review processing."""

import logging
from typing import Any, Dict, List
from ..states import State
from ..tools.moderation import filter_safe_reviews

logger = logging.getLogger(__name__)


def filter_by_rules(state: State) -> Dict[str, Any]:
    """Filter reviews based on business rules and content moderation."""
    reviews = state.get("reviews", [])
    
    if not reviews:
        logger.warning("No reviews to filter")
        return {"filtered_reviews": []}
    
    logger.info(f"Starting to filter {len(reviews)} reviews")
    
    # Step 1: Basic business rule filtering
    basic_filtered = []
    for review in reviews:
        # Check text length (must be > 20 characters)
        text = review.get("text", "")
        if len(text.strip()) <= 20:
            continue
        
        # Check if image exists (preferred but not required)
        basic_filtered.append(review)
    
    logger.info(f"After basic filtering: {len(basic_filtered)} reviews")
    
    # Step 2: Content moderation filtering
    try:
        # Use moderation tool to filter out inappropriate content
        safe_reviews = filter_safe_reviews(basic_filtered, text_field="text")
        logger.info(f"After content moderation: {len(safe_reviews)} reviews")
        
        return {"filtered_reviews": safe_reviews}
        
    except Exception as e:
        logger.error(f"Content moderation failed, using basic filtering only: {e}")
        return {"filtered_reviews": basic_filtered}


def check_review_exists(state: State) -> Dict[str, Any]:
    """Check if filtered reviews exist."""
    filtered_reviews = state.get("filtered_reviews", [])
    exists = len(filtered_reviews) > 0
    
    logger.info(f"Review existence check: {exists} ({len(filtered_reviews)} reviews)")
    
    return {"exists": exists}


def filter_by_criteria(state: State, criteria_type: str, criteria: List[str]) -> Dict[str, Any]:
    """Filter reviews based on specific criteria."""
    filtered_reviews = state.get("filtered_reviews", [])
    
    if not filtered_reviews:
        return {"criteria_filtered_reviews": []}
    
    # This is a placeholder implementation
    # In a real scenario, you might use NLP techniques to match criteria
    criteria_filtered = []
    
    for review in filtered_reviews:
        text_lower = review.get("text", "").lower()
        
        # Simple keyword matching for demonstration
        matches_criteria = False
        for criterion in criteria:
            if criterion.lower() in text_lower:
                matches_criteria = True
                break
        
        if matches_criteria:
            criteria_filtered.append(review)
    
    logger.info(f"Filtered {len(filtered_reviews)} to {len(criteria_filtered)} reviews for criteria: {criteria_type}")
    
    return {"criteria_filtered_reviews": criteria_filtered}


def prioritize_reviews_with_images(state: State) -> Dict[str, Any]:
    """Prioritize reviews that have images."""
    filtered_reviews = state.get("filtered_reviews", [])
    
    if not filtered_reviews:
        return {"prioritized_reviews": []}
    
    # Separate reviews with and without images
    with_images = [review for review in filtered_reviews if review.get("image_exists", False)]
    without_images = [review for review in filtered_reviews if not review.get("image_exists", False)]
    
    # Put reviews with images first
    prioritized = with_images + without_images
    
    logger.info(f"Prioritized {len(with_images)} reviews with images, {len(without_images)} without images")
    
    return {"prioritized_reviews": prioritized}