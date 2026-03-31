#ifndef ENGINE_H
#define ENGINE_H

#ifdef __cplusplus
extern "C" {
#endif

/*
 * SINGULARITY ENGINE - C Core
 * Stack-based expression evaluator supporting +, -, *, /, ^
 * Operates on a fixed expression set via set_expression()
 */

/* Maximum expression length */
#define MAX_EXPR_LEN 256

/* Set the expression to be evaluated */
void set_expression(const char* expr);

/* Evaluate the expression at a given value of x */
double eval_expr(double x);

/* Evaluate a raw expression string at x (no need to call set_expression first) */
double eval_expr_str(const char* expr, double x);

/* Return last error message (empty string if no error) */
const char* get_last_error(void);

#ifdef __cplusplus
}
#endif

#endif /* ENGINE_H */
