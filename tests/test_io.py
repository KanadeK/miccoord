import json
from pathlib import Path

import pytest

from miccoord.io import load_audit_config, load_plan_config, load_scan_csv
from miccoord.model import InputError


def _write_json(path: Path, payload: object) -> Path:
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def test_load_plan_config_parses_ranges_exclusions_and_defaults(tmp_path: Path) -> None:
    source = _write_json(
        tmp_path / "plan.json",
        {
            "requested": 6,
            "ranges": [{"start_mhz": "470.100", "end_mhz": "480.000", "step_khz": 50}],
            "exclusions": [
                {
                    "start_mhz": "471.000",
                    "end_mhz": "471.300",
                    "label": "known carrier",
                }
            ],
        },
    )

    config = load_plan_config(source)

    assert config.requested == 6
    assert config.spares == 0
    assert config.ranges[0].start_khz == 470_100
    assert config.ranges[0].step_khz == 50
    assert config.exclusions[0].label == "known carrier"
    assert config.intermod_guard_khz == 250
    assert config.max_search_nodes == 250_000


def test_load_plan_config_rejects_unknown_keys_instead_of_ignoring_typos(tmp_path: Path) -> None:
    source = _write_json(
        tmp_path / "plan.json",
        {
            "requested": 3,
            "ranges": [{"start_mhz": 470, "end_mhz": 480, "step_khz": 50}],
            "intermod_guards_khz": 250,
        },
    )

    with pytest.raises(InputError, match=r"unknown field.*intermod_guards_khz"):
        load_plan_config(source)


def test_load_audit_config_rejects_duplicate_frequencies(tmp_path: Path) -> None:
    source = _write_json(
        tmp_path / "audit.json",
        {"frequencies_mhz": ["590.000", "590.000"]},
    )

    with pytest.raises(InputError, match="must not contain duplicates"):
        load_audit_config(source)


def test_load_scan_csv_reads_finite_points_and_preserves_threshold_evidence(
    tmp_path: Path,
) -> None:
    source = tmp_path / "scan.csv"
    source.write_text(
        "frequency_mhz,power_dbm\n470.100,-80.5\n470.200,-74.9\n",
        encoding="utf-8",
    )

    points = load_scan_csv(source)

    assert [(point.frequency_khz, point.power_dbm) for point in points] == [
        (470_100, -80.5),
        (470_200, -74.9),
    ]


def test_load_scan_csv_rejects_wrong_header(tmp_path: Path) -> None:
    source = tmp_path / "scan.csv"
    source.write_text("mhz,dbm\n470.100,-80\n", encoding="utf-8")

    with pytest.raises(InputError, match="header must be frequency_mhz,power_dbm"):
        load_scan_csv(source)


def test_load_json_rejects_non_object_root(tmp_path: Path) -> None:
    source = _write_json(tmp_path / "plan.json", [])

    with pytest.raises(InputError, match="root must be a JSON object"):
        load_plan_config(source)
