"""Regenerate deterministic MicCoord report fixtures."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from miccoord.intermod import audit_frequencies
from miccoord.io import load_audit_config, load_plan_config, load_scan_csv
from miccoord.planner import plan_frequencies
from miccoord.reporting import build_audit_report, build_plan_report, render_text

ROOT = Path(__file__).resolve().parents[1]


def _write_report(output: Path, name: str, report: dict[str, object]) -> None:
    (output / f"{name}.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    (output / f"{name}.txt").write_text(
        render_text(report),
        encoding="utf-8",
        newline="\n",
    )


def generate(output: Path) -> None:
    output.mkdir(parents=True, exist_ok=True)
    examples = ROOT / "examples"

    plan_config = load_plan_config(examples / "plan.json")
    plan_result = plan_frequencies(plan_config, load_scan_csv(examples / "scan.csv"))
    if plan_result.status != "FOUND":
        raise RuntimeError(f"documented plan must be FOUND, got {plan_result.status}")
    _write_report(output, "plan-report", build_plan_report(plan_config, plan_result))

    audit_config = load_audit_config(examples / "audit-conflict.json")
    conflicts = audit_frequencies(
        audit_config.frequencies_khz,
        minimum_spacing_khz=audit_config.minimum_spacing_khz,
        intermod_guard_khz=audit_config.intermod_guard_khz,
    )
    if not conflicts:
        raise RuntimeError("documented audit must contain conflicts")
    _write_report(output, "audit-conflict-report", build_audit_report(audit_config, conflicts))

    infeasible_config = load_plan_config(examples / "infeasible.json")
    infeasible_result = plan_frequencies(infeasible_config, ())
    if infeasible_result.status != "INFEASIBLE":
        raise RuntimeError(
            f"documented infeasible plan must be INFEASIBLE, got {infeasible_result.status}"
        )
    _write_report(
        output,
        "infeasible-report",
        build_plan_report(infeasible_config, infeasible_result),
    )

    exhausted_config = load_plan_config(examples / "exhausted.json")
    exhausted_result = plan_frequencies(exhausted_config, ())
    if exhausted_result.status != "EXHAUSTED":
        raise RuntimeError(
            f"documented exhausted plan must be EXHAUSTED, got {exhausted_result.status}"
        )
    _write_report(
        output,
        "exhausted-report",
        build_plan_report(exhausted_config, exhausted_result),
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=ROOT / "examples")
    args = parser.parse_args()
    generate(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
