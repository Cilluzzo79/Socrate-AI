"""
Cost-Optimized Cache Manager for RAG System
Provides embedding and result caching to reduce latency and costs
"""

import logging
import hashlib
import json
import numpy as np
from typing import Optional, Any, Dict
import os

logger = logging.getLogger(__name__)

# Try to import redis
try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    logger.warning("Redis not available, caching disabled")


class CacheManager:
    """
    Unified cache manager for embeddings and query results

    Features:
    - Embedding cache: Store query embeddings (768-dim vectors)
    - Result cache: Store full query results (answer + sources)
    - Automatic TTL (time-to-live)
    - Fallback to no-cache if Redis unavailable
    """

    def __init__(self, redis_url: Optional[str] = None, ttl_seconds: int = 3600):
        """
        Initialize cache manager

        Args:
            redis_url: Redis connection URL (reads from env if not provided)
            ttl_seconds: Time-to-live for cache entries (default: 1 hour)
        """
        self.redis_client = None
        self.ttl = ttl_seconds
        self.enabled = False

        if not REDIS_AVAILABLE:
            logger.warning("[CACHE] Redis not installed, caching disabled")
            return

        # Get Redis URL from env or parameter
        redis_url = redis_url or os.getenv('REDIS_URL')

        if not redis_url:
            logger.warning("[CACHE] No REDIS_URL found, caching disabled")
            return

        try:
            self.redis_client = redis.Redis.from_url(
                redis_url,
                decode_responses=False,  # We store binary data (embeddings)
                socket_connect_timeout=2,
                socket_timeout=2
            )

            # Test connection
            self.redis_client.ping()
            self.enabled = True
            logger.info(f"[CACHE] Initialized successfully (TTL: {ttl_seconds}s)")

        except Exception as e:
            logger.warning(f"[CACHE] Failed to connect to Redis: {e}, caching disabled")
            self.redis_client = None
            self.enabled = False

    def _normalize_query(self, query: str) -> str:
        """Normalize query for consistent cache keys"""
        return query.lower().strip()

    def _make_cache_key(self, prefix: str, query: str, doc_id: Optional[str] = None) -> str:
        """
        Generate cache key from query (and optionally doc_id)

        Args:
            prefix: Cache key prefix (e.g., 'emb', 'result')
            query: User query
            doc_id: Optional document ID

        Returns:
            Cache key string
        """
        normalized = self._normalize_query(query)

        # Include doc_id in hash if provided
        if doc_id:
            to_hash = f"{normalized}:{doc_id}"
        else:
            to_hash = normalized

        # MD5 hash for compact key
        hash_hex = hashlib.md5(to_hash.encode('utf-8')).hexdigest()

        return f"{prefix}:{hash_hex}"

    # ========================================================================
    # EMBEDDING CACHE
    # ========================================================================

    def get_embedding(self, query: str) -> Optional[np.ndarray]:
        """
        Get cached query embedding

        Args:
            query: User query

        Returns:
            Embedding array (768-dim) or None if cache miss
        """
        if not self.enabled:
            return None

        try:
            cache_key = self._make_cache_key('emb', query)
            cached = self.redis_client.get(cache_key)

            if cached:
                # Deserialize numpy array from bytes
                embedding = np.frombuffer(cached, dtype=np.float32)
                logger.debug(f"[CACHE HIT] Embedding for query: {query[:50]}...")
                return embedding

            logger.debug(f"[CACHE MISS] Embedding for query: {query[:50]}...")
            return None

        except Exception as e:
            logger.warning(f"[CACHE ERROR] Failed to get embedding: {e}")
            return None

    def set_embedding(self, query: str, embedding: np.ndarray) -> bool:
        """
        Cache query embedding

        Args:
            query: User query
            embedding: Embedding array (768-dim)

        Returns:
            True if cached successfully, False otherwise
        """
        if not self.enabled:
            return False

        try:
            cache_key = self._make_cache_key('emb', query)

            # Serialize numpy array to bytes
            embedding_bytes = embedding.astype(np.float32).tobytes()

            # Store with TTL
            self.redis_client.setex(cache_key, self.ttl, embedding_bytes)

            logger.debug(f"[CACHE SET] Embedding for query: {query[:50]}...")
            return True

        except Exception as e:
            logger.warning(f"[CACHE ERROR] Failed to set embedding: {e}")
            return False

    # ========================================================================
    # RESULT CACHE
    # ========================================================================

    def get_result(self, query: str, doc_id: str) -> Optional[Dict[str, Any]]:
        """
        Get cached query result

        Args:
            query: User query
            doc_id: Document ID

        Returns:
            Cached result dict or None if cache miss
        """
        if not self.enabled:
            return None

        try:
            cache_key = self._make_cache_key('result', query, doc_id)
            cached = self.redis_client.get(cache_key)

            if cached:
                # Deserialize JSON
                result = json.loads(cached.decode('utf-8'))
                logger.info(f"[CACHE HIT] Result for query on doc {doc_id}: {query[:50]}...")
                return result

            logger.debug(f"[CACHE MISS] Result for query on doc {doc_id}: {query[:50]}...")
            return None

        except Exception as e:
            logger.warning(f"[CACHE ERROR] Failed to get result: {e}")
            return None

    def set_result(self, query: str, doc_id: str, result: Dict[str, Any]) -> bool:
        """
        Cache query result

        Args:
            query: User query
            doc_id: Document ID
            result: Result dictionary (answer, sources, metadata)

        Returns:
            True if cached successfully, False otherwise
        """
        if not self.enabled:
            return False

        try:
            cache_key = self._make_cache_key('result', query, doc_id)

            # Serialize to JSON
            result_json = json.dumps(result, ensure_ascii=False)

            # Store with shorter TTL for results (refresh more often)
            result_ttl = min(self.ttl, 1800)  # Max 30 minutes for results
            self.redis_client.setex(cache_key, result_ttl, result_json.encode('utf-8'))

            logger.info(f"[CACHE SET] Result for query on doc {doc_id}: {query[:50]}...")
            return True

        except Exception as e:
            logger.warning(f"[CACHE ERROR] Failed to set result: {e}")
            return False

    # ========================================================================
    # CACHE MANAGEMENT
    # ========================================================================

    def clear_cache(self, pattern: Optional[str] = None) -> int:
        """
        Clear cache entries

        Args:
            pattern: Optional pattern to match keys (e.g., 'emb:*', 'result:*')
                    If None, clears all cache

        Returns:
            Number of keys deleted
        """
        if not self.enabled:
            return 0

        try:
            if pattern:
                # Find matching keys
                keys = self.redis_client.keys(pattern)
            else:
                # Clear all (use with caution!)
                keys = self.redis_client.keys('emb:*') + self.redis_client.keys('result:*')

            if keys:
                deleted = self.redis_client.delete(*keys)
                logger.info(f"[CACHE CLEAR] Deleted {deleted} keys")
                return deleted
            else:
                logger.info("[CACHE CLEAR] No keys found to delete")
                return 0

        except Exception as e:
            logger.warning(f"[CACHE ERROR] Failed to clear cache: {e}")
            return 0

    def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics

        Returns:
            Dict with cache stats (keys count, memory usage, etc.)
        """
        if not self.enabled:
            return {'enabled': False, 'message': 'Cache disabled'}

        try:
            info = self.redis_client.info('stats')

            # Count keys by prefix
            emb_keys = len(self.redis_client.keys('emb:*'))
            result_keys = len(self.redis_client.keys('result:*'))

            return {
                'enabled': True,
                'embedding_keys': emb_keys,
                'result_keys': result_keys,
                'total_keys': emb_keys + result_keys,
                'keyspace_hits': info.get('keyspace_hits', 0),
                'keyspace_misses': info.get('keyspace_misses', 0),
                'hit_rate': self._calculate_hit_rate(info)
            }

        except Exception as e:
            logger.warning(f"[CACHE ERROR] Failed to get stats: {e}")
            return {'enabled': True, 'error': str(e)}

    def _calculate_hit_rate(self, info: Dict) -> float:
        """Calculate cache hit rate from Redis info"""
        hits = info.get('keyspace_hits', 0)
        misses = info.get('keyspace_misses', 0)

        total = hits + misses
        if total == 0:
            return 0.0

        return hits / total


# Singleton instance
_cache_manager_instance: Optional[CacheManager] = None


def get_cache_manager(redis_url: Optional[str] = None, ttl_seconds: int = 3600) -> CacheManager:
    """
    Get singleton cache manager instance

    Args:
        redis_url: Redis URL (only used on first call)
        ttl_seconds: Cache TTL (only used on first call)

    Returns:
        CacheManager instance
    """
    global _cache_manager_instance

    if _cache_manager_instance is None:
        _cache_manager_instance = CacheManager(redis_url=redis_url, ttl_seconds=ttl_seconds)

    return _cache_manager_instance
