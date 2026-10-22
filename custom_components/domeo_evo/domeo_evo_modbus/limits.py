"""The airflow ranges each unit size accepts, from the S&P register table."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from .enums import Model


@dataclass(frozen=True, kw_only=True)
class FlowLimits:
    """The inclusive airflow ranges, in m³/h, one unit size accepts."""

    low: tuple[int, int]
    """Holding 40007 (low airflow), and the minimum airflow of 40011 to 40016."""

    high: tuple[int, int]
    """Holding 40008 (high airflow)."""

    freecooling: tuple[int, int]
    """Holding 40009 (freecooling airflow)."""

    maximum: tuple[int, int]
    """The maximum airflow of the humidity regulation, 40017 to 40022."""


# The table leaves the 450's freecooling range blank and gives its maximum as
# 390 while its default is 395. The ranges below keep the defaults valid.
FLOW_LIMITS: dict[Model, FlowLimits] = {
    Model.DOMEO_EVO_225: FlowLimits(
        low=(60, 135), high=(120, 225), freecooling=(120, 225), maximum=(120, 225)
    ),
    Model.DOMEO_EVO_315: FlowLimits(
        low=(90, 225), high=(150, 315), freecooling=(150, 315), maximum=(150, 315)
    ),
    Model.DOMEO_EVO_450: FlowLimits(
        low=(135, 300), high=(195, 395), freecooling=(195, 395), maximum=(195, 395)
    ),
}


def check_range[N: (int, float)](name: str, value: N, limits: tuple[N, N]) -> N:
    """Return ``value`` if it lies in ``limits``, or raise ``ValueError``."""
    low, high = limits
    if not low <= value <= high:
        raise ValueError(f"{name} must be between {low} and {high}, got {value}")
    return value


def int_range(low: int, high: int) -> Callable[[Any], int]:
    """A field validator that accepts whole numbers from ``low`` to ``high``."""

    def _validate(value: Any) -> int:
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ValueError(f"expected a number, got {value!r}")
        if int(value) != value:
            raise ValueError(f"expected a whole number, got {value!r}")
        return check_range("value", int(value), (low, high))

    return _validate
