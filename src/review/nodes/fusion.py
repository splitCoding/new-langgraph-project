"""Fusion and selection nodes for review processing."""

import logging
from typing import Any, Dict, List
from ..states import State, Candidate, SelectedCandidate

logger = logging.getLogger(__name__)


def fuse_candidates_implementation(state: State) -> Dict[str, Any]:
    """Fuse candidates and prepare for Human review processing."""
    candidates = state.get("candidates", [])
    approved_candidates = state.get("approved_candidates", [])
    
    # Human feedback이 처리된 경우 approved_candidates 사용
    if approved_candidates:
        candidates = approved_candidates
        logger.info(f"Using human-approved candidates: {len(candidates)}")
    
    # 각 후보의 점수 정보 로깅
    if not candidates:
        logger.info("No candidates to process.")
        return {"selected_candidates": []}
    
    # 각 후보의 평균 점수 계산
    processed_candidates = []
    for candidate in candidates:
        scores = candidate.get("score", [])
        if scores:
            avg_score = sum(s["score"] for s in scores) / len(scores)
            candidate_with_avg = candidate.copy()
            candidate_with_avg["avg_score"] = avg_score
            processed_candidates.append(candidate_with_avg)
        else:
            logger.warning(f"Candidate {candidate.get('review_id')} has no scores")

    # 평균 점수 기준 내림차순 정렬 후 상위 10개 선택
    top_candidates = sorted(
        processed_candidates, 
        key=lambda c: c.get("avg_score", 0), 
        reverse=True
    )[:10]
    
    logger.info(f"Selected top {len(top_candidates)} candidates by average score.")
    return {"selected_candidates": top_candidates}


def select_best_candidates(state: State, max_candidates: int = 5) -> Dict[str, Any]:
    """Select the best candidates based on combined scoring."""
    candidates = state.get("candidates", [])
    
    if not candidates:
        logger.warning("No candidates available for selection")
        return {"selected_candidates": []}
    
    # Calculate composite scores for each candidate
    candidate_scores = []
    for candidate in candidates:
        scores = candidate.get("score", [])
        if not scores:
            continue
        
        # Calculate weighted average based on perspective importance
        perspective_weights = {
            "품질": 0.4,      # Quality is most important
            "진정성": 0.35,    # Authenticity is second
            "유용성": 0.25     # Helpfulness is third
        }
        
        weighted_sum = 0
        total_weight = 0
        
        for score_item in scores:
            perspective = score_item.get("perspective", "")
            score = score_item.get("score", 0)
            weight = perspective_weights.get(perspective, 0.1)  # Default weight for unknown perspectives
            
            weighted_sum += score * weight
            total_weight += weight
        
        if total_weight > 0:
            composite_score = weighted_sum / total_weight
            candidate_scores.append({
                "candidate": candidate,
                "composite_score": composite_score,
                "individual_scores": scores
            })
    
    # Sort by composite score and select top candidates
    candidate_scores.sort(key=lambda x: x["composite_score"], reverse=True)
    selected = candidate_scores[:max_candidates]
    
    # Create SelectedCandidate objects
    selected_candidates = []
    for item in selected:
        selected_candidate = SelectedCandidate(
            candidate=item["candidate"],
            selected=True
        )
        selected_candidates.append(selected_candidate)
    
    logger.info(f"Selected {len(selected_candidates)} best candidates from {len(candidates)} total")
    
    return {"selected_candidates": selected_candidates}


def rank_candidates_by_criteria(state: State, criteria_weights: Dict[str, float] = None) -> Dict[str, Any]:
    """Rank candidates using custom criteria weights."""
    if criteria_weights is None:
        criteria_weights = {
            "품질": 0.4,
            "진정성": 0.35,
            "유용성": 0.25
        }
    
    candidates = state.get("candidates", [])
    
    if not candidates:
        return {"ranked_candidates": []}
    
    ranked_candidates = []
    
    for candidate in candidates:
        scores = candidate.get("score", [])
        if not scores:
            continue
        
        # Calculate ranking score
        total_score = 0
        total_weight = 0
        score_breakdown = {}
        
        for score_item in scores:
            perspective = score_item.get("perspective", "")
            score = score_item.get("score", 0)
            weight = criteria_weights.get(perspective, 0)
            
            if weight > 0:
                total_score += score * weight
                total_weight += weight
                score_breakdown[perspective] = {
                    "score": score,
                    "weight": weight,
                    "weighted_score": score * weight
                }
        
        if total_weight > 0:
            final_score = total_score / total_weight
            
            ranked_candidates.append({
                "candidate": candidate,
                "final_score": final_score,
                "score_breakdown": score_breakdown,
                "raw_scores": scores
            })
    
    # Sort by final score
    ranked_candidates.sort(key=lambda x: x["final_score"], reverse=True)
    
    logger.info(f"Ranked {len(ranked_candidates)} candidates using criteria weights")
    
    return {"ranked_candidates": ranked_candidates}