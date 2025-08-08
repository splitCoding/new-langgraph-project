"""OpenAI moderation tool for profanity and content filtering."""

import os
import time
import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import openai
from langchain_core.tools import tool

logger = logging.getLogger(__name__)


@dataclass
class ModerationResult:
    """Result of content moderation."""
    flagged: bool
    categories: Dict[str, bool]
    category_scores: Dict[str, float]
    reason: Optional[str] = None
    custom_violations: List[str] = field(default_factory=list)


@dataclass
class RateLimiter:
    """Rate limiter for API calls."""
    max_calls: int = 60  # Maximum calls per minute
    time_window: int = 60  # Time window in seconds
    calls: List[datetime] = field(default_factory=list)
    
    def can_make_call(self) -> bool:
        """Check if a call can be made within rate limits."""
        now = datetime.now()
        
        # Remove calls older than time window
        self.calls = [call_time for call_time in self.calls 
                     if (now - call_time).total_seconds() < self.time_window]
        
        return len(self.calls) < self.max_calls
    
    def record_call(self) -> None:
        """Record a successful API call."""
        self.calls.append(datetime.now())
    
    def wait_time(self) -> float:
        """Get time to wait before next call can be made."""
        if not self.calls:
            return 0.0
        
        oldest_call = min(self.calls)
        elapsed = (datetime.now() - oldest_call).total_seconds()
        
        if elapsed >= self.time_window:
            return 0.0
        
        return self.time_window - elapsed


class ContentModerationTool:
    """Tool for content moderation using OpenAI and custom rules."""
    
    # Default custom rules for Korean content
    DEFAULT_CUSTOM_RULES = {
        "profanity_keywords": [
            "씨발", "시발", "병신", "개새끼", "미친", "좆", "지랄", "꺼져", "닥쳐"
        ],
        "spam_patterns": [
            "광고", "홍보", "마케팅", "구매링크", "할인쿠폰", "이벤트참여"
        ],
        "fake_indicators": [
            "가짜", "조작", "허위", "거짓", "사기", "속임수"
        ]
    }
    
    def __init__(self, 
                 openai_api_key: Optional[str] = None,
                 rate_limit_per_minute: int = 60,
                 custom_rules: Optional[Dict[str, List[str]]] = None):
        """
        Initialize moderation tool.
        
        Args:
            openai_api_key: OpenAI API key (defaults to env var)
            rate_limit_per_minute: Max API calls per minute
            custom_rules: Custom moderation rules
        """
        self.openai_client = openai.OpenAI(
            api_key=openai_api_key or os.getenv("OPENAI_API_KEY")
        )
        self.rate_limiter = RateLimiter(max_calls=rate_limit_per_minute)
        self.custom_rules = custom_rules or self.DEFAULT_CUSTOM_RULES
        
    def _check_custom_rules(self, text: str) -> Tuple[bool, List[str]]:
        """
        Check content against custom rules.
        
        Args:
            text: Text to check
            
        Returns:
            Tuple of (has_violations, list_of_violations)
        """
        violations = []
        text_lower = text.lower()
        
        # Check profanity
        for word in self.custom_rules.get("profanity_keywords", []):
            if word in text_lower:
                violations.append(f"Profanity detected: {word}")
        
        # Check spam patterns
        for pattern in self.custom_rules.get("spam_patterns", []):
            if pattern in text_lower:
                violations.append(f"Spam pattern detected: {pattern}")
        
        # Check fake indicators
        for indicator in self.custom_rules.get("fake_indicators", []):
            if indicator in text_lower:
                violations.append(f"Fake content indicator: {indicator}")
        
        return len(violations) > 0, violations
    
    def _call_openai_moderation(self, text: str) -> Optional[ModerationResult]:
        """
        Call OpenAI moderation API with rate limiting.
        
        Args:
            text: Text to moderate
            
        Returns:
            ModerationResult or None if rate limited
        """
        # Check rate limit
        if not self.rate_limiter.can_make_call():
            wait_time = self.rate_limiter.wait_time()
            logger.warning(f"Rate limit reached. Need to wait {wait_time:.1f} seconds")
            return None
        
        try:
            response = self.openai_client.moderations.create(input=text)
            self.rate_limiter.record_call()
            
            result = response.results[0]
            
            return ModerationResult(
                flagged=result.flagged,
                categories=dict(result.categories),
                category_scores=dict(result.category_scores)
            )
            
        except openai.APIError as e:
            logger.error(f"OpenAI moderation API error: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error in OpenAI moderation: {e}")
            return None
    
    def moderate_content(self, text: str, use_openai: bool = True, wait_if_rate_limited: bool = False) -> ModerationResult:
        """
        Moderate content using OpenAI and custom rules.
        
        Args:
            text: Text to moderate
            use_openai: Whether to use OpenAI moderation
            wait_if_rate_limited: Whether to wait if rate limited
            
        Returns:
            ModerationResult with combined results
        """
        # Check custom rules first
        has_custom_violations, custom_violations = self._check_custom_rules(text)
        
        # Initialize result with custom rule findings
        result = ModerationResult(
            flagged=has_custom_violations,
            categories={},
            category_scores={},
            custom_violations=custom_violations
        )
        
        # Use OpenAI moderation if enabled and available
        if use_openai:
            # Wait for rate limit if requested
            if wait_if_rate_limited:
                wait_time = self.rate_limiter.wait_time()
                if wait_time > 0:
                    logger.info(f"Waiting {wait_time:.1f} seconds for rate limit")
                    time.sleep(wait_time)
            
            openai_result = self._call_openai_moderation(text)
            
            if openai_result:
                # Combine results
                result.flagged = result.flagged or openai_result.flagged
                result.categories = openai_result.categories
                result.category_scores = openai_result.category_scores
                
                # Add reason if flagged
                if openai_result.flagged:
                    flagged_categories = [cat for cat, flagged in openai_result.categories.items() if flagged]
                    result.reason = f"OpenAI flagged categories: {', '.join(flagged_categories)}"
            else:
                logger.warning("OpenAI moderation unavailable, using custom rules only")
        
        return result
    
    def moderate_batch(self, texts: List[str], batch_size: int = 10) -> List[ModerationResult]:
        """
        Moderate multiple texts in batches.
        
        Args:
            texts: List of texts to moderate
            batch_size: Number of texts to process at once
            
        Returns:
            List of ModerationResult objects
        """
        results = []
        
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            batch_results = []
            
            for text in batch:
                result = self.moderate_content(text, wait_if_rate_limited=True)
                batch_results.append(result)
                
                # Small delay between calls to respect rate limits
                time.sleep(0.1)
            
            results.extend(batch_results)
            logger.info(f"Processed batch {i//batch_size + 1}/{(len(texts) + batch_size - 1)//batch_size}")
        
        return results


# Global moderation tool instance
_moderation_tool = None

def get_moderation_tool() -> ContentModerationTool:
    """Get singleton moderation tool instance."""
    global _moderation_tool
    if _moderation_tool is None:
        _moderation_tool = ContentModerationTool()
    return _moderation_tool


# LangGraph tool definitions
@tool
def moderate_text(text: str, use_openai: bool = True, strict_mode: bool = False) -> Dict[str, Any]:
    """
    Moderate text content for profanity and inappropriate content.
    
    Args:
        text: Text to moderate
        use_openai: Whether to use OpenAI moderation API
        strict_mode: Whether to use strict moderation rules
        
    Returns:
        Dictionary with moderation results
    """
    try:
        tool = get_moderation_tool()
        
        # Add stricter custom rules in strict mode
        if strict_mode:
            tool.custom_rules["profanity_keywords"].extend([
                "바보", "멍청이", "등신", "쓰레기", "죽어", "짜증"
            ])
        
        result = tool.moderate_content(text, use_openai=use_openai, wait_if_rate_limited=True)
        
        return {
            "flagged": result.flagged,
            "openai_categories": result.categories,
            "openai_scores": result.category_scores,
            "custom_violations": result.custom_violations,
            "reason": result.reason,
            "is_safe": not result.flagged
        }
        
    except Exception as e:
        logger.error(f"Failed to moderate text: {e}")
        return {
            "flagged": True,  # Conservative approach - flag on error
            "openai_categories": {},
            "openai_scores": {},
            "custom_violations": [f"Moderation error: {str(e)}"],
            "reason": "Moderation service unavailable",
            "is_safe": False
        }


@tool
def moderate_review_batch(reviews: List[Dict[str, Any]], text_field: str = "text") -> List[Dict[str, Any]]:
    """
    Moderate a batch of reviews for content filtering.
    
    Args:
        reviews: List of review dictionaries
        text_field: Field name containing text to moderate
        
    Returns:
        List of reviews with moderation results added
    """
    try:
        tool = get_moderation_tool()
        
        # Extract texts
        texts = [review.get(text_field, "") for review in reviews]
        
        # Moderate batch
        moderation_results = tool.moderate_batch(texts)
        
        # Add moderation results to reviews
        enhanced_reviews = []
        for review, moderation in zip(reviews, moderation_results):
            enhanced_review = review.copy()
            enhanced_review["moderation"] = {
                "flagged": moderation.flagged,
                "categories": moderation.categories,
                "category_scores": moderation.category_scores,
                "custom_violations": moderation.custom_violations,
                "is_safe": not moderation.flagged
            }
            enhanced_reviews.append(enhanced_review)
        
        return enhanced_reviews
        
    except Exception as e:
        logger.error(f"Failed to moderate review batch: {e}")
        # Return original reviews with error flag
        return [
            {
                **review,
                "moderation": {
                    "flagged": True,
                    "categories": {},
                    "category_scores": {},
                    "custom_violations": [f"Moderation error: {str(e)}"],
                    "is_safe": False
                }
            }
            for review in reviews
        ]


@tool
def filter_safe_reviews(reviews: List[Dict[str, Any]], text_field: str = "text") -> List[Dict[str, Any]]:
    """
    Filter reviews to return only safe (non-flagged) content.
    
    Args:
        reviews: List of review dictionaries
        text_field: Field name containing text to moderate
        
    Returns:
        List of safe reviews
    """
    try:
        # First moderate all reviews
        moderated_reviews = moderate_review_batch(reviews, text_field)
        
        # Filter safe reviews
        safe_reviews = [
            review for review in moderated_reviews 
            if review.get("moderation", {}).get("is_safe", False)
        ]
        
        logger.info(f"Filtered {len(reviews)} reviews to {len(safe_reviews)} safe reviews")
        return safe_reviews
        
    except Exception as e:
        logger.error(f"Failed to filter safe reviews: {e}")
        return []  # Conservative approach - return no reviews on error


@tool 
def get_moderation_stats() -> Dict[str, Any]:
    """
    Get current moderation tool statistics.
    
    Returns:
        Dictionary with moderation statistics
    """
    try:
        tool = get_moderation_tool()
        
        now = datetime.now()
        recent_calls = [
            call for call in tool.rate_limiter.calls 
            if (now - call).total_seconds() < tool.rate_limiter.time_window
        ]
        
        return {
            "rate_limit": {
                "max_calls_per_minute": tool.rate_limiter.max_calls,
                "current_calls_in_window": len(recent_calls),
                "remaining_calls": tool.rate_limiter.max_calls - len(recent_calls),
                "wait_time_seconds": tool.rate_limiter.wait_time()
            },
            "custom_rules": {
                "profanity_keywords_count": len(tool.custom_rules.get("profanity_keywords", [])),
                "spam_patterns_count": len(tool.custom_rules.get("spam_patterns", [])),
                "fake_indicators_count": len(tool.custom_rules.get("fake_indicators", []))
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to get moderation stats: {e}")
        return {}