"""MicCoord command-line interface."""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence
from pathlib import Path

from miccoord import __version__
from miccoord.intermod import audit_frequencies
from miccoord.io import load_audit_config, load_plan_config, load_scan_csv
from miccoord.model import InputError
from miccoord.planner import plan_frequencies
from miccoord.reporting import build_audit_report, build_plan_report, render_text


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="miccoord",
        description=(
            "Plan or audit wireless-microphone frequencies under an explicit third-order model."
        ),
    )
    parser.add_argument("--version", action="version", version=f"miccoord {__version__}")
    subparsers = parser.add_subparsers(dest="command", required=True)

    plan = subparsers.add_parser("plan", help="plan a compatible set from declared ranges")
    plan.add_argument("input", type=Path, help="plan JSON file")
    plan.add_argument("--scan", type=Path, help="optional frequency_mhz,power_dbm CSV")
    _add_output_arguments(plan)

    audit = subparsers.add_parser("audit", help="audit an existing carrier set")
    audit.add_argument("input", type=Path, help="audit JSON file")
    _add_output_arguments(audit)
    return parser


def _add_output_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--format", choices=("text", "json"), default="text")
    parser.add_argument("--output", type=Path, help="write the complete report to this file")


def _emit(report: dict[str, object], output_format: str, output: Path | None) -> None:
    rendered = (
        json.dumps(report, indent=2, ensure_ascii=False) + "\n"
        if output_format == "json"
        else render_text(report)
    )
    if output is None:
        print(rendered, end="")
        return
    if output.exists() and output.is_dir():
        raise InputError(f"output path is a directory: {output}")
    if not output.parent.is_dir():
        raise InputError(f"output parent directory does not exist: {output.parent}")
    try:
        output.write_text(rendered, encoding="utf-8", newline="\n")
    except OSError as error:
        raise InputError(f"cannot write output {output}: {error}") from None


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        if args.command == "plan":
            plan_config = load_plan_config(args.input)
            scan = load_scan_csv(args.scan) if args.scan is not None else ()
            result = plan_frequencies(plan_config, scan)
            report = build_plan_report(plan_config, result)
            _emit(report, args.format, args.output)
            if result.status == "FOUND":
                return 0
            return 1 if result.status == "INFEASIBLE" else 2

        audit_config = load_audit_config(args.input)
        conflicts = audit_frequencies(
            audit_config.frequencies_khz,
            minimum_spacing_khz=audit_config.minimum_spacing_khz,
            intermod_guard_khz=audit_config.intermod_guard_khz,
        )
        report = build_audit_report(audit_config, conflicts)
        _emit(report, args.format, args.output)
        return 1 if conflicts else 0
    except InputError as error:
        print(f"miccoord: error: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
