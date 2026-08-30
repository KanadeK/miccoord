# MicCoord v0.1.0 tasks

- [ ] Task 1: Domain contracts
  - Acceptance: immutable models express plan/audit inputs, reports, conflicts, and stable statuses.
  - Verify: focused model tests fail before implementation and pass after it.
  - Files: `src/miccoord/model.py`, `tests/test_model.py`.

- [ ] Task 2: Third-order audit engine
  - Acceptance: carrier spacing, two-tone `2f1-f2`, and three-tone `f1+f2-f3` collisions produce exact witnesses without duplicates.
  - Verify: `590/595/600` regression plus clean-set tests.
  - Files: `src/miccoord/intermod.py`, `tests/test_intermod.py`.

- [ ] Task 3: Candidate and scan filtering
  - Acceptance: integer-kHz range generation, exclusions, and thresholded scan points produce an explainable candidate pool.
  - Verify: focused planner and I/O tests.
  - Files: `src/miccoord/planner.py`, `src/miccoord/io.py`, `tests/test_planner.py`, `tests/test_io.py`.

- [ ] Task 4: Deterministic bounded planner
  - Acceptance: valid examples find exact requested count; infeasible and exhausted searches are distinct and preserve the strongest partial set.
  - Verify: deterministic repeat test, infeasible fixture, one-node exhaustion fixture.
  - Files: `src/miccoord/planner.py`, `tests/test_planner.py`.

- [ ] Task 5: CLI vertical slice
  - Acceptance: `plan`, `audit`, JSON/text output, output files, and exit 0/1/2 work in real subprocesses.
  - Verify: CLI integration suite.
  - Files: `src/miccoord/cli.py`, `src/miccoord/__main__.py`, `tests/test_cli.py`.

- [ ] Task 6: Release surface
  - Acceptance: examples, docs, CI, packaging, changelog, and local gate match the spec.
  - Verify: `uv run python scripts/check.py` passes from a clean checkout.
  - Files: delivery and documentation files only.

- [ ] Task 7: Review and publish
  - Acceptance: required review findings fixed, clean Git state, public CI/tag/release/assets/install/contributor checks pass, then Gmail is sent.
  - Verify: recorded URLs, run IDs, asset hashes, install transcript, and Gmail message ID.

