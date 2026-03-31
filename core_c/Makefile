# ============================================================
#  SINGULARITY ENGINE — C Core Makefile
#  Targets:
#    make          → build libengine.so (shared library)
#    make test     → build & run standalone test binary
#    make clean    → remove build artefacts
# ============================================================

CC      = gcc
CFLAGS  = -O2 -Wall -Wextra -fPIC -std=c11
LDFLAGS = -shared
LIBS    = -lm

SRC     = engine.c
OBJ     = engine.o
TARGET  = libengine.so

.PHONY: all test clean

# Default: build shared library
all: $(TARGET)

$(TARGET): $(OBJ)
	$(CC) $(LDFLAGS) -o $@ $^ $(LIBS)
	@echo "[OK] Built $(TARGET)"

$(OBJ): $(SRC) engine.h
	$(CC) $(CFLAGS) -c -o $@ $<

# Build and run a quick self-test
test: engine.c engine.h
	$(CC) $(CFLAGS) -DTEST_MAIN -o engine_test engine.c $(LIBS)
	@echo "[OK] Running self-test..."
	./engine_test

clean:
	rm -f $(OBJ) $(TARGET) engine_test
	@echo "[OK] Cleaned"
