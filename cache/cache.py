"""
cache.py — SINGULARITY ENGINE Result Cache
==========================================
Dictionary-based LRU-style cache for expression evaluations.

Design:
  - Key   : (expression_string, x_value)  — fully qualified cache key
  - Value : numeric result (float)
  - Auto hit/miss detection with counters for diagnostics
  - Optional max-size with LRU eviction (via collections.OrderedDict)
"""

from collections import OrderedDict
from typing import Optional, Tuple

# Type alias for cache keys
CacheKey = Tuple[str, float]


class EvalCache:
    """
    Thread-unsafe (single-process) evaluation cache.
    Set max_size=None for unlimited growth.
    """

    def __init__(self, max_size: int = 1024):
        self._store: OrderedDict[CacheKey, float] = OrderedDict()
        self._max_size = max_size
        self._hits   = 0
        self._misses = 0

    # ------------------------------------------------------------------
    # Core interface
    # ------------------------------------------------------------------

    def get(self, expr: str, x: float) -> Optional[float]:
        """
        Return cached result for (expr, x), or None on cache miss.
        Moves the accessed entry to the end (most-recently-used).
        """
        key: CacheKey = (expr, round(x, 10))   # round to avoid float drift
        if key in self._store:
            self._hits += 1
            self._store.move_to_end(key)         # LRU bookkeeping
            return self._store[key]
        self._misses += 1
        return None

    def put(self, expr: str, x: float, result: float) -> None:
        """
        Store result for (expr, x).
        Evicts the least-recently-used entry when max_size is reached.
        """
        key: CacheKey = (expr, round(x, 10))
        if key in self._store:
            self._store.move_to_end(key)
        else:
            if self._max_size and len(self._store) >= self._max_size:
                # Evict oldest (first) entry
                evicted_key, _ = self._store.popitem(last=False)
            self._store[key] = result

    def invalidate(self, expr: Optional[str] = None) -> int:
        """
        Remove all entries matching expr, or flush everything if expr is None.
        Returns the number of entries removed.
        """
        if expr is None:
            count = len(self._store)
            self._store.clear()
            return count
        keys_to_remove = [k for k in self._store if k[0] == expr]
        for k in keys_to_remove:
            del self._store[k]
        return len(keys_to_remove)

    # ------------------------------------------------------------------
    # Diagnostics
    # ------------------------------------------------------------------

    @property
    def hits(self) -> int:
        return self._hits

    @property
    def misses(self) -> int:
        return self._misses

    @property
    def size(self) -> int:
        return len(self._store)

    @property
    def hit_rate(self) -> float:
        total = self._hits + self._misses
        return self._hits / total if total > 0 else 0.0

    def stats(self) -> dict:
        return {
            "size"    : self.size,
            "hits"    : self._hits,
            "misses"  : self._misses,
            "hit_rate": f"{self.hit_rate:.1%}",
            "max_size": self._max_size,
        }

    def __repr__(self) -> str:
        return (f"EvalCache(size={self.size}, hits={self._hits}, "
                f"misses={self._misses}, max_size={self._max_size})")


# ------------------------------------------------------------------
# Module-level default cache instance (shared across the application)
# ------------------------------------------------------------------
default_cache = EvalCache(max_size=1024)
