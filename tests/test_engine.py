import unittest
import os
import sys
import logging

# Ensure project root is in path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from python_layer.bridge import evaluate, set_expr, jit_status
from python_layer.ai_module import symbolic_diff, symbolic_simplify

class TestSingularityEngine(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        # Build the C library if it doesn't exist (useful for local runs)
        # In CI, we expect it to be built by the workflow
        pass

    def test_c_engine_basic(self):
        """Test basic arithmetic in C engine via bridge"""
        set_expr("x^2 + 2*x + 1")
        res = evaluate(3.0)
        self.assertAlmostEqual(res, 16.0)

    def test_c_engine_functions(self):
        """Test extended math functions in C engine"""
        # floor(4.7) = 4.0
        res = evaluate(4.7, expr="floor(x)")
        self.assertEqual(res, 4.0)
        # abs(-5) = 5.0
        res = evaluate(-5.0, expr="abs(x)")
        self.assertEqual(res, 5.0)

    def test_jit_compilation(self):
        """Test if JIT compiles and executes correctly"""
        expr = "x^2 + 10"
        # First call triggers compilation
        res1 = evaluate(2.0, expr=expr)
        self.assertEqual(res1, 14.0)
        
        status = jit_status()
        self.assertIn(expr, status['expressions'], f"JIT failed to compile {expr}. Status: {status}")
        
        # Second call uses JIT
        res2 = evaluate(3.0, expr=expr)
        self.assertEqual(res2, 19.0)

    def test_symbolic_diff(self):
        """Test SymPy differentiation"""
        res_str, _ = symbolic_diff("x^3")
        self.assertEqual(res_str, "3*x**2")

    def test_symbolic_simplify(self):
        """Test SymPy simplification"""
        res_str, _ = symbolic_simplify("(x^2 - 1) / (x - 1)")
        self.assertTrue("x + 1" in res_str or "1 + x" in res_str)

    def test_cache(self):
        """Test the LRU evaluation cache"""
        set_expr("x + 1")
        evaluate(10.0) # Miss
        evaluate(10.0) # Hit
        from python_layer.bridge import cache_stats
        stats = cache_stats()
        self.assertGreaterEqual(stats['hits'], 1)

if __name__ == '__main__':
    unittest.main()
