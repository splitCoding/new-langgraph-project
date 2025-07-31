"""
LLM 쿼리 결과를 파일 기반으로 캐싱하는 모듈
"""

import hashlib
import json
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


def json_serializer(obj):
    """datetime 객체를 JSON으로 직렬화하기 위한 헬퍼 함수"""
    if isinstance(obj, datetime):
        return obj.isoformat()
    raise TypeError(f"Object of type {type(obj)} is not JSON serializable")


class LLMQueryCache:
    """파일 기반 LLM 쿼리 캐시 시스템"""

    def __init__(self, cache_dir: str = "cache/llm_queries", ttl_hours: int = 24):
        """
        Args:
            cache_dir: 캐시 파일을 저장할 디렉터리
            ttl_hours: 캐시 유지 시간 (시간 단위)
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.ttl_seconds = ttl_hours * 3600

    def _hash_reviews(self, reviews: List[Dict]) -> str:
        """
        리뷰 데이터를 해싱합니다.
        ID + createdAt 조합을 사용하여 효율적이면서도 정확한 해싱을 제공합니다.
        """
        if not reviews:
            return "empty_reviews"

        # ID + 생성시간 조합으로 메타데이터 생성
        metadata = []
        for review in reviews:
            review_id = review.get('id', '')
            created_at = review.get('createdAt', review.get('created_at', ''))
            metadata.append((review_id, created_at))

        # 정렬하여 순서에 무관하게 동일한 해시 생성
        metadata.sort()
        metadata_str = json.dumps(metadata, ensure_ascii=False, default=json_serializer)

        return hashlib.md5(metadata_str.encode()).hexdigest()

    def _generate_cache_key(
            self,
            llm_name: str,
            reviews: List[Dict],
            focus_instruction: str,
            candidate_count: int
    ) -> str:
        """캐시 키 생성"""
        reviews_hash = self._hash_reviews(reviews)

        # 모든 파라미터를 포함한 키 생성
        key_components = [
            f"llm:{llm_name}",
            f"reviews:{reviews_hash}",
            f"focus:{hashlib.md5(focus_instruction.encode()).hexdigest()}",
            f"count:{candidate_count}"
        ]

        key_string = "|".join(key_components)
        cache_key = hashlib.md5(key_string.encode()).hexdigest()

        return cache_key

    def _get_cache_file_path(self, cache_key: str) -> Path:
        """캐시 파일 경로 생성"""
        return self.cache_dir / f"{cache_key}.json"

    def _is_cache_valid(self, cache_file: Path) -> bool:
        """캐시 파일이 유효한지 확인 (TTL 체크)"""
        if not cache_file.exists():
            return False

        try:
            # 파일 수정 시간 확인
            file_mtime = cache_file.stat().st_mtime
            current_time = time.time()

            # TTL 확인
            if current_time - file_mtime > self.ttl_seconds:
                print(f"🕒 캐시 만료: {cache_file.name}")
                return False

            return True
        except Exception as e:
            print(f"⚠️  캐시 파일 검증 실패: {e}")
            return False

    def get_cached_result(
            self,
            llm_name: str,
            reviews: List[Dict],
            focus_instruction: str,
            candidate_count: int
    ) -> Optional[List[Dict]]:
        """캐시된 결과를 가져옵니다"""
        try:
            cache_key = self._generate_cache_key(llm_name, reviews, focus_instruction, candidate_count)
            cache_file = self._get_cache_file_path(cache_key)

            if not self._is_cache_valid(cache_file):
                return None

            with open(cache_file, 'r', encoding='utf-8') as f:
                cache_data = json.load(f)

            # 캐시 메타데이터 확인
            if cache_data.get('version') != '1.0':
                print(f"⚠️  캐시 버전 불일치: {cache_file.name}")
                return None

            cached_result = cache_data.get('result')
            cache_info = cache_data.get('metadata', {})

            print(f"💾 캐시 히트: {cache_key[:8]}... "
                  f"(생성: {cache_info.get('created_at', 'unknown')})")

            return cached_result

        except Exception as e:
            print(f"❌ 캐시 읽기 실패: {e}")
            return None

    def save_result(
            self,
            llm_name: str,
            reviews: List[Dict],
            focus_instruction: str,
            candidate_count: int,
            result: List[Dict]
    ) -> None:
        """결과를 캐시에 저장합니다"""
        try:
            cache_key = self._generate_cache_key(llm_name, reviews, focus_instruction, candidate_count)
            cache_file = self._get_cache_file_path(cache_key)

            # 캐시 데이터 구성
            cache_data = {
                'version': '1.0',
                'metadata': {
                    'cache_key': cache_key,
                    'created_at': datetime.now().isoformat(),
                    'llm_name': llm_name,
                    'reviews_count': len(reviews),
                    'candidate_count': candidate_count,
                    'focus_hash': hashlib.md5(focus_instruction.encode()).hexdigest()[:8]
                },
                'result': result
            }

            # 원자적 쓰기 (임시 파일 사용)
            temp_file = cache_file.with_suffix('.tmp')
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, ensure_ascii=False, indent=2, default=json_serializer)

            # 임시 파일을 실제 캐시 파일로 이동
            temp_file.rename(cache_file)

            print(f"💾 캐시 저장: {cache_key[:8]}... "
                  f"(리뷰: {len(reviews)}개, LLM: {llm_name})")

        except Exception as e:
            print(f"❌ 캐시 저장 실패: {e}")

    def clear_expired_cache(self) -> int:
        """만료된 캐시 파일들을 정리합니다"""
        cleared_count = 0
        try:
            for cache_file in self.cache_dir.glob("*.json"):
                if not self._is_cache_valid(cache_file):
                    cache_file.unlink()
                    cleared_count += 1

            if cleared_count > 0:
                print(f"🧹 만료된 캐시 {cleared_count}개 정리 완료")

        except Exception as e:
            print(f"❌ 캐시 정리 실패: {e}")

        return cleared_count

    def get_cache_info(self) -> Dict[str, Any]:
        """캐시 상태 정보를 반환합니다"""
        try:
            cache_files = list(self.cache_dir.glob("*.json"))
            valid_files = [f for f in cache_files if self._is_cache_valid(f)]
            expired_files = [f for f in cache_files if not self._is_cache_valid(f)]

            total_size = sum(f.stat().st_size for f in cache_files)

            return {
                'cache_dir': str(self.cache_dir),
                'total_files': len(cache_files),
                'valid_files': len(valid_files),
                'expired_files': len(expired_files),
                'total_size_mb': round(total_size / (1024 * 1024), 2),
                'ttl_hours': self.ttl_seconds / 3600
            }

        except Exception as e:
            print(f"❌ 캐시 정보 조회 실패: {e}")
            return {}


# 전역 캐시 인스턴스
_cache_instance = None


def get_cache() -> LLMQueryCache:
    """전역 캐시 인스턴스를 가져옵니다"""
    global _cache_instance
    if _cache_instance is None:
        _cache_instance = LLMQueryCache()
    return _cache_instance


def clear_cache() -> int:
    """전역 캐시를 정리합니다"""
    cache = get_cache()
    return cache.clear_expired_cache()


def get_cache_stats() -> Dict[str, Any]:
    """캐시 통계를 가져옵니다"""
    cache = get_cache()
    return cache.get_cache_info()


if __name__ == "__main__":
    # 테스트 코드
    cache = LLMQueryCache()

    # 테스트 데이터
    test_reviews = [
        {'id': 1, 'text': 'Great product!', 'createdAt': '2024-01-01'},
        {'id': 2, 'text': 'Amazing quality', 'createdAt': '2024-01-02'}
    ]

    test_result = [
        {'id': 1, 'score': 95, 'text': 'Great product!'}
    ]

    # 캐시 저장 테스트
    cache.save_result(
        llm_name="gpt-3.5-turbo",
        reviews=test_reviews,
        focus_instruction="Select best reviews",
        candidate_count=3,
        result=test_result
    )

    # 캐시 읽기 테스트
    cached = cache.get_cached_result(
        llm_name="gpt-3.5-turbo",
        reviews=test_reviews,
        focus_instruction="Select best reviews",
        candidate_count=3
    )

    print("캐시 테스트 결과:", cached)
    print("캐시 정보:", cache.get_cache_info())
