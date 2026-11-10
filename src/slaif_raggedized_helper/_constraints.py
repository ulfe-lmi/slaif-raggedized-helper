"""Shared strict numeric constraints: finite and positive budgets, and
finite nonnegative measured values (a measured zero is a real value)."""

from __future__ import annotations

import math
from typing import Annotated

from pydantic import AfterValidator, BeforeValidator, Field


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


def _reject_bool(value: object) -> object:
    # bool is an int subtype that pydantic lax mode would otherwise coerce
    # to 1.0; a boolean is never a measured duration/count.
    if isinstance(value, bool):
        raise ValueError("boolean is not a measured numeric value")
    return value


def _nonneg_finite(value: float) -> float:
    if not math.isfinite(value):
        raise ValueError("measured values must be finite (no NaN/Inf)")
    if value < 0:
        raise ValueError("measured values must be non-negative")
    return value


# A measured reported zero is a known zero (0.0), never null; missing
# values must stay null. Unrepresentable values (e.g. ints beyond the
# float range) are rejected by pydantic float validation itself.
NonNegativeFiniteFloat = Annotated[
    float, BeforeValidator(_reject_bool), AfterValidator(_nonneg_finite)
]
