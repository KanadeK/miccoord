# Contributing

MicCoord welcomes focused bug reports and small, evidence-backed changes within its documented product boundary.

## Set up

Install [uv](https://docs.astral.sh/uv/), clone the repository, then run:

```console
uv sync --locked
uv run python scripts/check.py
```

The second command is the release-equivalent local gate. It must end with `MICCOORD_RELEASE_GATE=PASS` before a change is ready for review.

## Change discipline

- Open an issue before adding a new product surface such as device profiles, regulatory data, new intermodulation orders, or hardware integration.
- Preserve integer kHz as the only internal frequency representation.
- Add a failing test before changing behavior, then make the smallest complete correction.
- Keep the conflict engine authoritative for both audit and planning; do not copy formulas into another path.
- Document public input, report, or exit-code changes in `SPEC.md`, `README.md`, and `CHANGELOG.md`.

Do not weaken a spacing rule, guard, test, or limitation statement merely to make an example pass. Generated report fixtures must be recreated with `scripts/generate_examples.py` and reviewed with their input change.
