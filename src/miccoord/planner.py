"""Candidate filtering and bounded deterministic frequency search."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from miccoord.intermod import audit_frequencies
from miccoord.model import InputError

MAX_CANDIDATES = 1000


@dataclass(frozen=True, slots=True)
class FrequencyRange:
    start_khz: int
    end_khz: int
    step_khz: int


@dataclass(frozen=True, slots=True)
class Exclusion:
    start_khz: int
    end_khz: int
    label: str


@dataclass(frozen=True, slots=True)
class ScanPoint:
    frequency_khz: int
    power_dbm: float


@dataclass(frozen=True, slots=True)
class PlanConfig:
    requested: int
    spares: int
    ranges: tuple[FrequencyRange, ...]
    minimum_spacing_khz: int
    intermod_guard_khz: int
    exclusions: tuple[Exclusion, ...]
    scan_threshold_dbm: float
    scan_guard_khz: int
    max_search_nodes: int


@dataclass(frozen=True, slots=True)
class CandidatePool:
    frequencies_khz: tuple[int, ...]
    generated: int
    excluded_by_ranges: int
    excluded_by_scan: int


@dataclass(frozen=True, slots=True)
class PlanResult:
    status: Literal["FOUND", "INFEASIBLE", "EXHAUSTED"]
    frequencies_khz: tuple[int, ...]
    requested_total: int
    candidate_count: int
    nodes_visited: int
    search_complete: bool
    excluded_by_ranges: int
    excluded_by_scan: int


def build_candidate_pool(config: PlanConfig, scan_points: tuple[ScanPoint, ...]) -> CandidatePool:
    """Generate the unique candidates allowed by declared ranges and evidence."""

    generated_values: set[int] = set()
    for allowed in config.ranges:
        generated_values.update(range(allowed.start_khz, allowed.end_khz + 1, allowed.step_khz))
    generated = len(generated_values)
    if generated > MAX_CANDIDATES:
        raise InputError(
            f"ranges generate {generated} candidates; the v0.1 limit is {MAX_CANDIDATES}"
        )

    after_ranges = tuple(
        frequency
        for frequency in sorted(generated_values)
        if not any(
            exclusion.start_khz <= frequency <= exclusion.end_khz for exclusion in config.exclusions
        )
    )
    active_scan = tuple(
        point for point in scan_points if point.power_dbm >= config.scan_threshold_dbm
    )
    after_scan = tuple(
        frequency
        for frequency in after_ranges
        if not any(
            abs(frequency - point.frequency_khz) <= config.scan_guard_khz for point in active_scan
        )
    )
    return CandidatePool(
        frequencies_khz=after_scan,
        generated=generated,
        excluded_by_ranges=generated - len(after_ranges),
        excluded_by_scan=len(after_ranges) - len(after_scan),
    )


def plan_frequencies(config: PlanConfig, scan_points: tuple[ScanPoint, ...]) -> PlanResult:
    """Find the first feasible set, or return an honest bounded-search result."""

    pool = build_candidate_pool(config, scan_points)
    target = config.requested + config.spares
    candidates = pool.frequencies_khz
    best: tuple[int, ...] = ()
    nodes_visited = 0
    exhausted = False

    def search(start: int, chosen: tuple[int, ...]) -> tuple[int, ...] | None:
        nonlocal best, exhausted, nodes_visited
        if len(chosen) > len(best) or (len(chosen) == len(best) and chosen < best):
            best = chosen
        if len(chosen) == target:
            return chosen
        if len(chosen) + len(candidates) - start < target:
            return None

        for index in range(start, len(candidates)):
            if nodes_visited >= config.max_search_nodes:
                exhausted = True
                return None
            nodes_visited += 1
            proposed = (*chosen, candidates[index])
            if audit_frequencies(
                proposed,
                minimum_spacing_khz=config.minimum_spacing_khz,
                intermod_guard_khz=config.intermod_guard_khz,
            ):
                continue
            found = search(index + 1, proposed)
            if found is not None:
                return found
            if exhausted:
                return None
        return None

    found = search(0, ())
    status: Literal["FOUND", "INFEASIBLE", "EXHAUSTED"]
    if found is not None:
        status = "FOUND"
        frequencies = found
    elif exhausted:
        status = "EXHAUSTED"
        frequencies = best
    else:
        status = "INFEASIBLE"
        frequencies = best
    return PlanResult(
        status=status,
        frequencies_khz=frequencies,
        requested_total=target,
        candidate_count=len(candidates),
        nodes_visited=nodes_visited,
        search_complete=not exhausted,
        excluded_by_ranges=pool.excluded_by_ranges,
        excluded_by_scan=pool.excluded_by_scan,
    )
