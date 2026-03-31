/*
 * SINGULARITY ENGINE - C Core Expression Evaluator
 *
 * Implements a recursive descent parser for math expressions.
 * Supports: +, -, *, /, ^ (exponentiation), unary minus, parentheses,
 *           the variable 'x', and common functions: sin, cos, tan, sqrt, log, exp, abs
 *
 * Grammar:
 *   expr    := term (('+' | '-') term)*
 *   term    := factor (('*' | '/') factor)*
 *   factor  := base ('^' factor)?          (right-associative)
 *   base    := NUMBER | 'x' | '(' expr ')' | FUNC '(' expr ')' | '-' base
 *
 * Compiled as a shared library: libengine.so
 */

#include "engine.h"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <ctype.h>
#include <stdarg.h>

/* ------------------------------------------------------------------ */
/* Internal parser state                                                */
/* ------------------------------------------------------------------ */

static char  g_expr[MAX_EXPR_LEN];   /* current expression string     */
static int   g_pos;                   /* current parse position        */
static double g_x;                    /* current value of x            */
static char  g_error[256];            /* last error message            */

/* ------------------------------------------------------------------ */
/* Error helpers                                                        */
/* ------------------------------------------------------------------ */

static void set_error(const char* fmt, ...) {
    va_list ap;
    va_start(ap, fmt);
    vsnprintf(g_error, sizeof(g_error), fmt, ap);
    va_end(ap);
}

const char* get_last_error(void) {
    return g_error;
}

/* ------------------------------------------------------------------ */
/* Lexer helpers                                                        */
/* ------------------------------------------------------------------ */

static void skip_whitespace(void) {
    while (g_expr[g_pos] && isspace((unsigned char)g_expr[g_pos]))
        g_pos++;
}

static char peek(void) {
    skip_whitespace();
    return g_expr[g_pos];
}

static char consume(void) {
    skip_whitespace();
    return g_expr[g_pos++];
}

/* ------------------------------------------------------------------ */
/* Forward declarations                                                 */
/* ------------------------------------------------------------------ */

static double parse_expr(void);
static double parse_term(void);
static double parse_factor(void);
static double parse_base(void);

/* ------------------------------------------------------------------ */
/* Parser implementation                                                */
/* ------------------------------------------------------------------ */

/*
 * parse_expr: handles addition and subtraction (lowest precedence)
 */
static double parse_expr(void) {
    double result = parse_term();

    while (1) {
        char c = peek();
        if (c == '+') {
            consume();
            result += parse_term();
        } else if (c == '-') {
            consume();
            result -= parse_term();
        } else {
            break;
        }
    }
    return result;
}

/*
 * parse_term: handles multiplication and division
 */
static double parse_term(void) {
    double result = parse_factor();

    while (1) {
        char c = peek();
        if (c == '*') {
            consume();
            result *= parse_factor();
        } else if (c == '/') {
            consume();
            double divisor = parse_factor();
            if (divisor == 0.0) {
                set_error("Division by zero");
                return 0.0;
            }
            result /= divisor;
        } else {
            break;
        }
    }
    return result;
}

/*
 * parse_factor: handles exponentiation (right-associative)
 *   e.g. 2^3^2 = 2^(3^2) = 512
 */
static double parse_factor(void) {
    double base = parse_base();

    if (peek() == '^') {
        consume();
        double exp = parse_factor();   /* right-recursive for right-assoc */
        base = pow(base, exp);
    }
    return base;
}

/*
 * parse_base: handles numbers, variable x, parentheses,
 *             unary minus, and named functions
 */
static double parse_base(void) {
    char c = peek();

    /* --- Unary minus --- */
    if (c == '-') {
        consume();
        return -parse_base();
    }

    /* --- Parenthesised sub-expression --- */
    if (c == '(') {
        consume();   /* eat '(' */
        double val = parse_expr();
        if (peek() != ')') {
            set_error("Expected closing parenthesis at position %d", g_pos);
            return 0.0;
        }
        consume();   /* eat ')' */
        return val;
    }

    /* --- Variable x --- */
    if (c == 'x') {
        consume();
        return g_x;
    }

    /* --- Named function (sin, cos, tan, sqrt, log, exp, abs) --- */
    if (isalpha((unsigned char)c)) {
        char fname[16] = {0};
        int  fi = 0;
        /* Read the function name */
        while (isalpha((unsigned char)peek()) && fi < 15) {
            fname[fi++] = consume();
        }
        fname[fi] = '\0';

        /* Expect opening parenthesis */
        if (peek() != '(') {
            set_error("Expected '(' after function '%s' at position %d", fname, g_pos);
            return 0.0;
        }
        consume();   /* eat '(' */
        double arg = parse_expr();
        if (peek() != ')') {
            set_error("Expected ')' after argument of '%s' at position %d", fname, g_pos);
            return 0.0;
        }
        consume();   /* eat ')' */

        /* Dispatch */
        if      (strcmp(fname, "sin")  == 0) return sin(arg);
        else if (strcmp(fname, "cos")  == 0) return cos(arg);
        else if (strcmp(fname, "tan")  == 0) return tan(arg);
        else if (strcmp(fname, "asin") == 0) return asin(arg);
        else if (strcmp(fname, "acos") == 0) return acos(arg);
        else if (strcmp(fname, "atan") == 0) return atan(arg);
        else if (strcmp(fname, "sqrt") == 0) {
            if (arg < 0) { set_error("sqrt of negative number"); return 0.0; }
            return sqrt(arg);
        }
        else if (strcmp(fname, "log")  == 0) {
            if (arg <= 0) { set_error("log of non-positive number"); return 0.0; }
            return log(arg);   /* natural log */
        }
        else if (strcmp(fname, "log10") == 0) {
            if (arg <= 0) { set_error("log10 of non-positive number"); return 0.0; }
            return log10(arg);
        }
        else if (strcmp(fname, "exp")  == 0) return exp(arg);
        else if (strcmp(fname, "abs")  == 0) return fabs(arg);
        else if (strcmp(fname, "floor") == 0) return floor(arg);
        else if (strcmp(fname, "ceil")  == 0) return ceil(arg);
        else if (strcmp(fname, "round") == 0) return round(arg);
        else {
            set_error("Unknown function: '%s'", fname);
            return 0.0;
        }
    }

    /* --- Numeric literal --- */
    if (isdigit((unsigned char)c) || c == '.') {
        char  numbuf[64];
        int   ni = 0;
        skip_whitespace();

        /* Integer part */
        while (isdigit((unsigned char)g_expr[g_pos]) && ni < 63)
            numbuf[ni++] = g_expr[g_pos++];
        /* Decimal part */
        if (g_expr[g_pos] == '.') {
            numbuf[ni++] = g_expr[g_pos++];
            while (isdigit((unsigned char)g_expr[g_pos]) && ni < 63)
                numbuf[ni++] = g_expr[g_pos++];
        }
        /* Scientific notation */
        if (g_expr[g_pos] == 'e' || g_expr[g_pos] == 'E') {
            numbuf[ni++] = g_expr[g_pos++];
            if (g_expr[g_pos] == '+' || g_expr[g_pos] == '-')
                numbuf[ni++] = g_expr[g_pos++];
            while (isdigit((unsigned char)g_expr[g_pos]) && ni < 63)
                numbuf[ni++] = g_expr[g_pos++];
        }
        numbuf[ni] = '\0';
        return atof(numbuf);
    }

    set_error("Unexpected character '%c' at position %d", c, g_pos);
    return 0.0;
}

/* ------------------------------------------------------------------ */
/* Public API                                                           */
/* ------------------------------------------------------------------ */

void set_expression(const char* expr) {
    strncpy(g_expr, expr, MAX_EXPR_LEN - 1);
    g_expr[MAX_EXPR_LEN - 1] = '\0';
    g_error[0] = '\0';
}

double eval_expr(double x) {
    g_pos   = 0;
    g_x     = x;
    g_error[0] = '\0';
    double result = parse_expr();
    return result;
}

double eval_expr_str(const char* expr, double x) {
    set_expression(expr);
    return eval_expr(x);
}

/* ------------------------------------------------------------------ */
/* Optional: standalone test (compiled only when TEST is defined)       */
/* ------------------------------------------------------------------ */

#ifdef TEST_MAIN
int main(void) {
    const char* tests[] = {
        "x^2 + 2*x + 1",
        "sin(x) + cos(x)",
        "sqrt(x^2 + 1)",
        "2^3^2",          /* should be 512 */
        "(1 + x) * (1 - x)",
        NULL
    };
    double xval = 3.0;
    for (int i = 0; tests[i]; i++) {
        set_expression(tests[i]);
        double r = eval_expr(xval);
        if (get_last_error()[0])
            printf("  EXPR: %-30s  ERROR: %s\n", tests[i], get_last_error());
        else
            printf("  EXPR: %-30s  x=%.1f  =>  %.6f\n", tests[i], xval, r);
    }
    return 0;
}
#endif
