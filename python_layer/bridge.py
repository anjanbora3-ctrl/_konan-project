"""
bridge.py — SINGULARITY ENGINE C Bridge
========================================
Loads the compiled C shared library (libengine.so) via ctypes and
exposes a clean Python API for expression evaluation.

Evaluation priority:
  1. JIT-compiled native function (if llvmlite available)
  2. Cache hit (dictionary lookup — O(1))
  3. C shared library via ctypes
  4. Pure-Python fallback (eval — limited, last resort)

Usage:
    from bridge import evaluate, set_expr

    set_expr("x^2 + sin(x)")
    result = evaluate(3.14)
"""

from __future__ import annotations

import ctypes
import os
import sys
import logging
from typing import Optional

# Adjust Python path so sibling packages are importable
_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from cache.cache_module import default_cache
from jit_layer.jit_stub  import jit_engine

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────
#  Constants
# ─────────────────────────────────────────────────────────────────────
_LIB_NAME    = "libengine.so"
_LIB_SEARCH  = [
    os.path.join(_ROOT, "core_c", _LIB_NAME),
    os.path.join(_HERE, _LIB_NAME),
    _LIB_NAME,                                # system ld path
]


# ─────────────────────────────────────────────────────────────────────
#  Load the shared library
# ─────────────────────────────────────────────────────────────────────

def _load_library() -> Optional[ctypes.CDLL]:
    """
    Attempt to load libengine.so from known locations.
    Returns the loaded library or None if unavailable.
    """
    for path in _LIB_SEARCH:
        if os.path.isfile(path):
            try:
                lib = ctypes.CDLL(path)
                _configure_signatures(lib)
                logger.info("[bridge] Loaded C engine from: %s", path)
                return lib
            except OSError as exc:
                logger.warning("[bridge] Failed to load '%s': %s", path, exc)
    logger.warning(
        "[bridge] libengine.so not found. Run 'make' in core_c/. "
        "Using Python fallback."
    )
    return None


def _configure_signatures(lib: ctypes.CDLL) -> None:
    """Define argument and return types for each exported C function."""

    # void set_expression(const char* expr)
    lib.set_expression.argtypes = [ctypes.c_char_p]
    lib.set_expression.restype  = None

    # double eval_expr(double x)
    lib.eval_expr.argtypes = [ctypes.c_double]
    lib.eval_expr.restype  = ctypes.c_double

    # double eval_expr_str(const char* expr, double x)
    lib.eval_expr_str.argtypes = [ctypes.c_char_p, ctypes.c_double]
    lib.eval_expr_str.restype  = ctypes.c_double

    # const char* get_last_error(void)
    lib.get_last_error.argtypes = []
    lib.get_last_error.restype  = ctypes.c_char_p


# Module-level library handle (None = unavailable)
_lib: Optional[ctypes.CDLL] = _load_library()

# Currently active expression string (kept in Python for cache keying)
_current_expr: str = "x"


# ─────────────────────────────────────────────────────────────────────
#  Public API
# ─────────────────────────────────────────────────────────────────────

def set_expr(expr: str) -> None:
    """
    Set the expression to be evaluated.
    This is propagated to the C engine and cached for future lookups.
    """
    global _current_expr
    _current_expr = expr.strip()
    if _lib is not None:
        _lib.set_expression(_current_expr.encode("utf-8"))
    logger.debug("[bridge] Expression set: '%s'", _current_expr)


def evaluate(x: float, expr: Optional[str] = None) -> float:
    """
    Evaluate the current (or given) expression at x.

    Priority:
      1. JIT cache
      2. Eval cache
      3. C library
      4. Python fallback

    Args:
        x    : the numeric value to substitute for the variable 'x'
        expr : optional expression string (overrides set_expr)

    Returns:
        float result
    """
    target_expr = (expr.strip() if expr else _current_expr)

    # ── 1. JIT path ────────────────────────────────────────────────
    jit_result = jit_engine.evaluate(target_expr, x)
    if jit_result is not None:
        logger.debug("[bridge] JIT hit for '%s' @ x=%g => %g", target_expr, x, jit_result)
        return jit_result

    # ── 2. Cache path ──────────────────────────────────────────────
    cached = default_cache.get(target_expr, x)
    if cached is not None:
        logger.debug("[bridge] Cache hit for '%s' @ x=%g => %g", target_expr, x, cached)
        return cached

    # ── 3. C library path ─────────────────────────────────────────
    result: float
    if _lib is not None:
        result = _lib.eval_expr_str(target_expr.encode("utf-8"), ctypes.c_double(x))
        err = _lib.get_last_error().decode("utf-8")
        if err:
            raise ValueError(f"C engine error: {err}")
    else:
        # ── 4. Python fallback (limited safety) ───────────────────
        logger.warning("[bridge] Using Python eval fallback for '%s'", target_expr)
        result = _python_eval_fallback(target_expr, x)

    # Store in cache
    default_cache.put(target_expr, x, result)
    return result


def get_error() -> str:
    """Return the last error from the C engine (empty string = no error)."""
    if _lib is not None:
        return _lib.get_last_error().decode("utf-8")
    return ""


def cache_stats() -> dict:
    """Return evaluation cache statistics."""
    return default_cache.stats()


def jit_status() -> dict:
    """Return JIT engine status."""
    return jit_engine.status()


# ─────────────────────────────────────────────────────────────────────
#  Python fallback evaluator
# ─────────────────────────────────────────────────────────────────────

def _python_eval_fallback(expr: str, x: float) -> float:
    """
    Very limited Python eval-based fallback.
    Only safe when the C library is unavailable.
    Supports basic arithmetic and math functions.
    """
    import math
    safe_env = {
        "__builtins__": {},
        "x"   : x,
        "sin" : math.sin,  "cos" : math.cos,  "tan" : math.tan,
        "sqrt": math.sqrt, "log" : math.log,   "exp" : math.exp,
        "abs" : abs,       "pi"  : math.pi,    "e"   : math.e,
    }
    # Replace ^ with ** for Python compatibility
    py_expr = expr.replace("^", "**")
    try:
        return float(eval(py_expr, safe_env))  # noqa: S307
    except Exception as exc:
        raise ValueError(f"Python fallback eval failed: {exc}") from exc
