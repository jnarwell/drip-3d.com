"""Pydantic schemas for PropertySource definitions."""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Union, Literal
from enum import Enum


class Category(str, Enum):
    STRUCTURAL = "structural"
    MATERIAL = "material"
    MECHANICAL = "mechanical"
    PROCESS = "process"
    ELECTRICAL = "electrical"
    STANDARDS = "standards"
    FASTENERS = "fasteners"
    TOLERANCES = "tolerances"
    FINISHES = "finishes"


class InterpMethod(str, Enum):
    LINEAR = "linear"
    LOG = "log"
    STEP = "step"
    SPLINE = "spline"


class ExtrapMethod(str, Enum):
    ERROR = "error"
    CLAMP = "clamp"
    EXTRAPOLATE = "extrapolate"


class InputType(str, Enum):
    CONTINUOUS = "continuous"
    DISCRETE = "discrete"


class InputDef(BaseModel):
    """Definition of an input (independent variable)."""
    name: str
    unit: str = "none"
    description: Optional[str] = None
    type: InputType = InputType.CONTINUOUS
    optional: bool = False  # If True, input is not required

    # For continuous inputs
    range: Optional[tuple[float, float]] = None
    values: Optional[List[Union[str, float, int]]] = None  # Grid points for continuous, allowed values for discrete

    # Interpolation/extrapolation
    interp: InterpMethod = InterpMethod.LINEAR
    extrap: ExtrapMethod = ExtrapMethod.ERROR


class OutputDef(BaseModel):
    """Definition of an output (dependent variable/property)."""
    name: str
    unit: str
    description: Optional[str] = None
    interp: InterpMethod = InterpMethod.LINEAR
    format: Optional[str] = None  # e.g., "0.00", "scientific"
    uncertainty: Optional[float] = None
    uncertainty_type: Optional[Literal["absolute", "percentage"]] = None


# Resolution types for different backends

class TableResolution(BaseModel):
    """Resolution for table-based lookups."""
    type: Literal["table"] = "table"
    data: Dict[str, Any]  # Structure varies by input count/type


class EquationResolution(BaseModel):
    """Resolution for equation-based lookups."""
    type: Literal["equation"] = "equation"
    formulas: Dict[str, str]  # output_name -> formula string
    constants: Dict[str, Any] = {}  # Named constants for formulas


class LibraryResolution(BaseModel):
    """Resolution for library-based lookups (e.g., CoolProp)."""
    type: Literal["library"] = "library"
    library: str = "coolprop"
    fluid: Optional[str] = None
    backend: Optional[str] = None
    output_mapping: Dict[str, str] = {}  # our name -> library name
    input_mapping: Dict[str, str] = {}   # our name -> library name


Resolution = Union[TableResolution, EquationResolution, LibraryResolution]


# View configuration for generating browsable tables

class GridSpec(BaseModel):
    """Specification for grid points in a view."""
    type: Literal["list", "range", "computed"] = "list"
    values: Optional[List[Union[float, int, str]]] = None
    start: Optional[float] = None
    end: Optional[float] = None
    step: Optional[float] = None
    compute: Optional[str] = None  # Expression for computed grids
    unit: Optional[str] = None  # Display unit


class ColumnDef(BaseModel):
    """Definition of a column in a view."""
    output: Optional[str] = None
    computed: Optional[str] = None  # e.g., "h_vapor - h_liquid"
    header: str
    subscript: Optional[str] = None
    phase: Optional[Literal["liquid", "vapor"]] = None
    unit: Optional[str] = None
    format: Optional[str] = None


class ViewConfig(BaseModel):
    """Configuration for generating a browsable table view."""
    id: str
    name: str
    description: Optional[str] = None
    grid: Dict[str, GridSpec]
    constraints: Dict[str, Any] = {}
    columns: List[ColumnDef]
    layout: Literal["flat", "nested"] = "flat"


class PropertySource(BaseModel):
    """Root schema for a property source definition."""
    # Identification
    id: str
    name: str
    category: Category
    description: Optional[str] = None

    # Provenance
    source: str
    source_url: Optional[str] = None
    version: str = "1.0"
    last_updated: Optional[str] = None

    # Type discriminator
    type: Literal["table", "equation", "library"]

    # Optional reference to a different source for LOOKUP()
    # When set, the LOOKUP template will use this source_id instead of self.id
    lookup_source_id: Optional[str] = None

    # Inputs and outputs
    inputs: List[InputDef]
    outputs: List[OutputDef]

    # Resolution (type-specific)
    resolution: Resolution

    # Display configuration
    views: List[ViewConfig] = []

    class Config:
        use_enum_values = True
