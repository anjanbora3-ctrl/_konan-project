"""
main.py — SINGULARITY ENGINE Interactive CLI
=============================================
Entry point for the Singularity Engine.

Commands:
  eval  <number>      Evaluate the current expression at x=<number>
  setx  <expression>  Set the active C-engine expression
  diff  <expression>  Symbolic differentiation (SymPy)
  intg  <expression>  Symbolic integration (SymPy)
  simp  <expression>  Symbolic simplification (SymPy)
  expa  <expression>  Symbolic expansion (SymPy)
  fact  <expression>  Symbolic factoring (SymPy)
  latex <expression>  LaTeX rendering of an expression
  cache               Print cache statistics
  jit                 Print JIT engine status
  help                Show this help message
  exit / quit         Exit the engine

Example session:
  > setx x^2 + sin(x)
  > eval 3.14
  > diff x^3 + 2*x
  > simp (x^2 - 1) / (x - 1)
"""

from __future__ import annotations

import os
import sys
import logging

# ─────────────────────────────────────────────────────────────────────
#  Path setup — allow running from any working directory
# ─────────────────────────────────────────────────────────────────────
_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

# ─────────────────────────────────────────────────────────────────────
#  Configure logging (DEBUG for dev, WARNING for production)
# ─────────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.WARNING,
    format="[%(levelname)s] %(name)s: %(message)s",
)

# ─────────────────────────────────────────────────────────────────────
#  Engine imports
# ─────────────────────────────────────────────────────────────────────
from python_layer.bridge     import evaluate, set_expr, cache_stats, jit_status
from python_layer.ai_module  import (
    symbolic_diff,
    symbolic_simplify,
    symbolic_integrate,
    symbolic_expand,
    symbolic_factor,
    symbolic_latex,
)

# ─────────────────────────────────────────────────────────────────────
#  ANSI colours (gracefully degrade on Windows)
# ─────────────────────────────────────────────────────────────────────
_USE_COLOR = sys.stdout.isatty() and os.name != "nt"

def _c(text: str, code: str) -> str:
    return f"\033[{code}m{text}\033[0m" if _USE_COLOR else text

def green(t):  return _c(t, "32")
def cyan(t):   return _c(t, "36")
def yellow(t): return _c(t, "33")
def red(t):    return _c(t, "31")
def bold(t):   return _c(t, "1")

# ─────────────────────────────────────────────────────────────────────
#  Help text
# ─────────────────────────────────────────────────────────────────────
_HELP = """
SINGULARITY ENGINE — Command Reference

  setx  <expression>    Set active expression  (e.g.  setx x^2 + sin(x))
  eval  <number>        Evaluate at x          (e.g.  eval 3.14)
  diff  <expression>    Differentiate          (e.g.  diff x^3 + 2*x)
  intg  <expression>    Integrate              (e.g.  intg x^2)
  simp  <expression>    Simplify               (e.g.  simp (x^2-1)/(x-1))
  expa  <expression>    Expand                 (e.g.  expa (x+1)^4)
  fact  <expression>    Factor                 (e.g.  fact x^2 - 4)
  latex <expression>    LaTeX form             (e.g.  latex sin(x)/x)
  cache                 Show cache statistics
  jit                   Show JIT engine status
  help                  Show this message
  exit / quit           Exit

Supported operators:  +  -  *  /  ^
Supported functions:  sin  cos  tan  sqrt  log  exp  abs
Variable:  x
"""

# ─────────────────────────────────────────────────────────────────────
#  Command dispatcher
# ─────────────────────────────────────────────────────────────────────

def _cmd_eval(arg: str, current_expr: str) -> None:
    if not arg:
        print(red("Usage: eval <number>"))
        return
    try:
        x      = float(arg)
        result = evaluate(x)
        print(green(f"  {current_expr}  @  x = {x}  =>  {result}"))
    except ValueError as exc:
        print(red(f"  Error: {exc}"))


def _cmd_setx(arg: str) -> str:
    if not arg:
        print(red("Usage: setx <expression>"))
        return "x"
    set_expr(arg)
    print(cyan(f"  Expression set: {arg}"))
    return arg


def _cmd_symbolic(cmd: str, arg: str) -> None:
    if not arg:
        print(red(f"Usage: {cmd} <expression>"))
        return
    try:
        if cmd == "diff":
            result, _ = symbolic_diff(arg)
            label = f"d/dx [{arg}]"
        elif cmd == "intg":
            result, _ = symbolic_integrate(arg)
            label = f"integral [{arg}] dx"
        elif cmd == "simp":
            result, _ = symbolic_simplify(arg)
            label = f"simplify({arg})"
        elif cmd == "expa":
            result, _ = symbolic_expand(arg)
            label = f"expand({arg})"
        elif cmd == "fact":
            result, _ = symbolic_factor(arg)
            label = f"factor({arg})"
        elif cmd == "latex":
            result = symbolic_latex(arg)
            label  = f"LaTeX({arg})"
        else:
            print(red(f"Unknown symbolic command: {cmd}"))
            return
        print(f"  {yellow(label)}  =>  {green(result)}")
    except RuntimeError as exc:
        print(red(f"  Symbolic error: {exc}"))
    except Exception as exc:
        print(red(f"  Error: {exc}"))


def _cmd_cache() -> None:
    stats = cache_stats()
    print(cyan("  Cache Statistics:"))
    for k, v in stats.items():
        print(f"    {k:12s}: {v}")


def _cmd_jit() -> None:
    status = jit_status()
    print(cyan("  JIT Engine Status:"))
    for k, v in status.items():
        print(f"    {k:12s}: {v}")

# ─────────────────────────────────────────────────────────────────────
#  Main REPL
# ─────────────────────────────────────────────────────────────────────

def main() -> None:
    print("\n  +==================================+")
    print("  |   SINGULARITY ENGINE  v1.0       |")
    print("  +==================================+")
    print("  Type 'help' for available commands.\n")

    # Default expression loaded into the C engine
    current_expr = "x^2 + 1"
    set_expr(current_expr)
    print(f"  Default expression: {cyan(current_expr)}\n")

    while True:
        try:
            raw = input("singularity> ").strip()
        except (EOFError, KeyboardInterrupt):
            print(f"\n  {yellow('Goodbye.')}")
            break

        if not raw:
            continue

        # Split into command + argument
        parts = raw.split(None, 1)
        cmd   = parts[0].lower()
        arg   = parts[1].strip() if len(parts) > 1 else ""

        # ── Routing ───────────────────────────────────────────────
        if cmd in ("exit", "quit"):
            print(yellow("  Goodbye."))
            break

        elif cmd == "help":
            print(_HELP)

        elif cmd == "eval":
            _cmd_eval(arg, current_expr)

        elif cmd == "setx":
            current_expr = _cmd_setx(arg)

        elif cmd in ("diff", "intg", "simp", "expa", "fact", "latex"):
            _cmd_symbolic(cmd, arg)

        elif cmd == "cache":
            _cmd_cache()

        elif cmd == "jit":
            _cmd_jit()

        else:
            print(red(f"  Unknown command: '{cmd}'.  Type 'help' for options."))


if __name__ == "__main__":
    main()
