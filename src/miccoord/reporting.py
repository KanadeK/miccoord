"""Stable machine-readable and human-readable MicCoord reports."""

from __future__ import annotations

from miccoord.io import AuditConfig
from miccoord.model import Conflict, format_mhz
from miccoord.planner import PlanConfig, PlanResult

SCHEMA_VERSION = "miccoord.report.v1"
MODEL_LIMITATION = (
    "Checks carrier spacing and third-order two-/three-transmitter products only; "
    "confirm local rules, device compatibility, and the on-site spectrum before transmitting."
)


def build_plan_report(config: PlanConfig, result: PlanResult) -> dict[str, object]:
    diagnostics = [MODEL_LIMITATION]
    if result.status == "INFEASIBLE":
        diagnostics.append(
            "The bounded candidate pool was searched completely; "
            "no set reached the requested count."
        )
    elif result.status == "EXHAUSTED":
        diagnostics.append(
            "The node budget was exhausted; this is not proof that the requested set is infeasible."
        )
    return {
        "schema_version": SCHEMA_VERSION,
        "command": "plan",
        "status": result.status,
        "model": {
            "minimum_spacing_khz": config.minimum_spacing_khz,
            "intermod_guard_khz": config.intermod_guard_khz,
            "intermod_order": 3,
        },
        "summary": {
            "requested": config.requested,
            "spares": config.spares,
            "requested_total": result.requested_total,
            "found": len(result.frequencies_khz),
            "candidate_count": result.candidate_count,
            "excluded_by_ranges": result.excluded_by_ranges,
            "excluded_by_scan": result.excluded_by_scan,
            "nodes_visited": result.nodes_visited,
            "search_complete": result.search_complete,
        },
        "frequencies_mhz": [format_mhz(value) for value in result.frequencies_khz],
        "conflicts": [],
        "diagnostics": diagnostics,
    }


def build_audit_report(config: AuditConfig, conflicts: tuple[Conflict, ...]) -> dict[str, object]:
    return {
        "schema_version": SCHEMA_VERSION,
        "command": "audit",
        "status": "CONFLICTS" if conflicts else "CLEAR",
        "model": {
            "minimum_spacing_khz": config.minimum_spacing_khz,
            "intermod_guard_khz": config.intermod_guard_khz,
            "intermod_order": 3,
        },
        "summary": {
            "frequency_count": len(config.frequencies_khz),
            "conflict_count": len(conflicts),
        },
        "frequencies_mhz": [format_mhz(value) for value in config.frequencies_khz],
        "conflicts": [conflict.to_dict() for conflict in conflicts],
        "diagnostics": [MODEL_LIMITATION],
    }


def render_text(report: dict[str, object]) -> str:
    lines = [f"MicCoord {report['command']}: {report['status']}"]
    frequencies = report["frequencies_mhz"]
    assert isinstance(frequencies, list)
    lines.append("Frequencies (MHz): " + (", ".join(frequencies) if frequencies else "none"))
    summary = report["summary"]
    assert isinstance(summary, dict)
    for key, value in summary.items():
        lines.append(f"{key}: {str(value).lower() if isinstance(value, bool) else value}")
    conflicts = report["conflicts"]
    assert isinstance(conflicts, list)
    if conflicts:
        lines.append("Conflicts:")
        for conflict in conflicts:
            assert isinstance(conflict, dict)
            lines.append(
                "- "
                f"{conflict['kind']}: {conflict['expression']} -> {conflict['product_mhz']} MHz, "
                f"target {conflict['target_mhz']} MHz, separation {conflict['separation_khz']} kHz"
            )
    lines.append("Diagnostics:")
    diagnostics = report["diagnostics"]
    assert isinstance(diagnostics, list)
    lines.extend(f"- {message}" for message in diagnostics)
    return "\n".join(lines) + "\n"
