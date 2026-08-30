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


def _valid_range() -> dict[str, object]:
    return {"start_mhz": 470, "end_mhz": 480, "step_khz": 50}


@pytest.mark.parametrize(
    ("payload", "message"),
    [
        ({"ranges": []}, "requires requested and ranges"),
        ({"requested": "6", "ranges": []}, "requested must be an integer"),
        ({"requested": 0, "ranges": []}, "requested must be an integer"),
        (
            {"requested": 20, "spares": 1, "ranges": [_valid_range()]},
            "requested plus spares",
        ),
        ({"requested": 1, "ranges": []}, "ranges must contain from 1 to 8"),
        ({"requested": 1, "ranges": ["470-480"]}, "ranges\\[0\\] must be an object"),
        (
            {"requested": 1, "ranges": [{"start_mhz": 470, "end_mhz": 480}]},
            "requires start_mhz, end_mhz, and step_khz",
        ),
        (
            {
                "requested": 1,
                "ranges": [{"start_mhz": 480, "end_mhz": 470, "step_khz": 50}],
            },
            "start_mhz must not exceed end_mhz",
        ),
        (
            {"requested": 1, "ranges": [_valid_range()], "exclusions": "none"},
            "exclusions must be an array",
        ),
        (
            {
                "requested": 1,
                "ranges": [_valid_range()],
                "exclusions": [{"start_mhz": 471, "end_mhz": 472}],
            },
            "requires start_mhz, end_mhz, and label",
        ),
        (
            {
                "requested": 1,
                "ranges": [_valid_range()],
                "exclusions": [{"start_mhz": 471, "end_mhz": 472, "label": " "}],
            },
            "label must contain from 1 to 100 characters",
        ),
        (
            {
                "requested": 1,
                "ranges": [_valid_range()],
                "exclusions": [{"start_mhz": 472, "end_mhz": 471, "label": "blocked"}],
            },
            "start_mhz must not exceed end_mhz",
        ),
        (
            {"requested": 1, "ranges": [_valid_range()], "scan_threshold_dbm": True},
            "scan_threshold_dbm must be a finite number",
        ),
        (
            {"requested": 1, "ranges": [_valid_range()], "scan_threshold_dbm": "loud"},
            "scan_threshold_dbm must be a finite number",
        ),
        (
            {"requested": 1, "ranges": [_valid_range()], "scan_threshold_dbm": "NaN"},
            "scan_threshold_dbm must be a finite number",
        ),
    ],
)
def test_plan_config_rejects_invalid_boundary_values(
    tmp_path: Path,
    payload: object,
    message: str,
) -> None:
    source = _write_json(tmp_path / "plan.json", payload)

    with pytest.raises(InputError, match=message):
        load_plan_config(source)


@pytest.mark.parametrize(
    "payload",
    [
        {},
        {"frequencies_mhz": []},
        {"frequencies_mhz": "590.000"},
    ],
)
def test_load_audit_config_requires_a_nonempty_frequency_array(
    tmp_path: Path,
    payload: object,
) -> None:
    source = _write_json(tmp_path / "audit.json", payload)

    with pytest.raises(InputError):
        load_audit_config(source)


def test_load_json_reports_invalid_json_and_missing_files(tmp_path: Path) -> None:
    invalid = tmp_path / "invalid.json"
    invalid.write_text("{", encoding="utf-8")

    with pytest.raises(InputError, match="not valid JSON: line 1, column 2"):
        load_plan_config(invalid)
    with pytest.raises(InputError, match="cannot read plan input"):
        load_plan_config(tmp_path / "missing.json")


def test_load_json_reports_integer_parser_limit(tmp_path: Path) -> None:
    source = tmp_path / "huge-number.json"
    source.write_text('{"requested": ' + "9" * 5000 + ', "ranges": []}', encoding="utf-8")

    with pytest.raises(InputError, match="numeric value beyond the parser limit"):
        load_plan_config(source)


def test_load_json_rejects_oversized_input(tmp_path: Path) -> None:
    source = tmp_path / "large.json"
    source.write_text(" " * 1_000_001, encoding="utf-8")

    with pytest.raises(InputError, match="exceeds the 1000000-byte limit"):
        load_plan_config(source)


def test_load_scan_csv_rejects_non_numeric_power(tmp_path: Path) -> None:
    source = tmp_path / "scan.csv"
    source.write_text(
        "frequency_mhz,power_dbm\n470.100,loud\n",
        encoding="utf-8",
    )

    with pytest.raises(InputError, match="scan row 2 power_dbm must be a finite number"):
        load_scan_csv(source)


def test_load_scan_csv_rejects_extra_columns(tmp_path: Path) -> None:
    source = tmp_path / "scan.csv"
    source.write_text(
        "frequency_mhz,power_dbm\n470.100,-80,unexpected\n",
        encoding="utf-8",
    )

    with pytest.raises(InputError, match="scan row 2 must contain exactly 2 columns"):
        load_scan_csv(source)
