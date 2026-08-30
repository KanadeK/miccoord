# Implementation plan: MicCoord v0.1.0

## Overview

Build the highest-risk path first: exact third-order conflict evidence and a bounded deterministic planner. Add file boundaries and CLI behavior only after the domain model is proven. Finish with release automation and public verification.

## Architecture decisions

- Integer kHz is the single authoritative frequency representation.
- One conflict engine serves both planning and auditing; no duplicate formulas.
- The search returns the first feasible deterministic set and reports its completeness honestly.
- Runtime remains dependency-free; development tools do not leak into installed behavior.

## Task list

### Phase 1: Contracts and domain proof

- [x] Define immutable input/report models and stable exit semantics.
- [x] Prove carrier-spacing and third-order witnesses with failing tests, then implement the conflict engine.

### Checkpoint: Domain

- [x] Focused tests pass and Shure's 590/595/600 example produces the expected witness.

### Phase 2: Real planning flow

- [x] Generate candidates from ranges and filter declared exclusions.
- [x] Import thresholded scan CSV evidence.
- [x] Implement bounded deterministic search with strongest-partial and exhaustion reports.
- [x] Connect `plan` and `audit` through real CLI subprocess tests.

### Checkpoint: User flow

- [x] Valid, conflict, scan, infeasible, and malformed examples exhibit exit codes 0/1/2 as specified.

### Phase 3: Delivery

- [x] Add README, examples, decision record, contributing/security guidance, changelog, and failure recovery.
- [x] Add cross-platform CI, tag release workflow, deterministic example bundle, and local release gate.
- [x] Run a five-axis self-review and repair required findings.
- [x] Commit, push, wait for CI, publish `v0.1.0`, download and verify assets, then send Gmail.

## Risks and mitigations

| Risk | Impact | Mitigation |
|---|---|---|
| Search grows combinatorially | High | Candidate/request caps, incremental compatibility checks, node budget, distinct exhausted status |
| Users over-read “compatible” | High | Third-order-only wording in every report and no legal/device guarantee |
| Decimal drift creates false witnesses | High | Parse decimal MHz directly to integer kHz; reject sub-kHz values |
| CI differs on Windows paths/EOL | Medium | Cross-platform matrix and byte-stable generated examples |

## Open questions

None blocking. Scope-expanding questions are deferred to post-v0.1 issues only after real user evidence.
