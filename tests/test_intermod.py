from miccoord.intermod import audit_frequencies


def test_audit_reports_shure_two_tone_example_with_exact_witness() -> None:
    conflicts = audit_frequencies(
        (590_000, 595_000, 600_000),
        minimum_spacing_khz=200,
        intermod_guard_khz=250,
    )

    matching = [
        conflict
        for conflict in conflicts
        if conflict.kind == "two_tone_third_order"
        and conflict.product_khz == 600_000
        and conflict.target_khz == 600_000
    ]
    assert len(matching) == 1
    assert matching[0].sources_khz == (590_000, 595_000)
    assert matching[0].expression == "2*595.000-590.000"
    assert matching[0].separation_khz == 0


def test_audit_reports_three_tone_product_without_duplicate_witnesses() -> None:
    conflicts = audit_frequencies(
        (500_000, 501_000, 503_000, 504_000),
        minimum_spacing_khz=200,
        intermod_guard_khz=1,
    )

    matching = [
        conflict
        for conflict in conflicts
        if conflict.kind == "three_tone_third_order"
        and conflict.product_khz == 504_000
        and conflict.target_khz == 504_000
    ]
    assert len(matching) == 1
    assert matching[0].sources_khz == (500_000, 501_000, 503_000)
    assert matching[0].expression == "501.000+503.000-500.000"


def test_audit_reports_spacing_below_minimum_but_allows_exact_minimum() -> None:
    too_close = audit_frequencies(
        (470_000, 470_199),
        minimum_spacing_khz=200,
        intermod_guard_khz=1,
    )
    exact = audit_frequencies(
        (470_000, 470_200),
        minimum_spacing_khz=200,
        intermod_guard_khz=1,
    )

    assert [conflict.kind for conflict in too_close] == ["carrier_spacing"]
    assert exact == ()


def test_audit_returns_conflicts_in_deterministic_order() -> None:
    forward = audit_frequencies(
        (590_000, 595_000, 600_000),
        minimum_spacing_khz=200,
        intermod_guard_khz=250,
    )
    reverse = audit_frequencies(
        (600_000, 595_000, 590_000),
        minimum_spacing_khz=200,
        intermod_guard_khz=250,
    )

    assert forward == reverse
