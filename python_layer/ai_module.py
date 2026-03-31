"""
ai_module.py — SINGULARITY ENGINE Symbolic AI Layer
=====================================================
Wraps SymPy to provide symbolic mathematics capabilities:

  • symbolic_diff(expr_str, var)  — differentiate an expression
  • symbolic_simplify(expr_str)   — algebraically simplify
  • symbolic_integrate(expr_str)  — indefinite integral
  • symbolic_expand(expr_str)     — expand products / powers
  • symbolic_factor(expr_str)     — factor polynomials
  • evaluate_symbolic(expr_str, substitutions) — substitute & evaluate

All functions accept plain strings and return (result_string, sympy_expr)
so callers can choose either the human-readable string or the SymPy object.
"""

from __future__ import annotations

import logging
from typing import Dict, Optional, Tuple, Union

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────
#  SymPy import with helpful error
# ─────────────────────────────────────────────────────────────────────
try:
    import sympy as sp
    from sympy.parsing.sympy_parser import (
        parse_expr,
        standard_transformations,
        implicit_multiplication_application,
    )
    _SYMPY_AVAILABLE = True
except ImportError:
    _SYMPY_AVAILABLE = False
    logger.error(
        "SymPy is not installed. Run:  pip install sympy\n"
        "Symbolic operations will raise RuntimeError until SymPy is available."
    )

# ─────────────────────────────────────────────────────────────────────
#  Parser configuration
# ─────────────────────────────────────────────────────────────────────
_TRANSFORMATIONS = (
    standard_transformations
    + (implicit_multiplication_application,)
) if _SYMPY_AVAILABLE else None


# ─────────────────────────────────────────────────────────────────────
#  Internal helpers
# ─────────────────────────────────────────────────────────────────────

def _require_sympy() -> None:
    if not _SYMPY_AVAILABLE:
        raise RuntimeError(
            "SymPy is required for symbolic operations. "
            "Install it with:  pip install sympy"
        )


def _parse(expr_str: str) -> "sp.Expr":
    """
    Parse a string into a SymPy expression.
    Handles ^ → ** substitution and implicit multiplication.
    """
    # Allow ^ as exponentiation operator (same as the C engine)
    normalised = expr_str.replace("^", "**")
    return parse_expr(normalised, transformations=_TRANSFORMATIONS)


def _format(expr: "sp.Expr") -> str:
    """Return a clean string representation of a SymPy expression."""
    return str(sp.pretty(expr, use_unicode=True))


# ─────────────────────────────────────────────────────────────────────
#  Public API
# ─────────────────────────────────────────────────────────────────────

def symbolic_diff(
    expr_str: str,
    var: str = "x",
    order: int = 1,
) -> Tuple[str, "sp.Expr"]:
    """
    Differentiate `expr_str` with respect to `var` (`order` times).

    Returns:
        (pretty_string, sympy_expression)

    Example:
        symbolic_diff("x^3 + sin(x)")  →  ("3*x**2 + cos(x)", ...)
    """
    _require_sympy()
    sym   = sp.Symbol(var)
    expr  = _parse(expr_str)
    deriv = sp.diff(expr, sym, order)
    deriv = sp.simplify(deriv)
    logger.debug("[ai] diff(%s, %s, order=%d) = %s", expr_str, var, order, deriv)
    return str(deriv), deriv


def symbolic_simplify(expr_str: str) -> Tuple[str, "sp.Expr"]:
    """
    Algebraically simplify `expr_str`.

    Returns:
        (pretty_string, sympy_expression)

    Example:
        symbolic_simplify("(x^2 - 1) / (x - 1)")  →  ("x + 1", ...)
    """
    _require_sympy()
    expr       = _parse(expr_str)
    simplified = sp.simplify(expr)
    logger.debug("[ai] simplify(%s) = %s", expr_str, simplified)
    return str(simplified), simplified


def symbolic_integrate(
    expr_str: str,
    var: str = "x",
) -> Tuple[str, "sp.Expr"]:
    """
    Compute the indefinite integral of `expr_str` with respect to `var`.

    Returns:
        (pretty_string, sympy_expression)

    Example:
        symbolic_integrate("x^2")  →  ("x**3/3", ...)
    """
    _require_sympy()
    sym      = sp.Symbol(var)
    expr     = _parse(expr_str)
    integral = sp.integrate(expr, sym)
    logger.debug("[ai] integrate(%s, %s) = %s", expr_str, var, integral)
    return str(integral), integral


def symbolic_expand(expr_str: str) -> Tuple[str, "sp.Expr"]:
    """
    Expand products and powers in `expr_str`.

    Example:
        symbolic_expand("(x + 1)^3")  →  ("x**3 + 3*x**2 + 3*x + 1", ...)
    """
    _require_sympy()
    expr     = _parse(expr_str)
    expanded = sp.expand(expr)
    logger.debug("[ai] expand(%s) = %s", expr_str, expanded)
    return str(expanded), expanded


def symbolic_factor(expr_str: str) -> Tuple[str, "sp.Expr"]:
    """
    Factor a polynomial expression.

    Example:
        symbolic_factor("x^2 - 1")  →  ("(x - 1)*(x + 1)", ...)
    """
    _require_sympy()
    expr      = _parse(expr_str)
    factored  = sp.factor(expr)
    logger.debug("[ai] factor(%s) = %s", expr_str, factored)
    return str(factored), factored


def evaluate_symbolic(
    expr_str: str,
    substitutions: Optional[Dict[str, Union[int, float]]] = None,
) -> Tuple[str, "sp.Expr"]:
    """
    Substitute values into a symbolic expression and evaluate numerically.

    Args:
        expr_str      : expression string, e.g. "x^2 + y"
        substitutions : dict of {variable_name: value}, e.g. {"x": 3, "y": 4}

    Returns:
        (result_string, sympy_expression)

    Example:
        evaluate_symbolic("x^2 + y", {"x": 3, "y": 4})  →  ("13", ...)
    """
    _require_sympy()
    expr = _parse(expr_str)
    if substitutions:
        subs_map = {sp.Symbol(k): v for k, v in substitutions.items()}
        expr = expr.subs(subs_map)
    result = sp.nsimplify(expr, rational=True)
    logger.debug("[ai] eval_symbolic(%s, %s) = %s", expr_str, substitutions, result)
    return str(result), result


def symbolic_latex(expr_str: str) -> str:
    """
    Return the LaTeX representation of an expression.
    Useful for documentation or rendering in Jupyter notebooks.
    """
    _require_sympy()
    expr = _parse(expr_str)
    return sp.latex(expr)
