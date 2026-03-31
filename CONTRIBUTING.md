# Contributing to Singularity Engine

Welcome! We are excited that you want to contribute to the Singularity Engine.

## Development Setup

1. **Clone the repository**:
   ```bash
   git clone https://github.com/anjanbora3-ctrl/_konan-project.git
   cd _konan-project
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Build the C Core**:
   - **Linux/macOS**: `cd core_c && make`
   - **Windows**: `cd core_c && mingw32-make`

## Running Tests

We use `pytest` for integration tests and `make test` for C core tests.

```bash
# C Core tests
cd core_c && make test

# Integration tests
cd ..
python -m pytest tests/test_engine.py
```

## Coding Standards

- **C Code**: Follow C11 standards. Keep the parser zero-allocation.
- **Python Code**: Follow PEP 8. Ensure type hints are used where appropriate.
- **JIT**: When adding new functions, ensure they have equivalent LLVM IR emitters in `jit_layer/jit_stub.py`.

## Pull Request Process

1. Create a new branch for your feature or bugfix.
2. Ensure all tests pass locally.
3. Update documentation if you add new features or functions.
4. Submit a Pull Request to the `main` branch.

---
MIT License
