"""Validated domain values shared by MicCoord commands."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import Literal

ConflictKind = Literal[
    "carrier_spacing",
    "two_tone_third_order",
    "three_tone_third_order",
]
MAX_FREQUENCY_MHZ = Decimal("100000")


class InputError(ValueError):
    """Raised when external input violates MicCoord's public contract."""


def parse_mhz_to_khz(value: object, field: str) -> int:
    """Parse a positive whole-kHz MHz value without binary float arithmetic."""

    message = f"{field} must be from 0.001 to 100000.000 MHz at whole-kHz precision"
    if isinstance(value, bool) or value is None:
        raise InputError(message)
    try:
        mhz = Decimal(str(value))
    except (InvalidOperation, ValueError):
        raise InputError(message) from None
    if not mhz.is_finite() or mhz <= 0 or mhz > MAX_FREQUENCY_MHZ:
        raise InputError(message)
    khz = mhz * 1000
    if khz != khz.to_integral_value():
        raise InputError(message)
    return int(khz)


def format_mhz(frequency_khz: int) -> str:
    """Render an internal kHz value as stable three-decimal MHz text."""

    whole, fraction = divmod(frequency_khz, 1000)
    return f"{whole}.{fraction:03d}"


@dataclass(frozen=True, slots=True)
class Conflict:
    """One exact reason a carrier set violates its declared model."""

    kind: ConflictKind
    sources_khz: tuple[int, ...]
    target_khz: int
    product_khz: int | None
    separation_khz: int
    required_separation_khz: int
    expression: str

    def to_dict(self) -> dict[str, object]:
        return {
            "kind": self.kind,
            "sources_mhz": [format_mhz(value) for value in self.sources_khz],
            "target_mhz": format_mhz(self.target_khz),
            "product_mhz": (format_mhz(self.product_khz) if self.product_khz is not None else None),
            "separation_khz": self.separation_khz,
            "required_separation_khz": self.required_separation_khz,
            "expression": self.expression,
        }
