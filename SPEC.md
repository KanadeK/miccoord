# Spec: MicCoord v0.1.0

## Objective

MicCoord is an offline Python CLI for small live-sound teams. It plans and audits wireless-microphone carrier sets inside ranges the user has already established as legal and appropriate. Success means the CLI performs real third-order intermodulation calculations, explains conflicts, handles occupied spectrum evidence, packages cleanly, and never claims that a computed set is guaranteed interference-free.

## Tech stack

- Python 3.11+.
- Standard-library runtime only: `argparse`, `csv`, `dataclasses`, `decimal`, `itertools`, `json`, and `pathlib`.
- Development and packaging through `uv`, `pytest`, `coverage`, `ruff`, `mypy`, `build`, and `twine`.
- Frequency arithmetic uses integer kHz after strict decimal parsing.

## Public CLI contract

```text
miccoord plan PLAN.json [--scan SCAN.csv] [--format text|json] [--output PATH]
miccoord audit AUDIT.json [--format text|json] [--output PATH]
miccoord --version
```

Exit codes:

- `0`: requested plan found, or audit has no conflicts.
- `1`: constraints are valid but the requested plan was not found, or audit found conflicts.
- `2`: invalid input, unreadable files, invalid output path, or exhausted search budget.

JSON reports always contain `schema_version`, `command`, `status`, `summary`, `frequencies_mhz`, `conflicts`, and `diagnostics`. Frequencies are emitted in ascending order with exactly three decimal places.

## Input contract

Plan JSON:

```json
{
  "requested": 6,
  "spares": 1,
  "ranges": [{"start_mhz": "470.100", "end_mhz": "480.000", "step_khz": 50}],
  "minimum_spacing_khz": 200,
  "intermod_guard_khz": 250,
  "exclusions": [{"start_mhz": "471.000", "end_mhz": "471.300", "label": "known carrier"}],
  "scan_threshold_dbm": -75,
  "scan_guard_khz": 100,
  "max_search_nodes": 250000
}
```

Audit JSON:

```json
{
  "frequencies_mhz": ["590.000", "595.000", "600.000"],
  "minimum_spacing_khz": 200,
  "intermod_guard_khz": 250
}
```

The scan CSV header is `frequency_mhz,power_dbm`. Points at or above `scan_threshold_dbm` block candidates within `scan_guard_khz`.

## Project structure

```text
src/miccoord/model.py      validated internal data and reports
src/miccoord/intermod.py   carrier-spacing and third-order conflict engine
src/miccoord/planner.py    candidate generation and bounded deterministic search
src/miccoord/io.py         JSON/CSV boundary parsing and report rendering
src/miccoord/cli.py        CLI orchestration and exit semantics
tests/                     unit and CLI integration tests
examples/                  valid, conflicting, scan, and infeasible fixtures
docs/                      research, design decision, and failure recovery
scripts/check.py           release-equivalent local gate
```

## Code style

```python
def third_order_product_khz(first_khz: int, second_khz: int) -> int:
    return 2 * first_khz - second_khz
```

Use explicit domain names, immutable dataclasses, integer kHz internally, boundary validation only, no broad exception swallowing, and no compatibility aliases in v0.1.

## Testing strategy

- Unit tests prove exact carrier-spacing and two-/three-tone third-order witnesses, using Shure's 590/595/600 MHz example.
- Planner tests prove exclusions, scan thresholds, deterministic output, feasible output, and honest incomplete-search semantics.
- CLI integration tests use real files and subprocesses for exit codes `0`, `1`, and `2`.
- The release gate requires at least 90% branch coverage, Ruff format/check, strict mypy, wheel/sdist build, metadata validation, isolated wheel execution, example regeneration, and an archive-content audit.

## Boundaries

- Always: validate all external JSON/CSV at the boundary; cap file size, candidate count, requested channels, and search nodes; preserve exact conflict witnesses; write output only after a complete report exists.
- Ask first: none for the authorized v0.1 scope.
- Never: fetch spectrum or legal data, control RF hardware, embed regional band rules, shell out with user data, emit secrets, weaken tests to pass a gate, or describe results as guaranteed interference-free.

## Success criteria

- The documented valid example returns six primaries plus one spare and audits cleanly under its declared model.
- The 590/595/600 MHz fixture reports the 600 MHz carrier colliding with the `2×595−590` product.
- Exclusions and above-threshold scan points remove candidates; malformed and oversized inputs fail with exit `2` and a concise error.
- Infeasible valid constraints fail with exit `1` and report the strongest partial set; search exhaustion is distinct and fails with exit `2`.
- Linux and Windows CI pass; `v0.1.0` has an annotated tag, non-draft GitHub Release, wheel, sdist, example bundle, and checksums.
- A clean environment installs the downloaded wheel and reproduces the documented plan/audit behavior.
- Git history and GitHub contributors contain only `KanadeK`, with no co-author trailers; Gmail notification is sent only after public verification.

## Open questions resolved for v0.1

- Candidate optimality: first deterministic feasible set under the declared search order, not a proof of globally best RF quality.
- Product model: third-order only; the report names this limitation.
- Regulatory data: caller-owned input, never bundled.
