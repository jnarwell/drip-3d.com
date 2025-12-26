"""Table backend - handles discrete and continuous table lookups with interpolation."""

from typing import Dict, Any, List, Union
import math

from ..schemas import PropertySource, InputType, InterpMethod


class TableLookupError(Exception):
    """Error during table lookup."""
    pass


def interp_1d_linear(xs: List[float], ys: List[float], x: float) -> float:
    """1D linear interpolation."""
    if x < xs[0] or x > xs[-1]:
        raise TableLookupError(f"Value {x} outside range [{xs[0]}, {xs[-1]}]")

    # Find bracketing indices
    i = 0
    while i < len(xs) - 1 and xs[i + 1] < x:
        i += 1

    if xs[i] == x:
        return ys[i]

    # Linear interpolation
    t = (x - xs[i]) / (xs[i + 1] - xs[i])
    return ys[i] + t * (ys[i + 1] - ys[i])


def interp_1d_log(xs: List[float], ys: List[float], x: float) -> float:
    """1D log-log interpolation (for S-N curves, etc.)."""
    if x <= 0:
        raise TableLookupError(f"Log interpolation requires positive values, got {x}")

    # Convert to log space
    log_xs = [math.log10(xi) for xi in xs if xi > 0]
    log_ys = [math.log10(yi) for yi in ys if yi > 0]
    log_x = math.log10(x)

    log_y = interp_1d_linear(log_xs, log_ys, log_x)
    return 10 ** log_y


def interp_1d_step(xs: List[float], ys: List[float], x: float) -> float:
    """1D step interpolation (returns value of nearest lower point)."""
    if x < xs[0]:
        raise TableLookupError(f"Value {x} below minimum {xs[0]}")

    # Find largest x_i <= x
    i = 0
    while i < len(xs) - 1 and xs[i + 1] <= x:
        i += 1

    return ys[i]


def interp_2d_bilinear(
    xs: List[float],
    ys: List[float],
    zs: List[List[float]],
    x: float,
    y: float
) -> float:
    """2D bilinear interpolation."""
    # Find bracketing indices in x
    if x < xs[0] or x > xs[-1]:
        raise TableLookupError(f"x={x} outside range [{xs[0]}, {xs[-1]}]")
    if y < ys[0] or y > ys[-1]:
        raise TableLookupError(f"y={y} outside range [{ys[0]}, {ys[-1]}]")

    i = 0
    while i < len(xs) - 1 and xs[i + 1] < x:
        i += 1

    j = 0
    while j < len(ys) - 1 and ys[j + 1] < y:
        j += 1

    # Handle exact matches
    if i == len(xs) - 1:
        i -= 1
    if j == len(ys) - 1:
        j -= 1

    # Get the four corner values
    x0, x1 = xs[i], xs[i + 1]
    y0, y1 = ys[j], ys[j + 1]

    z00 = zs[j][i]
    z01 = zs[j][i + 1]
    z10 = zs[j + 1][i]
    z11 = zs[j + 1][i + 1]

    # Bilinear interpolation
    if x1 == x0:
        tx = 0
    else:
        tx = (x - x0) / (x1 - x0)

    if y1 == y0:
        ty = 0
    else:
        ty = (y - y0) / (y1 - y0)

    z0 = z00 + tx * (z01 - z00)
    z1 = z10 + tx * (z11 - z10)
    return z0 + ty * (z1 - z0)


def resolve_table(
    source: PropertySource,
    output_name: str,
    inputs: Dict[str, Any]
) -> Union[float, str]:
    """
    Resolve a table-based lookup.

    Handles:
    - Single discrete input: data[key][output]
    - Single continuous input: 1D interpolation
    - Two continuous inputs: 2D bilinear interpolation
    - Mixed discrete + continuous: filter by discrete, interpolate continuous
    """
    resolution = source.resolution
    data = resolution.data

    # Categorize inputs
    discrete_inputs = []
    continuous_inputs = []

    for input_def in source.inputs:
        if input_def.type == InputType.DISCRETE:
            discrete_inputs.append(input_def)
        else:
            continuous_inputs.append(input_def)

    # Case 1: Single discrete input (e.g., AISC shapes)
    if len(discrete_inputs) == 1 and len(continuous_inputs) == 0:
        input_def = discrete_inputs[0]
        key = inputs.get(input_def.name)
        if key is None:
            raise TableLookupError(f"Missing required input: {input_def.name}")

        key_str = str(key)
        if key_str not in data:
            raise TableLookupError(f"No match for {input_def.name}='{key}'")

        row = data[key_str]
        if output_name not in row:
            raise TableLookupError(f"Output '{output_name}' not found for {key_str}")

        value = row[output_name]
        # Return string values as-is, convert numeric values to float
        if isinstance(value, str):
            return value
        return float(value)

    # Case 2: Two discrete inputs (e.g., pipe schedules, tolerance grades)
    if len(discrete_inputs) == 2 and len(continuous_inputs) == 0:
        key_parts = []
        for input_def in discrete_inputs:
            val = inputs.get(input_def.name)
            if val is None:
                raise TableLookupError(f"Missing required input: {input_def.name}")
            key_parts.append(str(val))

        # Try compound key first (e.g., "IT7|10-18")
        key_str = "|".join(key_parts)
        if key_str in data:
            row = data[key_str]
            if output_name not in row:
                raise TableLookupError(f"Output '{output_name}' not found")
            value = row[output_name]
            if isinstance(value, str):
                return value
            return float(value)

        # Try nested lookup (e.g., data["IT7"]["10-18"])
        key1, key2 = key_parts
        if key1 in data and isinstance(data[key1], dict):
            if key2 in data[key1]:
                row = data[key1][key2]
                if output_name not in row:
                    raise TableLookupError(f"Output '{output_name}' not found")
                value = row[output_name]
                if isinstance(value, str):
                    return value
                return float(value)

        raise TableLookupError(f"No match for {discrete_inputs[0].name}='{key1}', {discrete_inputs[1].name}='{key2}'")

    # Case 3: Single continuous input (e.g., temp-dependent properties)
    if len(discrete_inputs) == 0 and len(continuous_inputs) == 1:
        input_def = continuous_inputs[0]
        x = inputs.get(input_def.name)
        if x is None:
            raise TableLookupError(f"Missing required input: {input_def.name}")

        x = float(x)

        # Data format: { "xs": [...], "output1": [...], "output2": [...] }
        # or { input_name: [...], output_name: [...] }
        xs_key = input_def.name if input_def.name in data else "xs"
        if xs_key not in data:
            raise TableLookupError(f"Table data missing grid for {input_def.name}")

        xs = [float(v) for v in data[xs_key]]
        if output_name not in data:
            raise TableLookupError(f"Output '{output_name}' not in table data")

        ys = [float(v) for v in data[output_name]]

        # Get interpolation method for this output
        output_def = next((o for o in source.outputs if o.name == output_name), None)
        interp = output_def.interp if output_def else input_def.interp

        if interp == InterpMethod.LOG:
            return interp_1d_log(xs, ys, x)
        elif interp == InterpMethod.STEP:
            return interp_1d_step(xs, ys, x)
        else:
            return interp_1d_linear(xs, ys, x)

    # Case 4: Two continuous inputs (e.g., steam tables with T, P)
    if len(discrete_inputs) == 0 and len(continuous_inputs) == 2:
        input1, input2 = continuous_inputs

        x = inputs.get(input1.name)
        y = inputs.get(input2.name)

        if x is None:
            raise TableLookupError(f"Missing required input: {input1.name}")
        if y is None:
            raise TableLookupError(f"Missing required input: {input2.name}")

        x = float(x)
        y = float(y)

        # Data format: { "xs": [...], "ys": [...], "output": [[...], [...], ...] }
        xs_key = input1.name if input1.name in data else "xs"
        ys_key = input2.name if input2.name in data else "ys"

        xs = [float(v) for v in data[xs_key]]
        ys = [float(v) for v in data[ys_key]]

        if output_name not in data:
            raise TableLookupError(f"Output '{output_name}' not in table data")

        zs = [[float(v) for v in row] for row in data[output_name]]

        return interp_2d_bilinear(xs, ys, zs, x, y)

    # Case 5: Mixed discrete + continuous
    if len(discrete_inputs) >= 1 and len(continuous_inputs) >= 1:
        # Build discrete key to filter data subset
        key_parts = []
        for input_def in discrete_inputs:
            val = inputs.get(input_def.name)
            if val is None:
                raise TableLookupError(f"Missing required input: {input_def.name}")
            key_parts.append(str(val))

        discrete_key = "|".join(key_parts)

        if discrete_key not in data:
            raise TableLookupError(f"No data for {discrete_key}")

        subset = data[discrete_key]

        # Now interpolate on continuous inputs within this subset
        # Recursively call with subset data
        subset_source = PropertySource(
            **{
                **source.model_dump(),
                'inputs': continuous_inputs,
                'resolution': {'type': 'table', 'data': subset}
            }
        )

        continuous_inputs_dict = {
            k: v for k, v in inputs.items()
            if k in [i.name for i in continuous_inputs]
        }

        return resolve_table(subset_source, output_name, continuous_inputs_dict)

    raise TableLookupError(
        f"Unsupported input configuration: {len(discrete_inputs)} discrete, "
        f"{len(continuous_inputs)} continuous"
    )
