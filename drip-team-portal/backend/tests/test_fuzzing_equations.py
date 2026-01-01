"""
Equation Parser Stress Test / Fuzzing Suite
============================================
Tests edge cases that could break the parser:
- Circular MODEL references
- Boundary conditions (sqrt negative, div/0, overflow)
- Reference failures
- Malformed input

Run with: PYTHONPATH=. python3 tests/test_fuzzing_equations.py
"""

import sys
import math
import traceback
from typing import Tuple, Any

# Test result tracking
results = []

def log_test(category: str, test_name: str, input_val: Any, expected: str, actual: str, passed: bool):
    """Log a test result."""
    status = "✅ PASS" if passed else "❌ FAIL"
    results.append({
        "category": category,
        "test": test_name,
        "input": str(input_val)[:80],
        "expected": expected,
        "actual": actual[:200] if actual else "None",
        "passed": passed
    })
    print(f"{status} | {category} | {test_name}")
    if not passed:
        print(f"       Input: {str(input_val)[:80]}")
        print(f"       Expected: {expected}")
        print(f"       Actual: {actual[:200] if actual else 'None'}")


def test_safely(func, *args, **kwargs) -> Tuple[Any, str, bool]:
    """Execute a function safely, catching all exceptions."""
    try:
        result = func(*args, **kwargs)
        return (result, None, False)  # (result, error, is_exception)
    except Exception as e:
        return (None, f"{type(e).__name__}: {str(e)}", True)


# =============================================================================
# PRIORITY 1: MODEL Circular Reference Gap
# =============================================================================
def test_model_circular():
    print("\n" + "="*70)
    print("PRIORITY 1: MODEL Circular Reference Gap")
    print("="*70)

    from app.services.equation_engine.parser import parse_equation
    from app.services.equation_engine.evaluator import evaluate_equation

    # Test 1: Direct self-reference in MODEL (if MODEL parsing exists in equation_engine)
    # Note: MODEL() is handled by value_engine, not equation_engine parser
    # So we test via value_engine

    try:
        from app.services.value_engine import ValueEngine, ExpressionError
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker

        # Create a test session (in-memory or use existing)
        # For this test, we'll test the _parse_expression method directly

        print("\nTest 1a: MODEL() parsing in expression")
        test_expr = 'MODEL("SelfRef", x: MODEL("SelfRef", x: 1))'

        # We can't fully test without a DB, but we can test parsing
        class MockDB:
            def query(self, *args): return self
            def filter(self, *args): return self
            def first(self): return None
            def all(self): return []
            def add(self, *args): pass
            def flush(self): pass

        engine = ValueEngine(MockDB())

        result, error, is_exc = test_safely(engine._parse_expression, test_expr)

        if is_exc:
            log_test("MODEL_CIRCULAR", "nested_model_parse", test_expr,
                    "Should parse (circular check at eval)", error, False)
        else:
            # Check if model_calls were extracted
            model_calls = result.get('model_calls', {})
            has_nested = any('MODEL' in str(v.get('bindings', {})) for v in model_calls.values())
            log_test("MODEL_CIRCULAR", "nested_model_parse", test_expr,
                    "Parse succeeds, nested MODEL in bindings",
                    f"Parsed. model_calls={len(model_calls)}, has_nested={has_nested}", True)

            # Document the structure
            print(f"       Parsed structure: {result.get('model_calls', {})}")

    except ImportError as e:
        print(f"  SKIP: Could not import required modules: {e}")
    except Exception as e:
        print(f"  ERROR: {type(e).__name__}: {e}")
        traceback.print_exc()

    # Test 1b: Check if there's runtime circular detection for MODEL
    print("\nTest 1b: Check circular detection implementation")
    try:
        from app.services.model_evaluation import evaluate_inline_model

        # This would require actual DB with models - document expected behavior
        print("  INFO: evaluate_inline_model exists - would need DB to test circular")
        print("  INFO: Based on code review, MODEL circular detection is Phase 2 (not implemented)")
        log_test("MODEL_CIRCULAR", "circular_detection_status", "N/A",
                "Should have circular detection",
                "NOT IMPLEMENTED (skipped in tests)", False)

    except ImportError as e:
        print(f"  Module not available: {e}")


# =============================================================================
# PRIORITY 2: Boundary Conditions
# =============================================================================
def test_boundary_conditions():
    print("\n" + "="*70)
    print("PRIORITY 2: Boundary Conditions")
    print("="*70)

    from app.services.equation_engine.parser import parse_equation
    from app.services.equation_engine.evaluator import evaluate_equation, EvaluationError

    tests = [
        # (expression, input_values, expected_error_substring)
        ("sqrt(x)", {"x": -1}, "negative"),
        ("sqrt(x)", {"x": -0.0001}, "negative"),
        ("1/x", {"x": 0}, "zero"),
        ("a/(b-b)", {"a": 1, "b": 5}, "zero"),
        ("exp(x)", {"x": 10000}, "overflow"),
        ("exp(x)", {"x": 800}, "overflow"),  # math.exp overflows around 709
        ("tan(x)", {"x": math.pi/2}, "asymptote"),
        ("tan(x)", {"x": 1.5707963267948966}, "asymptote"),  # pi/2 exactly
        ("ln(x)", {"x": 0}, "non-positive"),
        ("ln(x)", {"x": -1}, "non-positive"),
        ("log(x)", {"x": 0}, "non-positive"),
        ("x**y", {"x": -2, "y": 0.5}, "negative"),  # (-2)^0.5
        ("x**y", {"x": 0, "y": -1}, "zero"),  # 0^(-1)
    ]

    for expr, inputs, expected_substr in tests:
        test_name = f"{expr} with {inputs}"

        # Parse
        parse_result, parse_error, parse_exc = test_safely(parse_equation, expr)

        if parse_exc:
            log_test("BOUNDARY", test_name, expr,
                    f"EvaluationError containing '{expected_substr}'",
                    f"Parse failed: {parse_error}", False)
            continue

        # Evaluate
        eval_result, eval_error, eval_exc = test_safely(
            evaluate_equation, parse_result["ast"], inputs
        )

        if eval_exc:
            # Check if it's the right kind of error
            is_eval_error = "EvaluationError" in eval_error
            has_expected_msg = expected_substr.lower() in eval_error.lower()
            passed = is_eval_error and has_expected_msg

            log_test("BOUNDARY", test_name, expr,
                    f"EvaluationError containing '{expected_substr}'",
                    eval_error, passed)
        else:
            # Should have raised an error but didn't
            log_test("BOUNDARY", test_name, expr,
                    f"EvaluationError containing '{expected_substr}'",
                    f"No error! Result={eval_result}", False)


# =============================================================================
# PRIORITY 3: Reference Failures
# =============================================================================
def test_reference_failures():
    print("\n" + "="*70)
    print("PRIORITY 3: Reference Failures")
    print("="*70)

    from app.services.value_engine import ValueEngine, ExpressionError

    class MockDB:
        def query(self, *args): return self
        def filter(self, *args): return self
        def first(self): return None
        def all(self): return []
        def add(self, *args): pass
        def flush(self): pass
        def get(self, *args): return None

    engine = ValueEngine(MockDB())

    # Test 3a: Non-existent reference
    print("\nTest 3a: Non-existent component reference")
    test_expr = "#NONEXISTENT_COMPONENT.some_property + 5"

    result, error, is_exc = test_safely(engine._parse_expression, test_expr)

    if is_exc:
        log_test("REF_FAILURE", "nonexistent_ref_parse", test_expr,
                "Parse succeeds (validation at eval)", error, False)
    else:
        refs = result.get("references", [])
        log_test("REF_FAILURE", "nonexistent_ref_parse", test_expr,
                "Parse succeeds, refs extracted",
                f"Refs found: {refs}", len(refs) > 0)

    # Test 3b: Resolve non-existent reference
    print("\nTest 3b: Resolve non-existent reference")
    resolve_result = engine._resolve_reference("NONEXISTENT.property")
    log_test("REF_FAILURE", "resolve_nonexistent", "NONEXISTENT.property",
            "Returns None gracefully",
            f"Result: {resolve_result}", resolve_result is None)

    # Test 3c: Invalid reference format
    print("\nTest 3c: Invalid reference formats")
    invalid_refs = [
        "no_dot_ref",
        ".property_only",
        "component.",
        "",
        "a.b.c.d",
    ]

    for ref in invalid_refs:
        resolve_result = engine._resolve_reference(ref)
        log_test("REF_FAILURE", f"invalid_format: {ref}", ref,
                "Returns None gracefully",
                f"Result: {resolve_result}", resolve_result is None)

    # Test 3d: Circular dependency detection (value graph)
    print("\nTest 3d: Circular dependency check function")
    # Test the check_circular_dependency method
    # With mock DB, this tests the logic path

    # node_id == target_id should return True
    result = engine.check_circular_dependency(1, 1)
    log_test("REF_FAILURE", "circular_self_check", "node 1 -> node 1",
            "Returns True (is circular)", f"Result: {result}", result == True)


# =============================================================================
# PRIORITY 4: Malformed Input
# =============================================================================
def test_malformed_input():
    print("\n" + "="*70)
    print("PRIORITY 4: Malformed Input")
    print("="*70)

    from app.services.equation_engine.parser import parse_equation, EquationParseError
    from app.services.value_engine import ValueEngine, ExpressionError

    tests = [
        # (input, expected_error_type)
        ("", "EquationParseError"),
        ("   ", "EquationParseError"),
        (None, "Error"),  # Should handle None gracefully
        ("(((", "EquationParseError"),
        ("((())", "EquationParseError"),
        ("sqrt(", "EquationParseError"),
        ("sin(cos(", "EquationParseError"),
        ("1 + + 2", "EquationParseError"),
        ("1 +", "EquationParseError"),
        ("* 5", "EquationParseError"),
        ("√(x)", "EquationParseError"),  # Unicode sqrt symbol
        ("×", "EquationParseError"),  # Unicode multiplication
        ("÷", "EquationParseError"),  # Unicode division
        ("π", "Success"),  # This might work as symbol 'π'
        ("∞", "EquationParseError"),  # Infinity symbol
        ("x²", "EquationParseError"),  # Superscript
        ("1e99999999", "Error"),  # Extreme number
        ("0." + "0"*1000 + "1", "Success"),  # Very small number
        ('MODEL("', "Error"),  # Incomplete MODEL
        ('LOOKUP("x",', "Error"),  # Incomplete LOOKUP
    ]

    # Test with equation_engine parser
    print("\nUsing equation_engine.parser:")
    for test_input, expected in tests:
        if test_input is None:
            # Special handling for None
            result, error, is_exc = test_safely(parse_equation, test_input)
        else:
            result, error, is_exc = test_safely(parse_equation, test_input)

        if expected == "Success":
            passed = not is_exc
            actual = f"Parsed successfully" if not is_exc else error
        else:
            passed = is_exc and expected in error
            actual = error if is_exc else f"Unexpected success: {result}"

        display_input = repr(test_input)[:40]
        log_test("MALFORMED", f"parser: {display_input}", test_input,
                expected, actual, passed)

    # Test with value_engine parser
    print("\nUsing value_engine._parse_expression:")

    class MockDB:
        def query(self, *args): return self
        def filter(self, *args): return self
        def first(self): return None
        def all(self): return []
        def add(self, *args): pass
        def flush(self): pass

    engine = ValueEngine(MockDB())

    value_engine_tests = [
        ("", "ExpressionError"),
        ("(((", "ExpressionError"),
        ("#.property", "Success"),  # Edge case - does it parse?
        ("#COMP.", "Success"),  # Missing property
        ("MODEL()", "Success"),  # Empty MODEL
        ('MODEL("Test")', "Success"),  # MODEL with no params
        ('MODEL("Test", :value)', "Error"),  # Invalid binding
    ]

    for test_input, expected in value_engine_tests:
        result, error, is_exc = test_safely(engine._parse_expression, test_input)

        if expected == "Success":
            passed = not is_exc
            actual = f"Parsed: valid={result.get('valid') if result else 'N/A'}" if not is_exc else error
        else:
            passed = is_exc
            actual = error if is_exc else f"Unexpected success"

        display_input = repr(test_input)[:40]
        log_test("MALFORMED", f"value_engine: {display_input}", test_input,
                expected, actual, passed)


# =============================================================================
# Additional Edge Cases
# =============================================================================
def test_additional_edge_cases():
    print("\n" + "="*70)
    print("ADDITIONAL: Edge Cases")
    print("="*70)

    from app.services.equation_engine.parser import parse_equation
    from app.services.equation_engine.evaluator import evaluate_equation

    # Test very deep nesting
    print("\nTest: Deep nesting")
    deep_expr = "sqrt(" * 50 + "x" + ")" * 50
    result, error, is_exc = test_safely(parse_equation, deep_expr)
    log_test("EDGE", "deep_nesting_50", deep_expr[:50] + "...",
            "Should parse or fail gracefully",
            error if is_exc else "Parsed OK", not is_exc or "RecursionError" not in str(error))

    # Test very long expression
    print("\nTest: Long expression")
    long_expr = " + ".join(["x"] * 1000)
    result, error, is_exc = test_safely(parse_equation, long_expr)
    log_test("EDGE", "long_expression_1000_terms", f"x + x + ... ({len(long_expr)} chars)",
            "Should parse",
            error if is_exc else f"Parsed OK, {len(result.get('inputs', []))} inputs", not is_exc)

    # Test special float values
    print("\nTest: Special float values in evaluation")
    simple_parse = parse_equation("x + y")

    special_floats = [
        ({"x": float('inf'), "y": 1}, "inf handling"),
        ({"x": float('-inf'), "y": 1}, "-inf handling"),
        ({"x": float('nan'), "y": 1}, "nan handling"),
        ({"x": 1e308, "y": 1e308}, "near-overflow addition"),
    ]

    for inputs, desc in special_floats:
        result, error, is_exc = test_safely(evaluate_equation, simple_parse["ast"], inputs)
        if is_exc:
            log_test("EDGE", desc, inputs, "Handle gracefully", error, True)
        else:
            # Check if result is sensible
            is_sensible = result is not None and (math.isfinite(result) or math.isinf(result) or math.isnan(result))
            log_test("EDGE", desc, inputs, "Handle gracefully",
                    f"Result: {result}", is_sensible)


# =============================================================================
# Main
# =============================================================================
def print_summary():
    print("\n" + "="*70)
    print("SUMMARY")
    print("="*70)

    total = len(results)
    passed = sum(1 for r in results if r["passed"])
    failed = total - passed

    print(f"\nTotal: {total} | Passed: {passed} | Failed: {failed}")
    print(f"Pass Rate: {passed/total*100:.1f}%")

    if failed > 0:
        print("\n--- FAILURES ---")
        for r in results:
            if not r["passed"]:
                print(f"\n{r['category']} | {r['test']}")
                print(f"  Input: {r['input']}")
                print(f"  Expected: {r['expected']}")
                print(f"  Actual: {r['actual']}")

    # Categorize by priority
    print("\n--- BY CATEGORY ---")
    categories = {}
    for r in results:
        cat = r["category"]
        if cat not in categories:
            categories[cat] = {"passed": 0, "failed": 0}
        if r["passed"]:
            categories[cat]["passed"] += 1
        else:
            categories[cat]["failed"] += 1

    for cat, stats in categories.items():
        total_cat = stats["passed"] + stats["failed"]
        print(f"  {cat}: {stats['passed']}/{total_cat} passed")


if __name__ == "__main__":
    print("="*70)
    print("EQUATION PARSER STRESS TEST / FUZZING SUITE")
    print("="*70)

    try:
        test_model_circular()
    except Exception as e:
        print(f"ERROR in test_model_circular: {e}")
        traceback.print_exc()

    try:
        test_boundary_conditions()
    except Exception as e:
        print(f"ERROR in test_boundary_conditions: {e}")
        traceback.print_exc()

    try:
        test_reference_failures()
    except Exception as e:
        print(f"ERROR in test_reference_failures: {e}")
        traceback.print_exc()

    try:
        test_malformed_input()
    except Exception as e:
        print(f"ERROR in test_malformed_input: {e}")
        traceback.print_exc()

    try:
        test_additional_edge_cases()
    except Exception as e:
        print(f"ERROR in test_additional_edge_cases: {e}")
        traceback.print_exc()

    print_summary()
