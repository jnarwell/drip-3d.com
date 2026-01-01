"""
MODEL() Function Parser Tests

Tests MODEL() pattern matching, parameter splitting, and binding parsing.
These tests use REAL implementations from value_engine.py.
"""

import pytest


class TestModelPatternMatching:
    """Test MODEL() regex pattern matching."""

    def test_simple_model_no_params(self, model_pattern):
        """MODEL("Name") with no parameters."""
        text = 'MODEL("Simple")'
        match = model_pattern.search(text)

        assert match is not None
        assert match.group(1) == "Simple"
        assert match.group(2) is None  # No parameters

    def test_simple_model_single_param(self, model_pattern):
        """MODEL("Name", x: 5) with one parameter."""
        text = 'MODEL("Simple", x: 5)'
        match = model_pattern.search(text)

        assert match is not None
        assert match.group(1) == "Simple"
        assert match.group(2) is not None
        assert "x: 5" in match.group(2)

    def test_model_multi_params(self, model_pattern):
        """MODEL with 3 parameters."""
        text = 'MODEL("Thermal Expansion", L0: 1, delta_T: 100, CTE: 2.3e-5)'
        match = model_pattern.search(text)

        assert match is not None
        assert match.group(1) == "Thermal Expansion"
        params = match.group(2)
        assert "L0: 1" in params
        assert "delta_T: 100" in params
        assert "CTE: 2.3e-5" in params

    def test_model_with_output_param(self, model_pattern):
        """MODEL with output parameter."""
        text = 'MODEL("Rectangle", length: 5, width: 3, output: "area")'
        match = model_pattern.search(text)

        assert match is not None
        assert match.group(1) == "Rectangle"
        assert 'output: "area"' in match.group(2)

    def test_model_with_references(self, model_pattern):
        """MODEL with #REF.prop parameters."""
        text = 'MODEL("Thermal", L0: #FRAME.length, delta_T: #SENSOR.temp, CTE: 2.3e-5)'
        match = model_pattern.search(text)

        assert match is not None
        assert "#FRAME.length" in match.group(2)
        assert "#SENSOR.temp" in match.group(2)

    def test_model_with_unit_values(self, model_pattern):
        """MODEL with values including units."""
        text = 'MODEL("Thermal", L0: 1m, delta_T: 100K, CTE: 23ppm/K)'
        match = model_pattern.search(text)

        assert match is not None
        assert "1m" in match.group(2)
        assert "100K" in match.group(2)

    def test_model_with_whitespace(self, model_pattern):
        """MODEL with various whitespace."""
        text = 'MODEL(  "Simple"  ,   x:   5  )'
        match = model_pattern.search(text)

        assert match is not None
        assert match.group(1) == "Simple"

    def test_model_in_expression(self, model_pattern):
        """MODEL embedded in larger expression."""
        text = '10 + MODEL("Simple", x: 5) * 2'
        match = model_pattern.search(text)

        assert match is not None
        assert match.group(1) == "Simple"

    def test_model_with_scientific_notation(self, model_pattern):
        """MODEL with scientific notation values."""
        text = 'MODEL("Thermal", CTE: 2.3e-5, delta_T: 1e2)'
        match = model_pattern.search(text)

        assert match is not None
        assert "2.3e-5" in match.group(2)
        assert "1e2" in match.group(2)

    def test_no_match_empty_model(self, model_pattern):
        """MODEL() with no name should not match."""
        text = 'MODEL()'
        match = model_pattern.search(text)

        assert match is None

    def test_no_match_unclosed_paren(self, model_pattern):
        """Unclosed parenthesis should not match."""
        text = 'MODEL("Name", x: 1'
        match = model_pattern.search(text)

        assert match is None

    def test_no_match_typo(self, model_pattern):
        """Typo in MODEL should not match."""
        text = 'MODL("Name", x: 1)'
        match = model_pattern.search(text)

        assert match is None

    def test_no_match_lowercase(self, model_pattern):
        """Lowercase model() should not match (case-sensitive)."""
        text = 'model("Name", x: 1)'
        match = model_pattern.search(text)

        assert match is None

    def test_no_match_missing_quotes(self, model_pattern):
        """Model name without quotes should not match."""
        text = 'MODEL(Name, x: 1)'
        match = model_pattern.search(text)

        assert match is None


class TestSplitModelParams:
    """Test _split_model_params() function."""

    def test_split_empty_string(self, split_model_params):
        """Empty string returns empty list."""
        result = split_model_params("")
        assert result == []

    def test_split_none(self, split_model_params):
        """None returns empty list."""
        result = split_model_params(None)
        assert result == []

    def test_split_single_param(self, split_model_params):
        """Single parameter."""
        result = split_model_params("x: 5")
        assert result == ["x: 5"]

    def test_split_two_params(self, split_model_params):
        """Two parameters."""
        result = split_model_params("x: 1, y: 2")
        assert result == ["x: 1", "y: 2"]

    def test_split_three_params(self, split_model_params):
        """Three parameters."""
        result = split_model_params("a: 1, b: 2, c: 3")
        assert result == ["a: 1", "b: 2", "c: 3"]

    def test_split_with_whitespace(self, split_model_params):
        """Parameters with extra whitespace."""
        result = split_model_params("  x: 1  ,  y: 2  ")
        assert result == ["x: 1", "y: 2"]

    def test_split_with_nested_model(self, split_model_params):
        """Nested MODEL() should not split on inner comma."""
        result = split_model_params('x: 1, y: MODEL("Inner", z: 2), w: 3')
        assert len(result) == 3
        assert result[0] == "x: 1"
        assert result[1] == 'y: MODEL("Inner", z: 2)'
        assert result[2] == "w: 3"

    def test_split_with_nested_lookup(self, split_model_params):
        """Nested LOOKUP() should not split on inner comma."""
        result = split_model_params('x: 1, y: LOOKUP("table", "col", key=1), z: 3')
        assert len(result) == 3
        assert 'LOOKUP("table", "col", key=1)' in result[1]

    def test_split_with_quoted_string(self, split_model_params):
        """Quoted strings with commas should not split."""
        result = split_model_params('name: "Hello, World", value: 5')
        assert len(result) == 2
        assert result[0] == 'name: "Hello, World"'
        assert result[1] == "value: 5"

    def test_split_with_output_param(self, split_model_params):
        """Output parameter with quoted value."""
        result = split_model_params('length: 5, width: 3, output: "area"')
        assert len(result) == 3
        assert 'output: "area"' in result[2]

    def test_split_scientific_notation(self, split_model_params):
        """Scientific notation values."""
        result = split_model_params("CTE: 2.3e-5, delta_T: 1e2")
        assert result == ["CTE: 2.3e-5", "delta_T: 1e2"]

    def test_split_with_references(self, split_model_params):
        """Property references."""
        result = split_model_params("x: #COMP.a, y: #COMP.b")
        assert result == ["x: #COMP.a", "y: #COMP.b"]


class TestParseModelBinding:
    """Test _parse_model_binding() function."""

    def test_parse_simple_binding(self, parse_model_binding):
        """Simple key: value binding."""
        key, value = parse_model_binding("x: 5")
        assert key == "x"
        assert value == "5"

    def test_parse_binding_with_spaces(self, parse_model_binding):
        """Binding with spaces around colon."""
        key, value = parse_model_binding("  x  :  10  ")
        assert key == "x"
        assert value == "10"

    def test_parse_scientific_notation(self, parse_model_binding):
        """Scientific notation value."""
        key, value = parse_model_binding("CTE: 2.3e-5")
        assert key == "CTE"
        assert value == "2.3e-5"

    def test_parse_negative_number(self, parse_model_binding):
        """Negative number value."""
        key, value = parse_model_binding("delta_T: -100")
        assert key == "delta_T"
        assert value == "-100"

    def test_parse_unit_value(self, parse_model_binding):
        """Value with unit."""
        key, value = parse_model_binding("length: 1m")
        assert key == "length"
        assert value == "1m"

    def test_parse_reference(self, parse_model_binding):
        """Property reference."""
        key, value = parse_model_binding("x: #COMP.prop")
        assert key == "x"
        assert value == "#COMP.prop"

    def test_parse_quoted_string(self, parse_model_binding):
        """Quoted string value (for output name)."""
        key, value = parse_model_binding('output: "area"')
        assert key == "output"
        assert value == '"area"'

    def test_parse_expression(self, parse_model_binding):
        """Expression value."""
        key, value = parse_model_binding("x: #A.val * 2 + 1")
        assert key == "x"
        assert value == "#A.val * 2 + 1"

    def test_parse_nested_model(self, parse_model_binding):
        """Nested MODEL() as value."""
        key, value = parse_model_binding('y: MODEL("Inner", z: 1)')
        assert key == "y"
        assert value == 'MODEL("Inner", z: 1)'

    def test_parse_no_colon_raises(self, parse_model_binding):
        """Missing colon should raise ValueError."""
        with pytest.raises(ValueError, match="missing ':'"):
            parse_model_binding("x 5")

    def test_parse_underscore_key(self, parse_model_binding):
        """Key with underscore."""
        key, value = parse_model_binding("delta_T: 100")
        assert key == "delta_T"
        assert value == "100"


class TestMultipleModelCalls:
    """Test extracting multiple MODEL() calls from expressions."""

    def test_two_models_in_expression(self, model_pattern):
        """Expression with two MODEL() calls."""
        text = 'MODEL("A", x: 1) + MODEL("B", y: 2)'

        matches = list(model_pattern.finditer(text))
        assert len(matches) == 2
        assert matches[0].group(1) == "A"
        assert matches[1].group(1) == "B"

    def test_nested_model_outer_only(self, model_pattern):
        """Nested MODEL() - outer match only with greedy regex."""
        text = 'MODEL("Outer", x: MODEL("Inner", y: 1))'

        # The regex is not designed to handle nested MODEL() properly yet
        # It will match the outer one
        match = model_pattern.search(text)
        assert match is not None
        assert match.group(1) == "Outer"

    def test_model_surrounded_by_text(self, model_pattern):
        """MODEL in middle of expression."""
        text = 'prefix + MODEL("Test", a: 1) * suffix'

        match = model_pattern.search(text)
        assert match is not None
        assert match.group(1) == "Test"
