"""curveforge — Build Dirac Live target curves from research-grounded recipes."""

from curveforge.api import build_curve
from curveforge.curve import Curve
from curveforge.curves import get_curve, list_curves
from curveforge.output.targetcurve import (
    parse_targetcurve,
    serialize_targetcurve,
    write_targetcurve,
)
from curveforge.transforms import get_transform, list_transforms

__all__ = [
    "Curve",
    "__version__",
    "build_curve",
    "get_curve",
    "get_transform",
    "list_curves",
    "list_transforms",
    "parse_targetcurve",
    "serialize_targetcurve",
    "write_targetcurve",
]
__version__ = "0.1.0"
