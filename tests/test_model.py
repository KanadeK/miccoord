from decimal import Decimal

import pytest

from miccoord.model import InputError, format_mhz, parse_mhz_to_khz


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("470.125", 470_125),
        (470, 470_000),
        (470.125, 470_125),
        (Decimal("470.125"), 470_125),
    ],
)
def test_parse_mhz_to_khz_accepts_exact_whole_khz_values(value: object, expected: int) -> None:
    assert parse_mhz_to_khz(value, "frequency") == expected


@pytest.mark.parametrize("value", [True, "470.1255", "not-a-frequency", 0, -1, None])
def test_parse_mhz_to_khz_rejects_ambiguous_or_invalid_values(value: object) -> None:
    with pytest.raises(InputError, match="frequency"):
        parse_mhz_to_khz(value, "frequency")


def test_format_mhz_has_stable_three_decimal_places() -> None:
    assert format_mhz(470_125) == "470.125"
    assert format_mhz(470_000) == "470.000"
