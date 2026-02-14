"""
Integration Test for Issue 04: Dimensional Analysis Validation Failure FIX

Tests that the fix correctly catches dimensional mismatches at the API validation level.

BUG (before fix):
- Location: backend/app/api/v1/physics_models.py line 571
- Problem: if expected_dim and input_dims: skipped validation when input_dims was {}
- Result: Dimension mismatches incorrectly validated as PASS

FIX (after):
- Removed check for input_dims being truthy
- Always validate when expected_dim exists
- Let dimensional_analysis.py catch undefined input dimensions
"""

import pytest
from app.services.dimensional_analysis import (
    Dimension,
    LENGTH,
    AREA,
    VOLUME,
    DIMENSIONLESS,
    validate_equation_dimensions,
    UNIT_DIMENSIONS,
)
from app.services.equation_engine import parse_equation


class TestIssueFourDimensionalFix:
    """Test the specific bug fix for Issue 04."""

    def test_bug_reproduction_m_vs_m2(self):
        """
        ORIGINAL BUG REPORT:
        - Output expects: m² (area)
        - Equation: test_input (which is m, length)
        - Before fix: PASS (incorrect)
        - After fix: FAIL (correct)
        """
        # Parse equation
        equation = "test_input"
        parsed = parse_equation(equation, allowed_inputs=["test_input"])
        ast = parsed['ast']

        # Input dimensions
        input_dims = {
            "test_input": LENGTH  # m
        }

        # Expected output dimension
        expected_dim = AREA  # m²

        # Should FAIL because LENGTH != AREA
        is_valid, error = validate_equation_dimensions(ast, input_dims, expected_dim)

        assert is_valid == False, "Should fail: m != m²"
        assert "mismatch" in error.lower(), f"Error should mention dimension mismatch: {error}"

    def test_correct_dimensions_pass(self):
        """
        Control test: Correct dimensions should pass.
        """
        equation = "test_input * test_input"
        parsed = parse_equation(equation, allowed_inputs=["test_input"])
        ast = parsed['ast']

        input_dims = {
            "test_input": LENGTH  # m
        }

        expected_dim = AREA  # m² = m * m

        is_valid, error = validate_equation_dimensions(ast, input_dims, expected_dim)

        assert is_valid == True, f"Should pass: m * m = m²"
        assert error == ""

    def test_missing_input_dimension_fails(self):
        """
        If an input is used but has no dimension, validation should fail.
        """
        equation = "length * width"
        parsed = parse_equation(equation, allowed_inputs=["length", "width"])
        ast = parsed['ast']

        # Only one input has dimension (width is missing)
        input_dims = {
            "length": LENGTH
            # "width" is missing!
        }

        expected_dim = AREA

        # Should fail because "width" dimension is unknown
        is_valid, error = validate_equation_dimensions(ast, input_dims, expected_dim)

        assert is_valid == False
        assert "width" in error.lower() or "unknown" in error.lower()

    def test_complex_equation_dimension_tracking(self):
        """
        Test that complex equations correctly track dimensions.
        
        Example: Volume = length * width * height
        All inputs are LENGTH (m)
        Result should be VOLUME (m³)
        """
        equation = "length * width * height"
        parsed = parse_equation(equation, allowed_inputs=["length", "width", "height"])
        ast = parsed['ast']

        input_dims = {
            "length": LENGTH,   # m
            "width": LENGTH,    # m
            "height": LENGTH    # m
        }

        expected_dim = VOLUME  # m³

        is_valid, error = validate_equation_dimensions(ast, input_dims, expected_dim)

        assert is_valid == True, f"m * m * m should equal m³"
        assert error == ""

    def test_power_operation_dimensions(self):
        """
        Test that power operations correctly compute dimensions.
        
        Example: area = length^2
        """
        equation = "length ** 2"
        parsed = parse_equation(equation, allowed_inputs=["length"])
        ast = parsed['ast']

        input_dims = {
            "length": LENGTH  # m
        }

        expected_dim = AREA  # m²

        is_valid, error = validate_equation_dimensions(ast, input_dims, expected_dim)

        assert is_valid == True, f"m² should equal m²"
        assert error == ""

    def test_division_dimensions(self):
        """
        Test that division correctly computes dimensions.
        
        Example: volume / area = length
        """
        equation = "volume / area"
        parsed = parse_equation(equation, allowed_inputs=["volume", "area"])
        ast = parsed['ast']

        input_dims = {
            "volume": VOLUME,  # m³
            "area": AREA       # m²
        }

        expected_dim = LENGTH  # m³ / m² = m

        is_valid, error = validate_equation_dimensions(ast, input_dims, expected_dim)

        assert is_valid == True, f"m³ / m² should equal m"
        assert error == ""

    def test_dimension_mismatch_in_addition(self):
        """
        Test that adding incompatible dimensions fails.
        
        Example: length + area (invalid!)
        """
        equation = "length + area"
        parsed = parse_equation(equation, allowed_inputs=["length", "area"])
        ast = parsed['ast']

        input_dims = {
            "length": LENGTH,  # m
            "area": AREA       # m²
        }

        expected_dim = LENGTH  # Doesn't matter, should fail before reaching here

        is_valid, error = validate_equation_dimensions(ast, input_dims, expected_dim)

        assert is_valid == False
        assert "mismatch" in error.lower() or "add" in error.lower()

    def test_dimensionless_outputs(self):
        """
        Test that dimensionless outputs validate correctly.
        
        Example: ratio = length / length (dimensionless)
        """
        equation = "length1 / length2"
        parsed = parse_equation(equation, allowed_inputs=["length1", "length2"])
        ast = parsed['ast']

        input_dims = {
            "length1": LENGTH,  # m
            "length2": LENGTH   # m
        }

        expected_dim = DIMENSIONLESS  # m / m = 1

        is_valid, error = validate_equation_dimensions(ast, input_dims, expected_dim)

        assert is_valid == True, f"m / m should equal dimensionless"
        assert error == ""


class TestAPIValidationLogicFix:
    """
    Test the actual API validation logic that was fixed.
    
    Simulates the code path in physics_models.py validation endpoint.
    """

    def simulate_api_validation(self, inputs_with_units, output_unit, equation, input_names):
        """
        Simulate the API validation logic before and after the fix.
        
        Returns: (is_valid, message)
        """
        # Build input_dims dict (only includes inputs with known units)
        input_dims = {}
        for inp_name, inp_unit in inputs_with_units.items():
            if inp_unit and inp_unit in UNIT_DIMENSIONS:
                input_dims[inp_name] = UNIT_DIMENSIONS[inp_unit]

        # Parse equation
        parsed = parse_equation(equation, allowed_inputs=input_names)
        ast = parsed['ast']

        # Get expected dimension
        expected_dim = UNIT_DIMENSIONS.get(output_unit) if output_unit else None

        # AFTER FIX: Always validate if expected_dim exists
        if expected_dim:
            is_valid, error_msg = validate_equation_dimensions(
                ast,
                input_dims,
                expected_dim
            )
            return is_valid, error_msg
        else:
            return True, "Dimensions not checked (no output unit specified)"

    def test_api_catches_dimension_mismatch(self):
        """
        Test that API validation now catches m vs m² mismatch.
        """
        inputs_with_units = {
            "test_input": "m"  # LENGTH
        }
        output_unit = "m²"  # AREA
        equation = "test_input"
        input_names = ["test_input"]

        is_valid, message = self.simulate_api_validation(
            inputs_with_units, output_unit, equation, input_names
        )

        # After fix: should FAIL
        assert is_valid == False, f"API should catch dimension mismatch. Got: {message}"
        assert "mismatch" in message.lower()

    def test_api_passes_correct_dimensions(self):
        """
        Test that API validation passes correct dimensions.
        """
        inputs_with_units = {
            "length": "m",
            "width": "m"
        }
        output_unit = "m²"
        equation = "length * width"
        input_names = ["length", "width"]

        is_valid, message = self.simulate_api_validation(
            inputs_with_units, output_unit, equation, input_names
        )

        # Should pass
        assert is_valid == True, f"API should pass correct dimensions. Got: {message}"

    def test_api_handles_missing_input_dimensions(self):
        """
        Test that API handles inputs without units gracefully.
        
        If an input is used in the equation but has no unit defined,
        the validation should fail with a clear error.
        """
        inputs_with_units = {
            "length": "m",
            # "width" has no unit!
        }
        output_unit = "m²"
        equation = "length * width"
        input_names = ["length", "width"]

        is_valid, message = self.simulate_api_validation(
            inputs_with_units, output_unit, equation, input_names
        )

        # Should fail because "width" dimension is unknown
        assert is_valid == False
        assert "width" in message.lower() or "unknown" in message.lower()

    def test_api_skips_validation_when_no_output_unit(self):
        """
        Test that API skips dimensional validation when output has no unit.
        
        This is acceptable for truly dimensionless outputs or outputs where
        dimensional analysis doesn't apply.
        """
        inputs_with_units = {
            "length": "m"
        }
        output_unit = None  # No unit specified
        equation = "length"
        input_names = ["length"]

        is_valid, message = self.simulate_api_validation(
            inputs_with_units, output_unit, equation, input_names
        )

        # Should pass (validation skipped)
        assert is_valid == True
        assert "not checked" in message.lower()


class TestEdgeCases:
    """Test edge cases and corner scenarios."""

    def test_all_inputs_dimensionless(self):
        """
        Test equation with all dimensionless inputs.
        """
        equation = "ratio * scale"
        parsed = parse_equation(equation, allowed_inputs=["ratio", "scale"])
        ast = parsed['ast']

        input_dims = {
            "ratio": DIMENSIONLESS,
            "scale": DIMENSIONLESS
        }

        expected_dim = DIMENSIONLESS

        is_valid, error = validate_equation_dimensions(ast, input_dims, expected_dim)

        assert is_valid == True
        assert error == ""

    def test_complex_unit_mismatch(self):
        """
        Test complex dimension mismatch: Force vs Energy.
        
        Force = M·L·T⁻² (N)
        Energy = M·L²·T⁻² (J)
        
        These are different!
        """
        from app.services.dimensional_analysis import FORCE, ENERGY

        equation = "force"
        parsed = parse_equation(equation, allowed_inputs=["force"])
        ast = parsed['ast']

        input_dims = {
            "force": FORCE  # M·L·T⁻²
        }

        expected_dim = ENERGY  # M·L²·T⁻² (different!)

        is_valid, error = validate_equation_dimensions(ast, input_dims, expected_dim)

        assert is_valid == False
        assert "mismatch" in error.lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
