"""Strict JSON and CSV boundary parsing for MicCoord."""

from __future__ import annotations

import csv
import json
import math
from dataclasses import dataclass
from json import JSONDecodeError
from pathlib import Path
from typing import cast

from miccoord.model import InputError, parse_mhz_to_khz
from miccoord.planner import Exclusion, FrequencyRange, PlanConfig, ScanPoint

MAX_JSON_BYTES = 1_000_000
MAX_SCAN_BYTES = 5_000_000
MAX_SCAN_ROWS = 100_000


@dataclass(frozen=True, slots=True)
class AuditConfig:
    frequencies_khz: tuple[int, ...]
    minimum_spacing_khz: int
    intermod_guard_khz: int


def _read_text(path: Path, *, limit: int, label: str) -> str:
    try:
        size = path.stat().st_size
        if size > limit:
            raise InputError(f"{label} exceeds the {limit}-byte limit")
        return path.read_text(encoding="utf-8-sig")
    except InputError:
        raise
    except (OSError, UnicodeError) as error:
        raise InputError(f"cannot read {label} {path}: {error}") from None


def _load_json_object(path: Path, label: str) -> dict[str, object]:
    text = _read_text(path, limit=MAX_JSON_BYTES, label=label)
    try:
        value = json.loads(text)
    except JSONDecodeError as error:
        raise InputError(
            f"{label} is not valid JSON: line {error.lineno}, column {error.colno}"
        ) from None
    except ValueError:
        raise InputError(f"{label} contains a numeric value beyond the parser limit") from None
    if not isinstance(value, dict):
        raise InputError(f"{label} root must be a JSON object")
    return cast(dict[str, object], value)


def _object(value: object, field: str) -> dict[str, object]:
    if not isinstance(value, dict):
        raise InputError(f"{field} must be an object")
    return cast(dict[str, object], value)


def _list(value: object, field: str) -> list[object]:
    if not isinstance(value, list):
        raise InputError(f"{field} must be an array")
    return cast(list[object], value)


def _reject_unknown(payload: dict[str, object], allowed: set[str], field: str) -> None:
    unknown = sorted(payload.keys() - allowed)
    if unknown:
        raise InputError(f"{field} has unknown field(s): {', '.join(unknown)}")


def _bounded_int(value: object, field: str, minimum: int, maximum: int) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise InputError(f"{field} must be an integer from {minimum} to {maximum}")
    if not minimum <= value <= maximum:
        raise InputError(f"{field} must be an integer from {minimum} to {maximum}")
    return value


def _finite_float(value: object, field: str, minimum: float, maximum: float) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float, str)):
        raise InputError(f"{field} must be a finite number from {minimum} to {maximum}")
    try:
        number = float(value)
    except ValueError:
        raise InputError(f"{field} must be a finite number from {minimum} to {maximum}") from None
    if not math.isfinite(number) or not minimum <= number <= maximum:
        raise InputError(f"{field} must be a finite number from {minimum} to {maximum}")
    return number


def load_plan_config(path: Path) -> PlanConfig:
    payload = _load_json_object(path, "plan input")
    allowed = {
        "requested",
        "spares",
        "ranges",
        "minimum_spacing_khz",
        "intermod_guard_khz",
        "exclusions",
        "scan_threshold_dbm",
        "scan_guard_khz",
        "max_search_nodes",
    }
    _reject_unknown(payload, allowed, "plan input")
    if "requested" not in payload or "ranges" not in payload:
        raise InputError("plan input requires requested and ranges")

    requested = _bounded_int(payload["requested"], "requested", 1, 20)
    spares = _bounded_int(payload.get("spares", 0), "spares", 0, 19)
    if requested + spares > 20:
        raise InputError("requested plus spares must not exceed 20")

    raw_ranges = _list(payload["ranges"], "ranges")
    if not 1 <= len(raw_ranges) <= 8:
        raise InputError("ranges must contain from 1 to 8 entries")
    ranges: list[FrequencyRange] = []
    for index, raw_range in enumerate(raw_ranges):
        item = _object(raw_range, f"ranges[{index}]")
        _reject_unknown(item, {"start_mhz", "end_mhz", "step_khz"}, f"ranges[{index}]")
        if item.keys() != {"start_mhz", "end_mhz", "step_khz"}:
            raise InputError(f"ranges[{index}] requires start_mhz, end_mhz, and step_khz")
        start = parse_mhz_to_khz(item["start_mhz"], f"ranges[{index}].start_mhz")
        end = parse_mhz_to_khz(item["end_mhz"], f"ranges[{index}].end_mhz")
        if start > end:
            raise InputError(f"ranges[{index}].start_mhz must not exceed end_mhz")
        step = _bounded_int(item["step_khz"], f"ranges[{index}].step_khz", 1, 5_000)
        ranges.append(FrequencyRange(start, end, step))

    raw_exclusions = _list(payload.get("exclusions", []), "exclusions")
    if len(raw_exclusions) > 100:
        raise InputError("exclusions must contain at most 100 entries")
    exclusions: list[Exclusion] = []
    for index, raw_exclusion in enumerate(raw_exclusions):
        item = _object(raw_exclusion, f"exclusions[{index}]")
        _reject_unknown(
            item,
            {"start_mhz", "end_mhz", "label"},
            f"exclusions[{index}]",
        )
        if item.keys() != {"start_mhz", "end_mhz", "label"}:
            raise InputError(f"exclusions[{index}] requires start_mhz, end_mhz, and label")
        label = item["label"]
        if not isinstance(label, str) or not 1 <= len(label.strip()) <= 100:
            raise InputError(f"exclusions[{index}].label must contain from 1 to 100 characters")
        start = parse_mhz_to_khz(item["start_mhz"], f"exclusions[{index}].start_mhz")
        end = parse_mhz_to_khz(item["end_mhz"], f"exclusions[{index}].end_mhz")
        if start > end:
            raise InputError(f"exclusions[{index}].start_mhz must not exceed end_mhz")
        exclusions.append(Exclusion(start, end, label.strip()))

    return PlanConfig(
        requested=requested,
        spares=spares,
        ranges=tuple(ranges),
        minimum_spacing_khz=_bounded_int(
            payload.get("minimum_spacing_khz", 200), "minimum_spacing_khz", 1, 5_000
        ),
        intermod_guard_khz=_bounded_int(
            payload.get("intermod_guard_khz", 250), "intermod_guard_khz", 1, 5_000
        ),
        exclusions=tuple(exclusions),
        scan_threshold_dbm=_finite_float(
            payload.get("scan_threshold_dbm", -75), "scan_threshold_dbm", -200, 100
        ),
        scan_guard_khz=_bounded_int(payload.get("scan_guard_khz", 100), "scan_guard_khz", 0, 5_000),
        max_search_nodes=_bounded_int(
            payload.get("max_search_nodes", 250_000),
            "max_search_nodes",
            1,
            5_000_000,
        ),
    )


def load_audit_config(path: Path) -> AuditConfig:
    payload = _load_json_object(path, "audit input")
    allowed = {"frequencies_mhz", "minimum_spacing_khz", "intermod_guard_khz"}
    _reject_unknown(payload, allowed, "audit input")
    if "frequencies_mhz" not in payload:
        raise InputError("audit input requires frequencies_mhz")
    raw_frequencies = _list(payload["frequencies_mhz"], "frequencies_mhz")
    if not 1 <= len(raw_frequencies) <= 20:
        raise InputError("frequencies_mhz must contain from 1 to 20 entries")
    frequencies = tuple(
        parse_mhz_to_khz(value, f"frequencies_mhz[{index}]")
        for index, value in enumerate(raw_frequencies)
    )
    if len(set(frequencies)) != len(frequencies):
        raise InputError("frequencies_mhz must not contain duplicates")
    return AuditConfig(
        frequencies_khz=tuple(sorted(frequencies)),
        minimum_spacing_khz=_bounded_int(
            payload.get("minimum_spacing_khz", 200), "minimum_spacing_khz", 1, 5_000
        ),
        intermod_guard_khz=_bounded_int(
            payload.get("intermod_guard_khz", 250), "intermod_guard_khz", 1, 5_000
        ),
    )


def load_scan_csv(path: Path) -> tuple[ScanPoint, ...]:
    text = _read_text(path, limit=MAX_SCAN_BYTES, label="scan input")
    reader = csv.DictReader(text.splitlines())
    if reader.fieldnames != ["frequency_mhz", "power_dbm"]:
        raise InputError("scan input header must be frequency_mhz,power_dbm")
    points: list[ScanPoint] = []
    for row_number, row in enumerate(reader, start=2):
        if len(points) >= MAX_SCAN_ROWS:
            raise InputError(f"scan input exceeds the {MAX_SCAN_ROWS}-row limit")
        if None in row:
            raise InputError(f"scan row {row_number} must contain exactly 2 columns")
        frequency = parse_mhz_to_khz(row["frequency_mhz"], f"scan row {row_number} frequency_mhz")
        power = _finite_float(row["power_dbm"], f"scan row {row_number} power_dbm", -300, 300)
        points.append(ScanPoint(frequency, power))
    return tuple(points)
