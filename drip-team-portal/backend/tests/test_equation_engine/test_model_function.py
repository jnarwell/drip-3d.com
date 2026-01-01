"""
Unit tests for MODEL() function integration.

Tests:
1. _extract_model_calls function (MODEL() parsing)
2. _split_model_params helper function
3. _parse_model_binding helper function
4. evaluate_inline_model function
5. Integration with ValueEngine expression parsing
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
import re

from app.services.value_engine import (
    _extract_model_calls,
    _split_model_params,
    _parse_model_binding,
)
from app.services.model_evaluation import (
    evaluate_inline_model,
    ModelEvaluationError,
)


# =============================================================================
# _extract_model_calls Tests
# =============================================================================

class TestExtractModelCalls:
    """Tests for _extract_model_calls() function."""

    def test_simple_model_single_input(self):
        """MODEL with single input should be extracted."""
        expr = 'MODEL("Simple", x: 5)'
        calls = _extract_model_calls(expr)
        assert len(calls) == 1
        assert calls[0]["model_name"] == "Simple"
        assert calls[0]["params_str"] == "x: 5"

    def test_model_with_multiple_inputs(self):
        """MODEL with multiple inputs should be extracted."""
        expr = 'MODEL("Thermal Expansion", CTE: 2.3e-5, delta_T: 100, L0: 1m)'
        calls = _extract_model_calls(expr)
        assert len(calls) == 1
        assert calls[0]["model_name"] == "Thermal Expansion"
        assert "CTE: 2.3e-5" in calls[0]["params_str"]
        assert "delta_T: 100" in calls[0]["params_str"]
        assert "L0: 1m" in calls[0]["params_str"]

    def test_model_with_output_parameter(self):
        """MODEL with output parameter should be extracted."""
        expr = 'MODEL("Rectangle", length: 5, width: 3, output: "area")'
        calls = _extract_model_calls(expr)
        assert len(calls) == 1
        assert calls[0]["model_name"] == "Rectangle"
        assert 'output: "area"' in calls[0]["params_str"]

    def test_model_with_no_inputs(self):
        """MODEL with no inputs should be extracted."""
        expr = 'MODEL("Constant")'
        calls = _extract_model_calls(expr)
        assert len(calls) == 1
        assert calls[0]["model_name"] == "Constant"
        assert calls[0]["params_str"] == ""

    def test_model_with_reference_input(self):
        """MODEL with #ref input should be extracted."""
        expr = 'MODEL("Thermal Expansion", CTE: #MAT.cte, delta_T: 100, L0: #PART.length)'
        calls = _extract_model_calls(expr)
        assert len(calls) == 1
        assert "#MAT.cte" in calls[0]["params_str"]
        assert "#PART.length" in calls[0]["params_str"]

    def test_model_with_scientific_notation(self):
        """MODEL with scientific notation should be extracted."""
        expr = 'MODEL("Test", value: 1.23e-10)'
        calls = _extract_model_calls(expr)
        assert len(calls) == 1
        assert "1.23e-10" in calls[0]["params_str"]

    def test_model_in_expression(self):
        """MODEL embedded in larger expression should be extracted."""
        expr = '#PART.length + MODEL("Thermal Expansion", CTE: 2.3e-5, delta_T: 100, L0: 1m)'
        calls = _extract_model_calls(expr)
        assert len(calls) == 1
        assert calls[0]["model_name"] == "Thermal Expansion"

    def test_model_with_spaces(self):
        """MODEL with various whitespace should be extracted."""
        expr = 'MODEL(  "Spaced Model"  ,  x: 5  ,  y: 10  )'
        calls = _extract_model_calls(expr)
        assert len(calls) == 1
        assert calls[0]["model_name"] == "Spaced Model"

    def test_nested_model_calls(self):
        """Nested MODEL() calls - outer contains inner as parameter."""
        expr = 'MODEL("Outer", x: MODEL("Inner", y: 5))'
        calls = _extract_model_calls(expr)
        # Extracts outer MODEL; inner is in params_str (processed during eval)
        assert len(calls) == 1
        assert calls[0]["model_name"] == "Outer"
        assert 'MODEL("Inner"' in calls[0]["params_str"]

    def test_multiple_model_calls(self):
        """Multiple MODEL() calls should all be extracted."""
        expr = 'MODEL("A", x: 1) + MODEL("B", y: 2)'
        calls = _extract_model_calls(expr)
        assert len(calls) == 2
        model_names = {c["model_name"] for c in calls}
        assert "A" in model_names
        assert "B" in model_names


# =============================================================================
# _split_model_params Tests
# =============================================================================

class TestSplitModelParams:
    """Tests for _split_model_params helper function."""

    def test_empty_string(self):
        """Empty string should return empty list."""
        assert _split_model_params("") == []
        assert _split_model_params(None) == []

    def test_single_param(self):
        """Single parameter should return list with one item."""
        result = _split_model_params("x: 5")
        assert result == ["x: 5"]

    def test_multiple_params(self):
        """Multiple parameters should split correctly."""
        result = _split_model_params("a: 1, b: 2, c: 3")
        assert result == ["a: 1", "b: 2", "c: 3"]

    def test_params_with_quoted_string(self):
        """Parameters with quoted strings should not split inside quotes."""
        result = _split_model_params('name: "hello, world", x: 5')
        assert result == ['name: "hello, world"', "x: 5"]

    def test_params_with_single_quotes(self):
        """Parameters with single-quoted strings should work."""
        result = _split_model_params("name: 'hello, world', x: 5")
        assert result == ["name: 'hello, world'", "x: 5"]

    def test_params_with_scientific_notation(self):
        """Parameters with scientific notation should work."""
        result = _split_model_params("CTE: 2.3e-5, delta_T: 1.5e+2")
        assert result == ["CTE: 2.3e-5", "delta_T: 1.5e+2"]

    def test_params_with_units(self):
        """Parameters with units should work."""
        result = _split_model_params("length: 1m, temp: 25°C")
        assert result == ["length: 1m", "temp: 25°C"]

    def test_params_with_expressions(self):
        """Parameters with math expressions should work."""
        result = _split_model_params("x: 2 + 3, y: sqrt(16)")
        assert result == ["x: 2 + 3", "y: sqrt(16)"]

    def test_nested_parentheses(self):
        """Parameters with nested parentheses should not split incorrectly."""
        result = _split_model_params("x: sin(pi/2), y: 10")
        assert result == ["x: sin(pi/2)", "y: 10"]


# =============================================================================
# _parse_model_binding Tests
# =============================================================================

class TestParseModelBinding:
    """Tests for _parse_model_binding helper function."""

    def test_simple_binding(self):
        """Simple binding should parse correctly."""
        key, value = _parse_model_binding("x: 5")
        assert key == "x"
        assert value == "5"

    def test_binding_with_spaces(self):
        """Binding with spaces should strip them."""
        key, value = _parse_model_binding("  x  :  5  ")
        assert key == "x"
        assert value == "5"

    def test_binding_with_unit(self):
        """Binding with unit should keep unit in value."""
        key, value = _parse_model_binding("length: 1m")
        assert key == "length"
        assert value == "1m"

    def test_binding_with_scientific_notation(self):
        """Binding with scientific notation should work."""
        key, value = _parse_model_binding("CTE: 2.3e-5")
        assert key == "CTE"
        assert value == "2.3e-5"

    def test_binding_with_reference(self):
        """Binding with reference should work."""
        key, value = _parse_model_binding("input: #PART.property")
        assert key == "input"
        assert value == "#PART.property"

    def test_binding_with_expression(self):
        """Binding with expression should work."""
        key, value = _parse_model_binding("x: a + b * 2")
        assert key == "x"
        assert value == "a + b * 2"

    def test_binding_with_quoted_string(self):
        """Binding with quoted string should work."""
        key, value = _parse_model_binding('output: "delta_L"')
        assert key == "output"
        assert value == '"delta_L"'

    def test_invalid_binding_no_colon(self):
        """Binding without colon should raise ValueError."""
        with pytest.raises(ValueError, match="missing ':'"):
            _parse_model_binding("invalid_binding")


# =============================================================================
# evaluate_inline_model Tests
# =============================================================================

class TestEvaluateInlineModel:
    """Tests for evaluate_inline_model function."""

    @pytest.fixture
    def mock_db(self):
        """Create a mock database session."""
        return MagicMock()

    @pytest.fixture
    def simple_model(self, mock_db):
        """Create a simple model fixture: y = x * 2."""
        # Create mock PhysicsModel
        mock_version = MagicMock()
        mock_version.version = 1
        mock_version.inputs = [{"name": "x", "required": True}]
        mock_version.outputs = [{"name": "y", "expression": "x * 2"}]
        mock_version.equations = {"y": "x * 2"}
        mock_version.equation_ast = None

        mock_model = MagicMock()
        mock_model.current_version = mock_version

        # Patch PhysicsModel.find_by_name
        with patch("app.models.physics_model.PhysicsModel.find_by_name") as mock_find:
            mock_find.return_value = mock_model
            yield mock_model

    @pytest.fixture
    def multi_output_model(self, mock_db):
        """Create a multi-output model fixture."""
        mock_version = MagicMock()
        mock_version.version = 1
        mock_version.inputs = [
            {"name": "length", "required": True},
            {"name": "width", "required": True}
        ]
        mock_version.outputs = [
            {"name": "area", "expression": "length * width"},
            {"name": "perimeter", "expression": "2 * (length + width)"}
        ]
        mock_version.equations = {
            "area": "length * width",
            "perimeter": "2 * (length + width)"
        }
        mock_version.equation_ast = None

        mock_model = MagicMock()
        mock_model.current_version = mock_version

        with patch("app.models.physics_model.PhysicsModel.find_by_name") as mock_find:
            mock_find.return_value = mock_model
            yield mock_model

    def test_model_not_found(self, mock_db):
        """Non-existent model should raise ModelEvaluationError."""
        with patch("app.models.physics_model.PhysicsModel.find_by_name") as mock_find:
            mock_find.return_value = None

            with pytest.raises(ModelEvaluationError, match="not found"):
                evaluate_inline_model(
                    model_name="NonExistent",
                    bindings={},
                    output_name=None,
                    db=mock_db
                )

    def test_model_no_current_version(self, mock_db):
        """Model with no current version should raise error."""
        mock_model = MagicMock()
        mock_model.current_version = None

        with patch("app.models.physics_model.PhysicsModel.find_by_name") as mock_find:
            mock_find.return_value = mock_model

            with pytest.raises(ModelEvaluationError, match="no current version"):
                evaluate_inline_model(
                    model_name="NoVersion",
                    bindings={},
                    output_name=None,
                    db=mock_db
                )

    def test_missing_required_input(self, mock_db, simple_model):
        """Missing required input should raise error."""
        with pytest.raises(ModelEvaluationError, match="missing required inputs"):
            evaluate_inline_model(
                model_name="Simple",
                bindings={},  # Missing 'x'
                output_name=None,
                db=mock_db
            )

    def test_multi_output_no_output_specified(self, mock_db, multi_output_model):
        """Multi-output model without output specified should raise error."""
        with pytest.raises(ModelEvaluationError, match="multiple outputs"):
            evaluate_inline_model(
                model_name="Rectangle",
                bindings={"length": 5, "width": 3},
                output_name=None,
                db=mock_db
            )

    def test_invalid_output_name(self, mock_db, multi_output_model):
        """Invalid output name should raise error."""
        with pytest.raises(ModelEvaluationError, match="has no output"):
            evaluate_inline_model(
                model_name="Rectangle",
                bindings={"length": 5, "width": 3},
                output_name="invalid",
                db=mock_db
            )

    def test_simple_model_evaluation(self, mock_db, simple_model):
        """Simple model should evaluate correctly."""
        result = evaluate_inline_model(
            model_name="Simple",
            bindings={"x": 5.0},
            output_name=None,
            db=mock_db
        )
        assert result == 10.0  # y = x * 2 = 5 * 2 = 10

    def test_multi_output_with_specified_output(self, mock_db, multi_output_model):
        """Multi-output model with specified output should work."""
        result_area = evaluate_inline_model(
            model_name="Rectangle",
            bindings={"length": 5.0, "width": 3.0},
            output_name="area",
            db=mock_db
        )
        assert result_area == 15.0  # area = 5 * 3 = 15

        result_perimeter = evaluate_inline_model(
            model_name="Rectangle",
            bindings={"length": 5.0, "width": 3.0},
            output_name="perimeter",
            db=mock_db
        )
        assert result_perimeter == 16.0  # perimeter = 2 * (5 + 3) = 16


# =============================================================================
# ValueEngine Expression Parsing Tests
# =============================================================================

class TestValueEngineModelParsing:
    """Tests for MODEL() parsing in ValueEngine._parse_expression."""

    @pytest.fixture
    def mock_db(self):
        """Create a mock database session."""
        return MagicMock()

    @pytest.fixture
    def value_engine(self, mock_db):
        """Create a ValueEngine instance."""
        from app.services.value_engine import ValueEngine
        return ValueEngine(db=mock_db)

    def test_parse_simple_model_expression(self, value_engine):
        """MODEL() expression should be parsed correctly."""
        expr = 'MODEL("Simple", x: 5)'
        parsed = value_engine._parse_expression(expr)

        assert parsed["valid"] is True
        assert "model_calls" in parsed
        assert len(parsed["model_calls"]) == 1

        model_call = list(parsed["model_calls"].values())[0]
        assert model_call["model_name"] == "Simple"
        assert model_call["bindings"] == {"x": "5"}
        assert model_call["output_name"] is None

    def test_parse_model_with_output(self, value_engine):
        """MODEL() with output parameter should be parsed correctly."""
        expr = 'MODEL("Rectangle", length: 5, width: 3, output: "area")'
        parsed = value_engine._parse_expression(expr)

        assert parsed["valid"] is True
        model_call = list(parsed["model_calls"].values())[0]
        assert model_call["model_name"] == "Rectangle"
        assert model_call["bindings"] == {"length": "5", "width": "3"}
        assert model_call["output_name"] == "area"

    def test_parse_model_with_reference(self, value_engine):
        """MODEL() with #ref input should be parsed correctly.

        Note: References like #MAT.cte are replaced with placeholders BEFORE
        MODEL() parsing, so the binding value contains the placeholder.
        """
        expr = 'MODEL("Thermal", CTE: #MAT.cte, delta_T: 100)'
        parsed = value_engine._parse_expression(expr)

        assert parsed["valid"] is True
        model_call = list(parsed["model_calls"].values())[0]
        # Reference is replaced with placeholder before MODEL() extraction
        assert "__ref_" in model_call["bindings"]["CTE"]
        assert model_call["bindings"]["delta_T"] == "100"
        # The original reference is stored in placeholders
        assert "MAT.cte" in parsed["references"]

    def test_parse_model_in_expression(self, value_engine):
        """MODEL() embedded in expression should be parsed correctly."""
        expr = '10 + MODEL("Simple", x: 5) * 2'
        parsed = value_engine._parse_expression(expr)

        assert parsed["valid"] is True
        assert "__model_0__" in parsed["modified"]
        assert len(parsed["model_calls"]) == 1

    def test_parse_multiple_models(self, value_engine):
        """Multiple MODEL() calls should be parsed correctly."""
        expr = 'MODEL("A", x: 1) + MODEL("B", y: 2)'
        parsed = value_engine._parse_expression(expr)

        assert parsed["valid"] is True
        assert len(parsed["model_calls"]) == 2
        assert "__model_0__" in parsed["modified"]
        assert "__model_1__" in parsed["modified"]


# =============================================================================
# Integration Tests (require database)
# =============================================================================

@pytest.mark.integration
class TestModelFunctionIntegration:
    """Integration tests that require database fixtures."""

    @pytest.fixture
    def db_session(self):
        """Create a test database session."""
        # This would be implemented with actual test database setup
        pytest.skip("Integration tests require database setup")

    def test_full_model_evaluation_flow(self, db_session):
        """Full MODEL() evaluation flow with real database."""
        # Create test model
        # Create ValueNode with MODEL() expression
        # Evaluate and verify result
        pass

    def test_model_with_dependencies(self, db_session):
        """MODEL() inputs depending on other ValueNodes."""
        pass

    def test_cascading_model_invalidation(self, db_session):
        """Changing a source should invalidate MODEL() outputs."""
        pass
