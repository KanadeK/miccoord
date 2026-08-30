"""Exact carrier-spacing and third-order intermodulation evidence."""

from __future__ import annotations

from itertools import combinations

from miccoord.model import Conflict, format_mhz


def _conflict_key(conflict: Conflict) -> tuple[object, ...]:
    order = {
        "carrier_spacing": 0,
        "two_tone_third_order": 1,
        "three_tone_third_order": 2,
    }
    return (
        order[conflict.kind],
        conflict.target_khz,
        conflict.product_khz if conflict.product_khz is not None else -1,
        conflict.sources_khz,
        conflict.expression,
    )


def audit_frequencies(
    frequencies_khz: tuple[int, ...],
    *,
    minimum_spacing_khz: int,
    intermod_guard_khz: int,
) -> tuple[Conflict, ...]:
    """Return every spacing or third-order conflict under the declared margins."""

    frequencies = tuple(sorted(frequencies_khz))
    conflicts: dict[tuple[object, ...], Conflict] = {}

    for first, second in combinations(frequencies, 2):
        separation = second - first
        if separation < minimum_spacing_khz:
            conflict = Conflict(
                kind="carrier_spacing",
                sources_khz=(first, second),
                target_khz=second,
                product_khz=None,
                separation_khz=separation,
                required_separation_khz=minimum_spacing_khz,
                expression=f"{format_mhz(second)}-{format_mhz(first)}",
            )
            conflicts[_conflict_key(conflict)] = conflict

    for first, second in combinations(frequencies, 2):
        pair_products = (
            (2 * first - second, f"2*{format_mhz(first)}-{format_mhz(second)}"),
            (2 * second - first, f"2*{format_mhz(second)}-{format_mhz(first)}"),
        )
        for product, expression in pair_products:
            for target in frequencies:
                separation = abs(product - target)
                if separation < intermod_guard_khz:
                    conflict = Conflict(
                        kind="two_tone_third_order",
                        sources_khz=(first, second),
                        target_khz=target,
                        product_khz=product,
                        separation_khz=separation,
                        required_separation_khz=intermod_guard_khz,
                        expression=expression,
                    )
                    conflicts[_conflict_key(conflict)] = conflict

    for first, second, third in combinations(frequencies, 3):
        triple_products = (
            (
                first + second - third,
                f"{format_mhz(first)}+{format_mhz(second)}-{format_mhz(third)}",
            ),
            (
                first + third - second,
                f"{format_mhz(first)}+{format_mhz(third)}-{format_mhz(second)}",
            ),
            (
                second + third - first,
                f"{format_mhz(second)}+{format_mhz(third)}-{format_mhz(first)}",
            ),
        )
        for product, expression in triple_products:
            for target in frequencies:
                separation = abs(product - target)
                if separation < intermod_guard_khz:
                    conflict = Conflict(
                        kind="three_tone_third_order",
                        sources_khz=(first, second, third),
                        target_khz=target,
                        product_khz=product,
                        separation_khz=separation,
                        required_separation_khz=intermod_guard_khz,
                        expression=expression,
                    )
                    conflicts[_conflict_key(conflict)] = conflict

    return tuple(sorted(conflicts.values(), key=_conflict_key))
