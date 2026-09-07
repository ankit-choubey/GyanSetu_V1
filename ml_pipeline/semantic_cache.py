"""
ml_pipeline/semantic_cache.py — Distributed Redis Semantic Caching Layer.

Provides high-speed, cost-saving semantic caching for Groq LLM inference:
1. Generates deterministic SHA-256 keys over normalized content, competency, and difficulty.
2. Connects to Redis via connection pool with configurable TTL (default 24h).
3. Features automatic, thread-safe In-Memory LRU Cache fallback if Redis is offline.
4. Tracks telemetry: hits, misses, hit ratio, and latency saved.
"""
from __future__ import annotations

from collections import OrderedDict
import hashlib
import json
import os
import threading
import time
from typing import Any, Dict, Optional

# Optional dependency: redis
try:
    import redis
    _REDIS_AVAILABLE = True
except ImportError:
    _REDIS_AVAILABLE = False


class InMemoryLRUCache:
    """Thread-safe in-memory LRU cache fallback."""

    def __init__(self, maxsize: int = 1000):
        self.maxsize = maxsize
        self._cache: OrderedDict[str, tuple[Any, float]] = OrderedDict()
        self._lock = threading.Lock()

    def get(self, key: str) -> Optional[Any]:
        with self._lock:
            if key not in self._cache:
                return None
            val, expiry = self._cache[key]
            if expiry > 0 and time.time() > expiry:
                del self._cache[key]
                return None
            self._cache.move_to_end(key)
            return val

    def set(self, key: str, value: Any, ttl: int = 86400) -> bool:
        with self._lock:
            expiry = (time.time() + ttl) if ttl > 0 else 0.0
            if key in self._cache:
                self._cache.move_to_end(key)
            self._cache[key] = (value, expiry)
            if len(self._cache) > self.maxsize:
                self._cache.popitem(last=False)
            return True

    def clear(self) -> bool:
        with self._lock:
            self._cache.clear()
            return True


class SemanticCache:
    """Production Redis caching manager with in-memory LRU fallback."""

    def __init__(
        self,
        redis_url: Optional[str] = None,
        default_ttl: int = 86400,
        enable_in_memory_fallback: bool = True,
    ):
        self.default_ttl = default_ttl
        self.enable_in_memory_fallback = enable_in_memory_fallback
        self.redis_client: Optional[redis.Redis] = None
        self.in_memory = InMemoryLRUCache(maxsize=1000)

        # Telemetry metrics
        self.hits = 0
        self.misses = 0
        self.latency_saved_sec = 0.0

        target_url = redis_url or os.environ.get("REDIS_URL", "redis://localhost:6379/0")

        if _REDIS_AVAILABLE:
            try:
                client = redis.Redis.from_url(
                    target_url,
                    socket_connect_timeout=0.5,
                    socket_timeout=0.5,
                    decode_responses=True,
                )
                client.ping()
                self.redis_client = client
            except Exception:
                self.redis_client = None

    @property
    def is_redis_active(self) -> bool:
        """Returns True if connected to live Redis instance."""
        if not self.redis_client:
            return False
        try:
            return bool(self.redis_client.ping())
        except Exception:
            return False

    def is_available(self) -> bool:
        """Returns True if Redis is active or in-memory fallback is enabled."""
        return self.is_redis_active or self.enable_in_memory_fallback

    @staticmethod
    def compute_mcq_key(content: str, competency: str, difficulty: str, num_questions: int) -> str:
        """Computes deterministic SHA-256 hash for MCQ generation parameters."""
        norm_content = " ".join(content.lower().split())
        payload = f"mcq:{competency.lower()}:{difficulty.lower()}:{num_questions}:{norm_content}"
        return "gyansetu:mcq:" + hashlib.sha256(payload.encode("utf-8")).hexdigest()

    @staticmethod
    def compute_feedback_key(question: str, selected_letter: str, correct_letter: str) -> str:
        """Computes deterministic SHA-256 hash for personalized cognitive feedback."""
        norm_q = " ".join(question.lower().split())
        payload = f"feedback:{norm_q}:{selected_letter.upper()}:{correct_letter.upper()}"
        return "gyansetu:feedback:" + hashlib.sha256(payload.encode("utf-8")).hexdigest()

    def get(self, key: str) -> Optional[Any]:
        """Retrieves cached item by key, logging telemetry."""
        # 1. Try Redis
        if self.is_redis_active and self.redis_client:
            try:
                raw = self.redis_client.get(key)
                if raw is not None:
                    self.hits += 1
                    self.latency_saved_sec += 2.0  # Average saved Groq LLM latency
                    return json.loads(raw)
            except Exception:
                pass

        # 2. Try In-Memory fallback
        if self.enable_in_memory_fallback:
            val = self.in_memory.get(key)
            if val is not None:
                self.hits += 1
                self.latency_saved_sec += 2.0
                return val

        self.misses += 1
        return None

    def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None,
        ttl_seconds: Optional[int] = None,
    ) -> bool:
        """Stores item into cache with TTL."""
        effective_ttl = ttl_seconds if ttl_seconds is not None else ttl
        target_ttl = effective_ttl if effective_ttl is not None else self.default_ttl
        success = False

        # 1. Store in Redis if available
        if self.is_redis_active and self.redis_client:
            try:
                serialized = json.dumps(value)
                self.redis_client.set(key, serialized, ex=target_ttl)
                success = True
            except Exception:
                pass

        # 2. Store in In-Memory fallback
        if self.enable_in_memory_fallback:
            self.in_memory.set(key, value, ttl=target_ttl)
            success = True

        return success

    def clear(self) -> bool:
        """Flushes cache."""
        cleared = False
        if self.is_redis_active and self.redis_client:
            try:
                keys = self.redis_client.keys("gyansetu:*")
                if keys:
                    self.redis_client.delete(*keys)
                cleared = True
            except Exception:
                pass

        if self.enable_in_memory_fallback:
            self.in_memory.clear()
            cleared = True

        return cleared

    def get_metrics(self) -> Dict[str, Any]:
        """Returns cache telemetry."""
        total = self.hits + self.misses
        ratio = (self.hits / total) if total > 0 else 0.0
        return {
            "hits": self.hits,
            "misses": self.misses,
            "total_queries": total,
            "hit_ratio": round(ratio, 4),
            "backend_type": "redis" if self.is_redis_active else "in_memory",
            "estimated_latency_saved_sec": round(self.latency_saved_sec, 2),
        }


# Singleton shared instance
_global_cache = SemanticCache()


def get_semantic_cache() -> SemanticCache:
    """Returns the shared global SemanticCache instance."""
    global _global_cache
    return _global_cache
