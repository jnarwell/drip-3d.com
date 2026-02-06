"""
Tests for specific ValueEngine bugs:
1. Space sensitivity in expressions
2. Dimension inference for power expressions
3. Volume (product) calculations

These tests use mocked database to avoid integration complexity.
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from unittest.mock import MagicMock, patch
import sympy as sp
from sympy import Symbol

from app.services.dimensional_analysis import (
    Dimension, DIMENSIONLESS, LENGTH, AREA, VOLUME,
    dimension_to_string, dimension_to_si_unit
)


class TestValueEngineParseExpression:
    """Test ValueEngine._parse_expression for edge cases."""

    def test_parse_expression_caret_no_space(self):
        """Test parsing #REF.Height^2 (no space)."""
        from app.services.value_engine import ValueEngine

        # Create mock db session
        mock_db = MagicMock()
        engine = ValueEngine(mock_db)

        # Mock _get_reference_unit to return 'mm'
        engine._get_reference_unit = MagicMock(return_value='mm')

        expression = "#COMPONENT.Height^2"
        result = engine._parse_expression(expression)

        assert result['valid'] == True
        assert '**' in result['modified']  # ^ converted to **
        assert '^' not in result['modified']  # no ^ left
        assert '__ref_0__' in result['modified']

    def test_parse_expression_caret_with_space(self):
        """Test parsing #REF.Height ^2 (space before caret)."""
        from app.services.value_engine import ValueEngine

        mock_db = MagicMock()
        engine = ValueEngine(mock_db)
        engine._get_reference_unit = MagicMock(return_value='mm')

        expression = "#COMPONENT.Height ^2"
        result = engine._parse_expression(expression)

        assert result['valid'] == True
        assert '**' in result['modified']
        assert '^' not in result['modified']

    def test_parse_expression_triple_product(self):
        """Test parsing #R.Height * #R.Width * #R.Depth."""
        from app.services.value_engine import ValueEngine

        mock_db = MagicMock()
        engine = ValueEngine(mock_db)
        engine._get_reference_unit = MagicMock(return_value='mm')

        expression = "#R.Height * #R.Width * #R.Depth"
        result = engine._parse_expression(expression)

        assert result['valid'] == True
        assert '__ref_0__' in result['modified']
        assert '__ref_1__' in result['modified']
        assert '__ref_2__' in result['modified']
        assert len(result['references']) == 3


class TestValueEngineComputeExpressionDimension:
    """Test ValueEngine._compute_expression_dimension."""

    def test_dimension_of_height_squared(self):
        """Test dimension computation for Height^2."""
        from app.services.value_engine import ValueEngine

        mock_db = MagicMock()
        engine = ValueEngine(mock_db)
        engine._get_reference_unit = MagicMock(return_value='mm')

        # Create a parsed expression dict
        parsed = {
            'original': '#REF.Height^2',
            'modified': '__ref_0__**2',
            'placeholders': {'__ref_0__': 'REF.Height'},
            'ref_units': {'__ref_0__': 'mm'},
            'literal_values': {},
            'bare_literals': {},
            'lookup_calls': {},
            'model_calls': {},
            'references': ['REF.Height'],
            'valid': True
        }

        dimension, error = engine._compute_expression_dimension(parsed)

        # mm^2 should give AREA (L^2)
        assert dimension is not None, f"Dimension computation failed: {error}"
        assert dimension == AREA, f"Expected AREA, got {dimension_to_string(dimension)}"

    def test_dimension_of_height_squared_with_space(self):
        """Test dimension computation for Height ^2 (space before ^)."""
        from app.services.value_engine import ValueEngine

        mock_db = MagicMock()
        engine = ValueEngine(mock_db)
        engine._get_reference_unit = MagicMock(return_value='mm')

        # Note: space in expression doesn't change the modified expr after ^ conversion
        parsed = {
            'original': '#REF.Height ^2',
            'modified': '__ref_0__ **2',  # Space preserved between placeholder and **
            'placeholders': {'__ref_0__': 'REF.Height'},
            'ref_units': {'__ref_0__': 'mm'},
            'literal_values': {},
            'bare_literals': {},
            'lookup_calls': {},
            'model_calls': {},
            'references': ['REF.Height'],
            'valid': True
        }

        dimension, error = engine._compute_expression_dimension(parsed)

        # Should still give AREA
        assert dimension is not None, f"Dimension computation failed: {error}"
        assert dimension == AREA, f"Expected AREA, got {dimension_to_string(dimension)}"

    def test_dimension_of_volume_triple_product(self):
        """Test dimension computation for Height * Width * Depth = Volume."""
        from app.services.value_engine import ValueEngine

        mock_db = MagicMock()
        engine = ValueEngine(mock_db)
        engine._get_reference_unit = MagicMock(return_value='mm')

        parsed = {
            'original': '#R.Height * #R.Width * #R.Depth',
            'modified': '__ref_0__ * __ref_1__ * __ref_2__',
            'placeholders': {
                '__ref_0__': 'R.Height',
                '__ref_1__': 'R.Width',
                '__ref_2__': 'R.Depth',
            },
            'ref_units': {
                '__ref_0__': 'mm',
                '__ref_1__': 'mm',
                '__ref_2__': 'mm',
            },
            'literal_values': {},
            'bare_literals': {},
            'lookup_calls': {},
            'model_calls': {},
            'references': ['R.Height', 'R.Width', 'R.Depth'],
            'valid': True
        }

        dimension, error = engine._compute_expression_dimension(parsed)

        # L * L * L = L^3 = VOLUME
        assert dimension is not None, f"Dimension computation failed: {error}"
        assert dimension == VOLUME, f"Expected VOLUME, got {dimension_to_string(dimension)}"


class TestInferDimensionFromExpr:
    """Test ValueEngine._infer_dimension_from_expr directly."""

    def test_infer_simple_power(self):
        """Test inferring dimension for __ref_0__**2."""
        from app.services.value_engine import ValueEngine

        mock_db = MagicMock()
        engine = ValueEngine(mock_db)

        placeholder_dims = {'__ref_0__': LENGTH}
        result = engine._infer_dimension_from_expr('__ref_0__**2', placeholder_dims)

        assert result == AREA, f"Expected AREA, got {dimension_to_string(result)}"

    def test_infer_power_with_space(self):
        """Test inferring dimension for __ref_0__ **2 (space before **)."""
        from app.services.value_engine import ValueEngine

        mock_db = MagicMock()
        engine = ValueEngine(mock_db)

        placeholder_dims = {'__ref_0__': LENGTH}
        result = engine._infer_dimension_from_expr('__ref_0__ **2', placeholder_dims)

        assert result == AREA, f"Expected AREA, got {dimension_to_string(result)}"

    def test_infer_triple_product(self):
        """Test inferring dimension for __ref_0__ * __ref_1__ * __ref_2__."""
        from app.services.value_engine import ValueEngine

        mock_db = MagicMock()
        engine = ValueEngine(mock_db)

        placeholder_dims = {
            '__ref_0__': LENGTH,
            '__ref_1__': LENGTH,
            '__ref_2__': LENGTH,
        }
        result = engine._infer_dimension_from_expr(
            '__ref_0__ * __ref_1__ * __ref_2__',
            placeholder_dims
        )

        assert result == VOLUME, f"Expected VOLUME, got {dimension_to_string(result)}"

    def test_infer_dimension_with_missing_placeholder(self):
        """Test that missing placeholder in dims returns DIMENSIONLESS."""
        from app.services.value_engine import ValueEngine

        mock_db = MagicMock()
        engine = ValueEngine(mock_db)

        # __ref_0__ is NOT in placeholder_dims
        placeholder_dims = {}
        result = engine._infer_dimension_from_expr('__ref_0__**2', placeholder_dims)

        # When placeholder isn't found, it should default to DIMENSIONLESS
        # And DIMENSIONLESS^2 = DIMENSIONLESS
        assert result == DIMENSIONLESS, f"Expected DIMENSIONLESS, got {dimension_to_string(result)}"


class TestUnitSymbolToSIUnit:
    """Test that dimension_to_si_unit works for computed dimensions."""

    def test_area_to_m2(self):
        """AREA dimension should map to m²."""
        result = dimension_to_si_unit(AREA)
        assert result == 'm²', f"Expected 'm²', got '{result}'"

    def test_volume_to_m3(self):
        """VOLUME dimension should map to m³."""
        result = dimension_to_si_unit(VOLUME)
        assert result == 'm³', f"Expected 'm³', got '{result}'"

    def test_computed_area_to_m2(self):
        """Computed LENGTH**2 should map to m²."""
        computed = LENGTH ** 2
        result = dimension_to_si_unit(computed)
        assert result == 'm²', f"Expected 'm²', got '{result}'"

    def test_computed_volume_to_m3(self):
        """Computed LENGTH**3 should map to m³."""
        computed = LENGTH ** 3
        result = dimension_to_si_unit(computed)
        assert result == 'm³', f"Expected 'm³', got '{result}'"


class TestMissingUnitHandling:
    """Test behavior when unit information is missing."""

    def test_missing_unit_produces_warning(self, caplog):
        """Test that missing unit info produces a warning log."""
        import logging
        from app.services.value_engine import ValueEngine

        mock_db = MagicMock()
        engine = ValueEngine(mock_db)

        # Mock _get_reference_unit to return None (unit not found)
        engine._get_reference_unit = MagicMock(return_value=None)
        # Mock _resolve_reference to return None (no ValueNode)
        engine._resolve_reference = MagicMock(return_value=None)

        with caplog.at_level(logging.WARNING):
            result = engine._parse_expression('#REF.Height^2')
            dim, err = engine._compute_expression_dimension(result)

        # Check that a warning was logged about missing unit info
        assert any("No unit info" in record.message for record in caplog.records), \
            "Expected a warning about missing unit info"

        # The dimension should be DIMENSIONLESS (fallback behavior)
        assert dim == DIMENSIONLESS

    def test_dimension_with_fallback_from_valuenode(self):
        """Test that dimension is correctly inferred from ValueNode.computed_unit_symbol."""
        from app.services.value_engine import ValueEngine

        mock_db = MagicMock()
        engine = ValueEngine(mock_db)

        # Mock _get_reference_unit to return None (no PropertyDefinition)
        engine._get_reference_unit = MagicMock(return_value=None)

        # Mock _resolve_reference to return a ValueNode WITH computed_unit_symbol
        mock_node = MagicMock()
        mock_node.computed_unit_symbol = 'mm'
        engine._resolve_reference = MagicMock(return_value=mock_node)

        result = engine._parse_expression('#REF.Height^2')
        dim, err = engine._compute_expression_dimension(result)

        # Should correctly infer AREA from the fallback
        assert dim == AREA, f"Expected AREA, got {dimension_to_string(dim)}"


class TestCreateLiteralWithUnit:
    """Test that create_literal properly sets computed_unit_symbol."""

    def test_create_literal_without_unit(self):
        """create_literal without unit_id should not set computed_unit_symbol."""
        from app.services.value_engine import ValueEngine
        from app.models.values import ValueNode

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = None
        mock_db.add = MagicMock()
        mock_db.flush = MagicMock()

        engine = ValueEngine(mock_db)

        # Capture the ValueNode that gets created
        created_node = None
        def capture_add(node):
            nonlocal created_node
            created_node = node
        mock_db.add.side_effect = capture_add

        engine.create_literal(value=10.0)

        assert created_node is not None
        assert created_node.computed_unit_symbol is None

    def test_create_literal_with_unit(self):
        """create_literal with unit_id should set computed_unit_symbol."""
        from app.services.value_engine import ValueEngine
        from app.models.values import ValueNode

        # Mock unit lookup
        mock_unit = MagicMock()
        mock_unit.symbol = 'mm'

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = mock_unit
        mock_db.add = MagicMock()
        mock_db.flush = MagicMock()

        engine = ValueEngine(mock_db)

        # Capture the ValueNode that gets created
        created_node = None
        def capture_add(node):
            nonlocal created_node
            created_node = node
        mock_db.add.side_effect = capture_add

        engine.create_literal(value=10.0, unit_id=1)

        assert created_node is not None
        assert created_node.computed_unit_symbol == 'mm'


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
