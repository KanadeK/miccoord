from miccoord.intermod import audit_frequencies
from miccoord.planner import (
    Exclusion,
    FrequencyRange,
    PlanConfig,
    ScanPoint,
    build_candidate_pool,
    plan_frequencies,
)


def _config(**overrides: object) -> PlanConfig:
    values: dict[str, object] = {
        "requested": 3,
        "spares": 0,
        "ranges": (FrequencyRange(470_000, 472_000, 25),),
        "minimum_spacing_khz": 200,
        "intermod_guard_khz": 250,
        "exclusions": (),
        "scan_threshold_dbm": -75.0,
        "scan_guard_khz": 100,
        "max_search_nodes": 250_000,
    }
    values.update(overrides)
    return PlanConfig(**values)  # type: ignore[arg-type]


def test_candidate_pool_applies_inclusive_exclusions() -> None:
    config = _config(
        ranges=(FrequencyRange(470_000, 470_200, 50),),
        exclusions=(Exclusion(470_050, 470_150, "licensed link"),),
    )

    pool = build_candidate_pool(config, ())

    assert pool.frequencies_khz == (470_000, 470_200)
    assert pool.excluded_by_ranges == 3
    assert pool.excluded_by_scan == 0


def test_candidate_pool_blocks_only_scan_points_at_or_above_threshold() -> None:
    config = _config(
        ranges=(FrequencyRange(470_000, 470_400, 100),),
        scan_guard_khz=50,
    )
    scan = (
        ScanPoint(470_200, -74.9),
        ScanPoint(470_400, -75.1),
    )

    pool = build_candidate_pool(config, scan)

    assert pool.frequencies_khz == (470_000, 470_100, 470_300, 470_400)
    assert pool.excluded_by_scan == 1


def test_planner_finds_requested_set_that_audits_cleanly() -> None:
    config = _config(
        requested=6,
        spares=1,
        ranges=(FrequencyRange(470_100, 480_000, 50),),
    )

    result = plan_frequencies(config, ())

    assert result.status == "FOUND"
    assert len(result.frequencies_khz) == 7
    assert (
        audit_frequencies(
            result.frequencies_khz,
            minimum_spacing_khz=config.minimum_spacing_khz,
            intermod_guard_khz=config.intermod_guard_khz,
        )
        == ()
    )


def test_planner_is_deterministic() -> None:
    config = _config()

    first = plan_frequencies(config, ())
    second = plan_frequencies(config, ())

    assert first == second


def test_planner_proves_small_infeasible_pool_and_keeps_strongest_partial() -> None:
    config = _config(
        requested=3,
        ranges=(FrequencyRange(470_000, 470_400, 200),),
        minimum_spacing_khz=250,
        intermod_guard_khz=1,
    )

    result = plan_frequencies(config, ())

    assert result.status == "INFEASIBLE"
    assert result.search_complete is True
    assert result.frequencies_khz == (470_000, 470_400)


def test_planner_distinguishes_search_budget_exhaustion_from_infeasibility() -> None:
    config = _config(requested=3, max_search_nodes=1)

    result = plan_frequencies(config, ())

    assert result.status == "EXHAUSTED"
    assert result.search_complete is False
    assert len(result.frequencies_khz) == 1
