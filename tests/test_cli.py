from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any, cast


def _write_json(path: Path, payload: object) -> Path:
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def _run(*arguments: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "miccoord", *arguments],
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )


def _json_stdout(result: subprocess.CompletedProcess[str]) -> dict[str, Any]:
    return cast(dict[str, Any], json.loads(result.stdout))


def test_plan_command_returns_real_compatible_set_as_json(tmp_path: Path) -> None:
    source = _write_json(
        tmp_path / "plan.json",
        {
            "requested": 3,
            "ranges": [{"start_mhz": "470.100", "end_mhz": "474.000", "step_khz": 50}],
        },
    )

    result = _run("plan", str(source), "--format", "json")
    report = _json_stdout(result)

    assert result.returncode == 0
    assert report["status"] == "FOUND"
    assert len(report["frequencies_mhz"]) == 3
    assert report["summary"]["search_complete"] is True
    assert report["conflicts"] == []


def test_audit_command_returns_one_and_exact_conflict_evidence(tmp_path: Path) -> None:
    source = _write_json(
        tmp_path / "audit.json",
        {"frequencies_mhz": ["590.000", "595.000", "600.000"]},
    )

    result = _run("audit", str(source), "--format", "json")
    report = _json_stdout(result)

    assert result.returncode == 1
    assert report["status"] == "CONFLICTS"
    assert any(
        conflict["expression"] == "2*595.000-590.000" and conflict["target_mhz"] == "600.000"
        for conflict in report["conflicts"]
    )


def test_infeasible_plan_returns_one_with_strongest_partial_set(tmp_path: Path) -> None:
    source = _write_json(
        tmp_path / "infeasible.json",
        {
            "requested": 3,
            "ranges": [{"start_mhz": 470, "end_mhz": "470.400", "step_khz": 200}],
            "minimum_spacing_khz": 250,
            "intermod_guard_khz": 1,
        },
    )

    result = _run("plan", str(source), "--format", "json")
    report = _json_stdout(result)

    assert result.returncode == 1
    assert report["status"] == "INFEASIBLE"
    assert report["frequencies_mhz"] == ["470.000", "470.400"]


def test_search_exhaustion_returns_two_instead_of_claiming_infeasible(tmp_path: Path) -> None:
    source = _write_json(
        tmp_path / "exhausted.json",
        {
            "requested": 3,
            "ranges": [{"start_mhz": 470, "end_mhz": 472, "step_khz": 25}],
            "max_search_nodes": 1,
        },
    )

    result = _run("plan", str(source), "--format", "json")
    report = _json_stdout(result)

    assert result.returncode == 2
    assert report["status"] == "EXHAUSTED"
    assert report["summary"]["search_complete"] is False


def test_invalid_input_leaves_no_requested_output_file(tmp_path: Path) -> None:
    source = tmp_path / "invalid.json"
    source.write_text("[]", encoding="utf-8")
    output = tmp_path / "report.json"

    result = _run("plan", str(source), "--format", "json", "--output", str(output))

    assert result.returncode == 2
    assert result.stdout == ""
    assert "root must be a JSON object" in result.stderr
    assert not output.exists()


def test_successful_output_file_is_complete_and_stdout_stays_empty(tmp_path: Path) -> None:
    source = _write_json(
        tmp_path / "audit.json",
        {"frequencies_mhz": ["470.000"], "intermod_guard_khz": 1},
    )
    output = tmp_path / "report.json"

    result = _run("audit", str(source), "--format", "json", "--output", str(output))

    assert result.returncode == 0
    assert result.stdout == ""
    assert json.loads(output.read_text(encoding="utf-8"))["status"] == "CLEAR"


def test_version_flag_uses_package_version() -> None:
    result = _run("--version")

    assert result.returncode == 0
    assert result.stdout.strip() == "miccoord 0.1.0"
