# SINGULARITY ENGINE

A high-performance hybrid computational engine combining:
- **C math core**: Recursive descent parser with extended function support.
- **Symbolic AI**: Powered by SymPy for differentiation, integration, and more.
- **LLVM JIT**: Native machine code compilation for hot expressions via `llvmlite`.
- **LRU Cache**: Multi-tier evaluation cache (JIT -> EvalCache -> C -> Python).

---

## Architecture

```
singularity_engine/
├── core_c/          C expression evaluator  →  libengine.so
├── python_layer/    Bridge (ctypes) + SymPy AI + CLI
├── cache/           LRU evaluation cache
├── jit_layer/       LLVM JIT Engine (powered by llvmlite)
└── README.md
```

**Evaluation priority:**
1. **JIT Cache**: Native machine code (Fastest)
2. **Eval Cache**: LRU Dictionary lookup
3. **C Library**: Compiled C evaluator (via ctypes)
4. **Python Fallback**: Limited `eval()` (Last resort)

---

## Requirements

| Component  | Requirement                          |
|------------|--------------------------------------|
| OS         | Linux, macOS, or Windows (MinGW/WSL2)|
| C compiler | gcc >= 9                             |
| Python     | >= 3.9                               |
| SymPy      | `pip install sympy`                  |
| llvmlite   | `pip install llvmlite` (Enabled!)    |

---

## Setup

### 1 — Install Python dependencies

```bash
pip install sympy llvmlite
```

### 2 — Compile the C shared library

**On Linux/macOS:**
```bash
cd core_c
make
```

**On Windows (MinGW):**
```bash
cd core_c
mingw32-make
```

### 3 — Run the interactive CLI

```bash
python -m python_layer.main
```

---

## Supported Syntax

- **Operators**: `+`, `-`, `*`, `/`, `^` (exponentiation)
- **Functions**: `sin`, `cos`, `tan`, `asin`, `acos`, `atan`, `sqrt`, `log` (ln), `log10`, `exp`, `abs`, `floor`, `ceil`, `round`
- **Variable**: `x`

---

## Example Session

```
singularity> setx x^2 + sin(x)
singularity> eval 3.14
  [JIT] Successfully compiled 'x^2 + sin(x)' to native code.
  x^2 + sin(x)  @  x = 3.14  =>  9.8611...

singularity> diff x^3 + 2*x
  d/dx [x^3 + 2*x]  =>  3*x**2 + 2

singularity> cache
  Cache Statistics:
    size        : 1
    hits        : 0
    misses      : 1
    ...
```

---

## JIT Engine

The JIT engine uses `llvmlite` to translate expressions into LLVM IR and compile them to native machine code at runtime. This bypasses the overhead of the C parser and Python interpreter for repeated evaluations.

---

## License
MIT
