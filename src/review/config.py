"""Configuration for review analysis graph."""

from dataclasses import dataclass
from typing import Dict, List, Any
from .nodes.data_loader import load_reviews_from_db, load_sample_reviews
from .nodes.filters import filter_by_rules, check_review_exists
from .nodes.scoring import process_all_perspectives, process_all_perspectives_async_version
from .nodes.fusion import fuse_candidates_implementation


@dataclass
class NodeNames:
    """Graph node name constants."""
    LOAD_REVIEWS = "load_reviews"
    FILTER_BY_RULES = "filter_by_rules"
    CHECK_REVIEW_EXISTS = "check_review_exists"
    PICK_CANDIDATES = "pick_candidates"
    QUALITY_PERSPECTIVE = "quality_perspective"
    AUTHENTICITY_PERSPECTIVE = "authenticity_perspective"
    HELPFULNESS_PERSPECTIVE = "helpfulness_perspective"
    FUSE_CANDIDATES = "fuse_candidates"
    GENERATE_TITLE_AND_SUMMARY = "generate_title_and_summary"
    VALIDATE_TITLE_AND_SUMMARY = "validate_title_and_summary"
    SAVE_BEST_REVIEWS = "save_best_reviews"
    END = "end"


@dataclass
class ReviewConfig:
    """Configuration for review analysis."""
    use_database: bool = True
    use_sample_data: bool = False
    use_async_processing: bool = False
    max_candidates: int = 10
    min_rating: int = 4
    min_text_length: int = 20
    enable_content_moderation: bool = True
    
    # Scoring criteria
    default_criteria: List[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.default_criteria is None:
            self.default_criteria = [
                {"type": "품질", "criteria": ["성능", "내구성", "디자인", "완성도"]},
                {"type": "진정성", "criteria": ["솔직함", "경험 기반", "구체성", "신뢰성"]},
                {"type": "유용성", "criteria": ["도움됨", "정보성", "실용성", "구체성"]}
            ]


# Node implementations mapping
NODE_IMPLEMENTATIONS = {
    NodeNames.LOAD_REVIEWS: load_reviews_from_db,
    NodeNames.FILTER_BY_RULES: filter_by_rules,
    NodeNames.CHECK_REVIEW_EXISTS: check_review_exists,
    NodeNames.PICK_CANDIDATES: process_all_perspectives,
    NodeNames.FUSE_CANDIDATES: fuse_candidates_implementation,
    NodeNames.END: lambda state: {
        "status": "BEST 리뷰 후보 선정이 완료되었습니다.",
        "selected_candidates": state.get("selected_candidates", [])
    }
}


def get_node_implementation(node_name: str, config: ReviewConfig = None):
    """Get node implementation based on configuration."""
    config = config or ReviewConfig()
    
    # Handle special cases based on configuration
    if node_name == NodeNames.LOAD_REVIEWS:
        if config.use_sample_data:
            return load_sample_reviews
        else:
            return load_reviews_from_db
    
    elif node_name == NodeNames.PICK_CANDIDATES:
        if config.use_async_processing:
            return process_all_perspectives_async_version
        else:
            return process_all_perspectives
    
    # Return default implementation
    return NODE_IMPLEMENTATIONS.get(node_name)