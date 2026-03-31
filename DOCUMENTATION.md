# SINGULARITY ENGINE - Documentation

## VERSION 2.0 (Enhanced)

A production-grade hybrid computational system that bridges the raw performance of C and LLVM JIT with the expressive power of Python's symbolic mathematics ecosystem.

---

## 1. Project Overview

Singularity Engine is designed around a clear evaluation priority chain that ensures maximum speed while maintaining full fallback safety.

### Evaluation Priority Chain

| Priority | Layer | Mechanism | Speed |
|----------|-------|-----------|-------|
| **1st** | JIT Engine | llvmlite LLVM native code | Native (~1ns) |
| **2nd** | Eval Cache | OrderedDict LRU lookup | O(1) hash |
| **3rd** | C Library | ctypes -> libengine.so | ~50-200ns |
| **4th** | Python Eval | Safe eval() fallback | ~1-5µs |

---

## 2. System Requirements

| Component | Minimum | Recommended | Notes |
|-----------|---------|-------------|-------|
| OS | Linux / macOS / Windows | Ubuntu 22.04+ / Windows 11 | MinGW supported on Windows |
| GCC | 9.0 | 12.0+ | Must support -std=c11 -fPIC |
| Python | 3.9 | 3.11+ | |
| SymPy | 1.10 | 1.12+ | `pip install sympy` |
| llvmlite | 0.39 | 0.43+ | `pip install llvmlite` |

---

## 3. C Core Engine

The C engine implements a classical recursive descent parser that is zero-allocation at runtime.

### Supported Syntax

- **Operators**: `+`, `-`, `*`, `/`, `^` (exponentiation, right-associative)
- **Functions**:
    - `sin(x)`, `cos(x)`, `tan(x)`
    - `asin(x)`, `acos(x)`, `atan(x)`
    - `sqrt(x)`
    - `log(x)` (natural log), `log10(x)`
    - `exp(x)`
    - `abs(x)`
    - `floor(x)`, `ceil(x)`, `round(x)`

---

## 4. JIT Engine (Enabled)

The JIT layer is powered by `llvmlite`. It parses expressions into SymPy ASTs, translates them into LLVM IR, and compiles them to native machine code using the MCJIT engine.

### How it works:
1. `bridge.py` requests an evaluation.
2. `jit_engine` checks if the expression is already compiled.
3. If not, it uses SymPy to parse the expression and generates LLVM IR instructions for each node.
4. LLVM compiles this IR into a native function.
5. The function is cached and executed for all subsequent calls with the same expression.

---

## 5. Usage Reference

| Command | Description | Example |
|---------|-------------|---------|
| `setx` | Set the active expression | `setx x^2 + 1` |
| `eval` | Evaluate at x | `eval 3.14` |
| `diff` | Symbolic differentiation | `diff x^3` |
| `intg` | Symbolic integration | `intg sin(x)` |
| `simp` | Algebraic simplification | `simp (x^2-1)/(x-1)` |
| `expa` | Expand products/powers | `expa (x+1)^2` |
| `fact` | Factor polynomial | `fact x^2-1` |
| `latex` | LaTeX representation | `latex x/sqrt(x^2+1)` |
| `cache` | Show cache stats | `cache` |
| `jit`   | Show JIT status | `jit` |
| `help`  | Show help | `help` |
| `exit`  | Exit | `exit` |

---

## 6. Troubleshooting

- **libengine.so not found**: Ensure you ran `make` or `mingw32-make` in `core_c/`.
- **Permission denied (Windows)**: Ensure no other process is using `libengine.so` when compiling.
- **JIT compilation failed**: Check if `llvmlite` is installed and if the expression uses supported functions.
