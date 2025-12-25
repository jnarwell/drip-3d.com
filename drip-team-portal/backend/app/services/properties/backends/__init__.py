"""Backend resolvers for different property source types."""

from .table import resolve_table
from .equation import resolve_equation
from .coolprop import resolve_coolprop

__all__ = ['resolve_table', 'resolve_equation', 'resolve_coolprop']
