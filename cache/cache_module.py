"""
cache_module.py — re-exports EvalCache and default_cache.
See cache.py for the full implementation.
"""
from cache.cache import EvalCache, default_cache   # noqa: F401

__all__ = ["EvalCache", "default_cache"]
