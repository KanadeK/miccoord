# MicCoord

[![CI](https://github.com/KanadeK/miccoord/actions/workflows/ci.yml/badge.svg)](https://github.com/KanadeK/miccoord/actions/workflows/ci.yml)
[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-3776AB.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

MicCoord is an offline, explainable frequency planner and auditor for small wireless-microphone setups. Give it ranges you have already established as usable; it returns a deterministic carrier set or an honest failure report with the strongest partial result.

Unlike a spectrum viewer, device-profile database, or vendor-file bridge, MicCoord has one narrow job: generic range-in/frequencies-out coordination that can be reviewed, versioned, and reproduced without RF hardware or a desktop suite. Every conflict names the carrier-spacing or third-order intermodulation witness that caused it.

> MicCoord does not determine which frequencies are legal, control RF hardware, model a particular receiver, or guarantee interference-free operation. A clean report means only that no conflict was found under the declared spacing and third-order model. Confirm local rules, device compatibility, and the on-site spectrum before transmitting.

## Quick start

Install the wheel from the [latest GitHub Release](https://github.com/KanadeK/miccoord/releases/latest):

```console
python -m pip install miccoord-0.1.0-py3-none-any.whl
miccoord --version
```

Clone contributors can instead run the locked environment:

```console
uv sync --locked
uv run miccoord --version
```

Plan six primary frequencies and one spare while applying a declared exclusion and imported scan evidence:

```console
miccoord plan examples/plan.json --scan examples/scan.csv
```

The committed fixture returns:

```text
MicCoord plan: FOUND
Frequencies (MHz): 470.100, 470.500, 471.350, 472.850, 474.600, 476.600, 479.600
```

Audit an existing set:

```console
miccoord audit examples/audit-conflict.json --format json
```

The `590/595/600 MHz` example identifies the `2×595−590 = 600 MHz` third-order product and exits `1` because conflicts were found.

## Commands

```text
miccoord plan PLAN.json [--scan SCAN.csv] [--format text|json] [--output PATH]
miccoord audit AUDIT.json [--format text|json] [--output PATH]
miccoord --version
```

Exit codes are part of the public contract:

| Code | Meaning |
|---:|---|
| `0` | Plan found, or audit clear |
| `1` | Valid constraints are infeasible, or audit found conflicts |
| `2` | Invalid input/output, or the bounded search was exhausted |

`INFEASIBLE` means MicCoord completely searched its bounded candidate pool. `EXHAUSTED` means the node budget ended first and is not proof that no solution exists. Invalid input never leaves a partial output file.

## Plan input

```json
{
  "requested": 6,
  "spares": 1,
  "ranges": [
    {"start_mhz": "470.100", "end_mhz": "480.000", "step_khz": 50}
  ],
  "minimum_spacing_khz": 200,
  "intermod_guard_khz": 250,
  "exclusions": [
    {"start_mhz": "471.000", "end_mhz": "471.300", "label": "known local carrier"}
  ],
  "scan_threshold_dbm": -75,
  "scan_guard_khz": 100,
  "max_search_nodes": 250000
}
```

Frequencies from `0.001` through `100000.000 MHz` are parsed at whole-kHz precision; the upper bound is a computational input limit, not a statement about equipment or legal bands. Allowed ranges are inclusive. Exclusions are inclusive. A scan CSV must have exactly this header:

```csv
frequency_mhz,power_dbm
470.350,-68
476.000,-82
```

Points at or above `scan_threshold_dbm` block candidates within `scan_guard_khz`. MicCoord treats the file as caller-supplied evidence; it does not interpret scanner calibration or freshness.

## What the model checks

MicCoord checks:

- minimum carrier-to-carrier spacing;
- two-transmitter third-order products `2f1−f2` and `2f2−f1`;
- three-transmitter third-order products `f1+f2−f3`, `f1−f2+f3`, and `f2+f3−f1`;
- distance from every modeled product to every selected carrier using the declared guard.

The planner uses the same audit engine as the standalone audit command. It generates integer-kHz candidates, filters exclusions and active scan points, then performs a deterministic bounded depth-first search. It returns the first feasible set in ascending candidate order, not a claim of globally optimal RF quality.

Third-order products and conservative spacing are established wireless-coordination concerns; Shure documents the `2f1−f2` / `2f2−f1` mechanism and recommends a margin around calculated products, while Sennheiser describes automated calculation and spacing constraints in professional coordination. See [research and differentiation](docs/research.md) for sources and the deliberately smaller scope.

## Reproducible examples

The [`examples`](examples) directory contains success, conflict, infeasible, exhausted, and invalid inputs plus committed text and JSON reports. Recreate every report byte-for-byte with:

```console
uv run python scripts/generate_examples.py
```

## Development and release gate

The runtime has no third-party dependencies. Development dependencies are locked in `uv.lock`.

```console
uv sync --locked
uv run python scripts/check.py
```

The gate checks formatting, lint, strict types, tests with branch coverage, dependency advisories, fixture reproducibility, all exit-code paths, wheel/sdist contents and metadata, deterministic example archives, and a clean-environment wheel install. A successful run ends with `MICCOORD_RELEASE_GATE=PASS` and produces release assets in `dist/`.

See [CONTRIBUTING.md](CONTRIBUTING.md), [SECURITY.md](SECURITY.md), [failure recovery](docs/failure-recovery.md), the [v0.1 specification](SPEC.md), and the [architecture decision](docs/decisions/0001-integer-khz-and-third-order-scope.md).

## License

MIT
