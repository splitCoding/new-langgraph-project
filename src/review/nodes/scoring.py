"""
Scoring nodes for review analysis.

Updated to use enhanced HTML preprocessing and token estimation tools:
- html_preprocessor: Advanced HTML cleaning with configurable options
- token_estimator: Multi-model token estimation and intelligent text chunking

Improvements:
- Better HTML entity handling and tag removal
- Sentence-boundary aware chunking for large reviews
- Enhanced token estimation with fallback mechanisms
- Support for split review handling in scoring
"""

import logging
import asyncio
import concurrent.futures
from typing import Any, Dict, List
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import StrOutputParser
import re

from ..states import State, Candidate, CandidateScore
from ...util.html_preprocessor import clean_html_text
from ...util.token_estimator import estimate_tokens, TextChunker

logger = logging.getLogger(__name__)

# Model configurations
MODEL_CONFIGS = {
    "gpt-4o-mini": {
        "max_tokens": 128000,
        "encoding": "cl100k_base",
        "output_tokens": 16384
    },
    "gpt-4o": {
        "max_tokens": 128000,
        "encoding": "cl100k_base",
        "output_tokens": 4096
    },
    "gpt-3.5-turbo": {
        "max_tokens": 16385,
        "encoding": "cl100k_base",
        "output_tokens": 4096
    }
}


# Note: clean_html_text and estimate_tokens are now imported from util modules


def create_review_chunks(
    reviews: List[Dict[str, Any]], 
    max_tokens_per_chunk: int = 8000,
    model: str = "gpt-4o-mini"
) -> List[List[Dict[str, Any]]]:
    """Split reviews into chunks based on token limits using enhanced chunker."""
    chunks = []
    current_chunk = []
    current_tokens = 0
    
    # 프롬프트 템플릿의 기본 토큰 수 (고정 부분)
    base_prompt_tokens = estimate_tokens("""
        다음 리뷰들을 {} 관점에서 평가해주세요.
        평가 기준: {}
        
        평가 요청사항:
        1. 각 리뷰를 위 기준에 따라 0-100점 사이의 점수를 매겨주세요
        2. 응답 형식: "리뷰 ID: 점수" (예: "review_1: 85")
        3. 모든 리뷰에 대한 점수를 한 줄씩 응답해주세요
        
        점수:
    """, model)
    
    # Initialize chunker for individual review processing if needed
    chunker = TextChunker(model, max_tokens_per_chunk)
    
    for review in reviews:
        # 리뷰 텍스트 전처리 (enhanced HTML cleaning)
        clean_text = clean_html_text(review.get('text', ''))
        review_with_clean_text = {**review, 'cleaned_text': clean_text}
        
        # Check if single review is too large and needs splitting
        review_text = f"리뷰 {len(current_chunk) + 1} (ID: {review['id']}): {clean_text}\n\n"
        review_tokens = estimate_tokens(review_text, model)
        
        # If single review exceeds chunk size, split it
        if review_tokens + base_prompt_tokens > max_tokens_per_chunk:
            # Save current chunk if it exists
            if current_chunk:
                chunks.append(current_chunk)
                current_chunk = []
                current_tokens = 0
            
            # Split large review text using chunker
            text_chunks = chunker.chunk_text(clean_text, preserve_sentences=True)
            for i, chunk_text in enumerate(text_chunks):
                split_review = {
                    **review_with_clean_text,
                    'cleaned_text': chunk_text,
                    'id': f"{review['id']}_part{i+1}",
                    'original_id': review['id'],
                    'is_split': True,
                    'part_number': i + 1,
                    'total_parts': len(text_chunks)
                }
                chunks.append([split_review])
            continue
        
        # 청크 크기 확인
        if current_chunk and (current_tokens + review_tokens + base_prompt_tokens) > max_tokens_per_chunk:
            chunks.append(current_chunk)
            current_chunk = [review_with_clean_text]
            current_tokens = review_tokens
        else:
            current_chunk.append(review_with_clean_text)
            current_tokens += review_tokens
    
    if current_chunk:
        chunks.append(current_chunk)
    
    logger.info(f"Created {len(chunks)} chunks from {len(reviews)} reviews")
    return chunks


def score_reviews_batch_with_llm(
    reviews: List[Dict[str, Any]], 
    criteria_type: str, 
    criteria: List[str],
    model: str = "gpt-4o-mini",
    max_chunk_tokens: int = 8000
) -> Dict[str, int]:
    """Score multiple reviews with chunking and parallel processing."""
    try:
        # 토큰 수가 많은 경우 청킹 처리
        chunks = create_review_chunks(reviews, max_chunk_tokens, model)
        
        if len(chunks) == 1:
            # 단일 청크인 경우 기존 로직 사용
            return _score_single_chunk(chunks[0], criteria_type, criteria, model)
        else:
            # 다중 청크인 경우 병렬 처리
            logger.info(f"Processing {len(chunks)} chunks in parallel for {criteria_type}")
            return _score_multiple_chunks_parallel(chunks, criteria_type, criteria, model)
            
    except Exception as e:
        logger.error(f"LLM batch scoring failed: {e}")
        return {review['id']: 50 for review in reviews}


def _score_single_chunk(
    reviews: List[Dict[str, Any]], 
    criteria_type: str, 
    criteria: List[str],
    model: str = "gpt-4o-mini"
) -> Dict[str, int]:
    """Score a single chunk of reviews."""
    try:
        # LLM 모델 초기화
        config = MODEL_CONFIGS.get(model, MODEL_CONFIGS["gpt-4o-mini"])
        llm = ChatOpenAI(
            model=model,
            temperature=0.1,
            max_tokens=min(config["output_tokens"], 2000)  # 출력 토큰 제한
        )
        
        # 리뷰들을 텍스트로 구성 (전처리된 텍스트 사용)
        reviews_text = ""
        for i, review in enumerate(reviews, 1):
            # cleaned_text가 있으면 사용, 없으면 원본 텍스트 전처리
            text = review.get('cleaned_text') or clean_html_text(review.get('text', ''))
            reviews_text += f"리뷰 {i} (ID: {review['id']}): {text}\n\n"
        
        # 프롬프트 템플릿 생성
        prompt = ChatPromptTemplate.from_template("""
        다음 리뷰들을 {criteria_type} 관점에서 평가해주세요.
        평가 기준: {criteria}
        
        {reviews_text}
        
        평가 요청사항:
        1. 각 리뷰를 위 기준에 따라 0-100점 사이의 점수를 매겨주세요
        2. 응답 형식: "리뷰 ID: 점수" (예: "review_1: 85")
        3. 모든 리뷰에 대한 점수를 한 줄씩 응답해주세요
        
        점수:
        """)
        
        # 체인 생성
        chain = prompt | llm | StrOutputParser()
        
        # LLM 호출
        response = chain.invoke({
            "criteria_type": criteria_type,
            "criteria": ", ".join(criteria),
            "reviews_text": reviews_text
        })
        
        # 응답 파싱
        scores = {}
        lines = response.strip().split('\n')
        
        logger.debug(f"LLM response for {criteria_type}:\n{response}")
        
        # 리뷰 ID와 인덱스 매핑 생성
        review_index_to_id = {}
        for i, review in enumerate(reviews, 1):
            review_index_to_id[str(i)] = str(review['id'])
        
        logger.debug(f"Review index mapping: {review_index_to_id}")
        
        for line in lines:
            line = line.strip()
            if ':' in line and line:
                try:
                    # "리뷰 1: 20" 패턴에서 인덱스와 점수 추출
                    review_match = re.search(r'리뷰\s*(\d+)', line)
                    
                    if review_match:
                        # 리뷰 인덱스 추출
                        review_index = review_match.group(1)
                        # 점수 추출
                        score_part = line.split(':')[-1]
                        numbers = re.findall(r'\d+', score_part)
                        if numbers:
                            score = int(numbers[0])
                            score = max(0, min(100, score))  # 0-100 범위 제한
                            
                            # 인덱스를 실제 리뷰 ID로 변환
                            if review_index in review_index_to_id:
                                review_id = review_index_to_id[review_index]
                                scores[review_id] = score
                                logger.debug(f"Parsed: Review index {review_index} (ID: {review_id}) -> Score {score}")
                            else:
                                logger.warning(f"Unknown review index: {review_index}")
                    else:
                        # 다른 패턴 시도 (예: "735: 85" 같은 직접 ID 형식)
                        review_id_part, score_part = line.split(':', 1)
                        # 숫자만 추출해서 ID로 사용
                        id_numbers = re.findall(r'\d+', review_id_part)
                        if id_numbers:
                            review_id = id_numbers[-1]  # 마지막 숫자를 ID로 사용
                            score_numbers = re.findall(r'\d+', score_part)
                            if score_numbers:
                                score = int(score_numbers[0])
                                score = max(0, min(100, score))  # 0-100 범위 제한
                                scores[review_id] = score
                                logger.debug(f"Parsed (fallback): Review {review_id} -> Score {score}")
                                
                except Exception as e:
                    logger.warning(f"Could not parse line: {line}, error: {e}")
        
        logger.debug(f"Extracted scores: {scores}")
        
        # 모든 리뷰에 대한 점수가 있는지 확인하고 없으면 기본값 설정
        for review in reviews:
            review_id = str(review['id'])  # ID를 문자열로 변환
            # Handle split reviews - check for both original and split IDs
            if review_id not in scores:
                # For split reviews, try to find score using original pattern
                found_score = False
                if review.get('is_split'):
                    original_id = str(review.get('original_id', review_id))
                    for score_key in scores.keys():
                        if score_key.startswith(original_id):
                            scores[review_id] = scores[score_key]
                            found_score = True
                            logger.debug(f"Found split review score: {review_id} -> {scores[review_id]}")
                            break
                
                if not found_score:
                    logger.warning(f"No score found for review {review_id}, using default")
                    scores[review_id] = 50
        
        # 최종 점수 딕셔너리를 원래 ID 타입과 맞춤
        final_scores = {}
        for review in reviews:
            original_id = review['id']
            string_id = str(original_id)
            if string_id in scores:
                final_scores[original_id] = scores[string_id]
            else:
                final_scores[original_id] = 50
        
        logger.debug(f"LLM scored {len(final_scores)} reviews for {criteria_type}")
        return final_scores
            
    except Exception as e:
        logger.error(f"Single chunk scoring failed: {e}")
        return {review['id']: 50 for review in reviews}


def _score_multiple_chunks_parallel(
    chunks: List[List[Dict[str, Any]]], 
    criteria_type: str, 
    criteria: List[str],
    model: str = "gpt-4o-mini"
) -> Dict[str, int]:
    """Score multiple chunks in parallel."""
    try:
        all_scores = {}
        
        # ThreadPoolExecutor를 사용한 병렬 처리
        with concurrent.futures.ThreadPoolExecutor(max_workers=min(len(chunks), 4)) as executor:
            # 각 청크를 별도 스레드에서 처리
            future_to_chunk = {
                executor.submit(_score_single_chunk, chunk, criteria_type, criteria, model): i
                for i, chunk in enumerate(chunks)
            }
            
            # 완료된 작업들의 결과를 수집
            for future in concurrent.futures.as_completed(future_to_chunk):
                chunk_index = future_to_chunk[future]
                try:
                    chunk_scores = future.result()
                    all_scores.update(chunk_scores)
                    logger.debug(f"Completed chunk {chunk_index + 1}/{len(chunks)} for {criteria_type}")
                except Exception as exc:
                    logger.error(f"Chunk {chunk_index + 1} failed for {criteria_type}: {exc}")
                    # 실패한 청크의 리뷰들에 기본 점수 할당
                    for review in chunks[chunk_index]:
                        all_scores[review['id']] = 50
        
        logger.info(f"Parallel scoring completed for {criteria_type}: {len(all_scores)} reviews")
        return all_scores
        
    except Exception as e:
        logger.error(f"Parallel chunk scoring failed: {e}")
        # 모든 청크의 리뷰들에 기본 점수 할당
        all_scores = {}
        for chunk in chunks:
            for review in chunk:
                all_scores[review['id']] = 50
        return all_scores


def score_review_with_llm(review: Dict[str, Any], criteria_type: str, criteria: List[str]) -> int:
    """Score a single review using LLM (kept for backward compatibility)."""
    scores = score_reviews_batch_with_llm([review], criteria_type, criteria)
    return scores.get(review['id'], 50)


def process_single_criteria_sync(
    criteria_item: Dict[str, Any], 
    filtered_reviews: List[Dict[str, Any]],
    model: str = "gpt-4o-mini",
    max_chunk_tokens: int = 8000
) -> Dict[str, Dict[str, Any]]:
    """Process a single criteria type synchronously."""
    criteria_type = criteria_item["type"]
    criteria = criteria_item["criteria"]
    
    logger.info(f"Processing criteria: {criteria_type}")
    
    try:
        # 모든 리뷰를 청킹을 고려하여 LLM으로 평가
        scores = score_reviews_batch_with_llm(
            filtered_reviews, criteria_type, criteria, model, max_chunk_tokens
        )
        
        # 결과를 기존 형식으로 변환
        review_scores = {}
        for review_id, score in scores.items():
            review_scores[review_id] = {"score": score, "perspective": criteria_type}
            
    except Exception as e:
        logger.error(f"Error scoring reviews for {criteria_type}: {e}")
        # 오류 시 모든 리뷰에 기본 점수 사용
        review_scores = {}
        for review in filtered_reviews:
            review_scores[review["id"]] = {"score": 50, "perspective": criteria_type}
    
    logger.info(f"Completed processing criteria: {criteria_type} ({len(review_scores)} reviews)")
    return {criteria_type: review_scores}


async def process_single_criteria_async(criteria_item: Dict[str, Any], filtered_reviews: List[Dict[str, Any]]) -> List[Candidate]:
    """Process a single criteria type asynchronously."""
    criteria_type = criteria_item["type"]
    criteria = criteria_item["criteria"]
    candidates = []
    
    logger.info(f"Processing criteria asynchronously: {criteria_type}")
    
    # 각 리뷰를 해당 criteria로 평가
    for review in filtered_reviews:
        # 비동기 작업 시뮬레이션 (실제로는 비동기 LLM API 호출 등)
        await asyncio.sleep(0.001)  # 1ms 지연으로 비동기 처리 시뮬레이션
        
        # 여기서 실제로는 LLM을 사용하여 각 criteria에 대해 점수를 매겨야 함
        score = 80 + (hash(f"{review['id']}{criteria_type}") % 20)  # 임시 점수 생성
        
        candidate = Candidate(
            review_id=review["id"],
            score=[CandidateScore(score=score, perspective=criteria_type)]
        )
        candidates.append(candidate)
    
    logger.info(f"Completed async processing criteria: {criteria_type} ({len(candidates)} candidates)")
    return candidates


def process_all_perspectives(
    state: State,
    model: str = "gpt-4o-mini",
    max_chunk_tokens: int = 8000
) -> Dict[str, Any]:
    """Process all perspectives using ThreadPoolExecutor."""
    criteria_list = state.get("criteria_by_type", [
        {"type": "품질", "criteria": ["성능", "내구성", "디자인"]},
        {"type": "진정성", "criteria": ["솔직함", "경험 기반", "구체성"]},
        {"type": "유용성", "criteria": ["도움됨", "정보성", "실용성"]}
    ])
    
    filtered_reviews = state.get("filtered_reviews", [])
    
    if not filtered_reviews:
        logger.warning("No filtered reviews to process")
        return {"candidates": []}
    
    logger.info(f"Starting parallel processing of {len(criteria_list)} criteria types")
    
    # ThreadPoolExecutor를 사용한 병렬 처리
    with concurrent.futures.ThreadPoolExecutor(max_workers=len(criteria_list)) as executor:
        # 각 criteria를 별도 스레드에서 처리
        future_to_criteria = {
            executor.submit(
                process_single_criteria_sync, 
                criteria_item, 
                filtered_reviews, 
                model, 
                max_chunk_tokens
            ): criteria_item
            for criteria_item in criteria_list
        }
        
        # 모든 criteria의 결과를 수집
        all_results = {}
        
        # 완료된 작업들의 결과를 수집
        for future in concurrent.futures.as_completed(future_to_criteria):
            criteria_item = future_to_criteria[future]
            try:
                result = future.result()
                all_results.update(result)
                logger.info(f"Successfully processed {criteria_item['type']}")
            except Exception as exc:
                logger.error(f"Error processing {criteria_item['type']}: {exc}")
        
        # 리뷰 ID별로 모든 점수를 조합
        candidates = []
        for review in filtered_reviews:
            review_id = review["id"]
            scores = []
            
            for criteria_type in all_results:
                if review_id in all_results[criteria_type]:
                    score_data = all_results[criteria_type][review_id]
                    scores.append(CandidateScore(
                        score=score_data["score"],
                        perspective=score_data["perspective"]
                    ))
            
            if scores:  # 점수가 있는 경우에만 후보로 추가
                candidates.append(Candidate(
                    review_id=review_id,
                    score=scores
                ))
    
    logger.info(f"Completed parallel processing. Total unique candidates: {len(candidates)}")
    return {"candidates": candidates}


def process_all_perspectives_async_version(state: State) -> Dict[str, Any]:
    """Process all perspectives using asyncio."""
    criteria_list = state.get("criteria_by_type", [
        {"type": "품질", "criteria": ["성능", "내구성", "디자인"]},
        {"type": "진정성", "criteria": ["솔직함", "경험 기반", "구체성"]},
        {"type": "유용성", "criteria": ["도움됨", "정보성", "실용성"]}
    ])
    
    filtered_reviews = state.get("filtered_reviews", [])
    
    if not filtered_reviews:
        logger.warning("No filtered reviews to process")
        return {"candidates": []}
    
    async def async_process():
        logger.info(f"Starting async parallel processing of {len(criteria_list)} criteria types")
        
        # 각 criteria를 비동기로 병렬 처리
        tasks = [
            process_single_criteria_async(criteria_item, filtered_reviews)
            for criteria_item in criteria_list
        ]
        
        # 모든 작업을 병렬로 실행하고 결과를 수집
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        all_candidates = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Error processing {criteria_list[i]['type']}: {result}")
            else:
                all_candidates.extend(result)
        
        logger.info(f"Completed async parallel processing. Total candidates: {len(all_candidates)}")
        return all_candidates
    
    # 비동기 함수를 동기 컨텍스트에서 실행
    try:
        # 새 이벤트 루프에서 실행
        all_candidates = asyncio.run(async_process())
    except RuntimeError as e:
        logger.warning(f"AsyncIO error: {e}. Falling back to thread-based processing.")
        # asyncio 실행 실패 시 스레드 기반 처리로 폴백
        return process_all_perspectives(state)
    
    return {"candidates": all_candidates}


def create_perspective_node_implementation(criteria_type: str, criteria_list: List[str]):
    """Create a perspective node implementation function."""
    def perspective_implementation(state: State) -> Dict[str, Any]:
        filtered_reviews = state.get("filtered_reviews", [])
        
        if not filtered_reviews:
            return {"candidates": []}
        
        candidates = []
        for review in filtered_reviews[:3]:  # 최대 3개
            score = score_review_with_llm(review, criteria_type, criteria_list)
            candidate = Candidate(
                review_id=review["id"],
                score=[CandidateScore(score=score, perspective=criteria_type)]
            )
            candidates.append(candidate)
        
        return {"candidates": candidates}
    
    return perspective_implementation