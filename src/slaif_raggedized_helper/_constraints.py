"""Shared strict numeric constraints: finite and positive budgets only."""

from __future__ import annotations

import math
from typing import Annotated

from pydantic import AfterValidator, Field


def _positive_finite(value: float) -> float:
    if not math.isfinite(value):
        raise ValueError("must be finite (no NaN/Inf budgets)")
    if value <= 0:
        raise ValueError("must be strictly positive")
    return value


PositiveFiniteFloat = Annotated[float, AfterValidator(_positive_finite)]
PositiveInt = Annotated[int, Field(gt=0)]


def _non_negative(value: int) -> int:
    if value < 0:
        raise ValueError("counts must be non-negative (missing counts stay null, never negative)")
    return value


# Measured counts may legitimately be zero; missing counts must be null.
NonNegativeInt = Annotated[int, AfterValidator(_non_negative)]
