# MicCoord 0.1.0

The first public release provides an offline, explainable planner and auditor for small wireless-microphone frequency sets.

Highlights:

- deterministic range-in/frequencies-out planning with optional declared exclusions and scan CSV evidence;
- exact carrier-spacing, two-transmitter, and three-transmitter third-order conflict witnesses;
- honest `FOUND`, `INFEASIBLE`, and `EXHAUSTED` outcomes with stable text/JSON reports;
- dependency-free Python 3.11+ runtime, cross-platform CI, reproducible examples, and verified wheel/sdist assets.

Start with `miccoord-0.1.0-examples.zip` and the [README](https://github.com/KanadeK/miccoord#readme).

MicCoord does not determine legal frequencies, model a particular receiver, control RF hardware, or guarantee interference-free operation. Confirm local rules, device compatibility, and the current on-site spectrum before transmitting.
