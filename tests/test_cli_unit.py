from __future__ import annotations

import json
from pathlib import Path

import pytest

from miccoord.cli import main


def _write_json(path: Path, payload: object) -> Path:
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def test_main_plan_with_scan_emits_json_and_reports_filtered_candidate(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    source = _write_json(
        tmp_path / "plan.json",
        {
            "requested": 3,
            "ranges": [{"start_mhz": 470, "end_mhz": 474, "step_khz": 50}],
        },
    )
    scan = tmp_path / "scan.csv"
    scan.write_text("frequency_mhz,power_dbm\n470.000,-70\n", encoding="utf-8")

    exit_code = main(["plan", str(source), "--scan", str(scan), "--format", "json"])

    captured = capsys.readouterr()
    report = json.loads(captured.out)
    assert exit_code == 0
    assert report["status"] == "FOUND"
    assert report["summary"]["excluded_by_scan"] == 3


def test_main_plan_infeasible_and_exhausted_have_distinct_exit_codes(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    infeasible = _write_json(
        tmp_path / "infeasible.json",
        {
            "requested": 3,
            "ranges": [{"start_mhz": 470, "end_mhz": "470.400", "step_khz": 200}],
            "minimum_spacing_khz": 250,
            "intermod_guard_khz": 1,
        },
    )
    exhausted = _write_json(
        tmp_path / "exhausted.json",
        {
            "requested": 3,
            "ranges": [{"start_mhz": 470, "end_mhz": 472, "step_khz": 25}],
            "max_search_nodes": 1,
        },
    )

    assert main(["plan", str(infeasible), "--format", "json"]) == 1
    first = json.loads(capsys.readouterr().out)
    assert first["status"] == "INFEASIBLE"
    assert main(["plan", str(exhausted), "--format", "json"]) == 2
    second = json.loads(capsys.readouterr().out)
    assert second["status"] == "EXHAUSTED"


def test_main_audit_renders_text_conflict(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    source = _write_json(
        tmp_path / "audit.json",
        {"frequencies_mhz": ["590.000", "595.000", "600.000"]},
    )

    exit_code = main(["audit", str(source)])

    captured = capsys.readouterr()
    assert exit_code == 1
    assert "MicCoord audit: CONFLICTS" in captured.out
    assert "2*595.000-590.000" in captured.out


def test_main_invalid_input_returns_two_and_writes_error(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    source = tmp_path / "invalid.json"
    source.write_text("[]", encoding="utf-8")

    exit_code = main(["plan", str(source)])

    captured = capsys.readouterr()
    assert exit_code == 2
    assert captured.out == ""
    assert "root must be a JSON object" in captured.err


def test_main_writes_complete_output_file(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    source = _write_json(tmp_path / "audit.json", {"frequencies_mhz": ["470.000"]})
    output = tmp_path / "report.json"

    exit_code = main(["audit", str(source), "--format", "json", "--output", str(output)])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert captured.out == ""
    assert json.loads(output.read_text(encoding="utf-8"))["status"] == "CLEAR"


def test_main_rejects_directory_and_missing_parent_output_paths(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    source = _write_json(tmp_path / "audit.json", {"frequencies_mhz": ["470.000"]})

    assert main(["audit", str(source), "--output", str(tmp_path)]) == 2
    assert "output path is a directory" in capsys.readouterr().err
    missing = tmp_path / "missing" / "report.txt"
    assert main(["audit", str(source), "--output", str(missing)]) == 2
    assert "output parent directory does not exist" in capsys.readouterr().err
