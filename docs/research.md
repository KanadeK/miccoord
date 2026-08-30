# Research and differentiation

Research was performed on 2026-08-30 before implementation. The goal was not to claim that no frequency-coordination software exists; it was to avoid reproducing an existing open-source project's job and interaction model.

## Observed need

A live-sound user asked for a simple way to enter a roughly 3–4 MHz range and generate about six generic intermodulation-free frequencies without the complexity of Wireless Workbench. That is the narrow workflow MicCoord serves: explicit caller-owned constraints, a deterministic small-channel result, and reviewable evidence.

Source: [Reddit: “Simple way of generating a small number of intermodulation free frequencies?”](https://www.reddit.com/r/livesound/comments/1fkh64b/simple_way_of_generating_a_small_number_of/)

## Representative alternatives

| Project/workflow | Primary job | Why MicCoord is structurally different |
|---|---|---|
| [berkon/wireless-microphone-analyzer](https://github.com/berkon/wireless-microphone-analyzer) | Visualize spectrum-analyzer data and overlay vendor preset frequencies | MicCoord needs no analyzer and computes a generic set from explicit constraints |
| [stoatworks-labs/wsm-wwb-bridge](https://github.com/stoatworks-labs/wsm-wwb-bridge) | Translate existing Sennheiser WSM and Shure WWB coordination files | MicCoord does not translate vendor projects; it plans and audits directly |
| Shure Wireless Workbench / Sennheiser WSM | Device-aware professional coordination, inventory, zones, and monitoring | MicCoord deliberately omits device profiles, hardware control, regulatory data, and operational monitoring |

Repository-name searches also found no existing GitHub or PyPI project named `MicCoord` at research time. This is collision evidence, not a claim that the name can never be used elsewhere.

## Model sources

- [Shure: All About Wireless — Intermodulation Distortion](https://www.shure.com/en-US/insights/all-about-wireless-intermodulation-distortion) explains the two-transmitter third-order products `2f1−f2` and `2f2−f1`, demonstrates the `590/595/600 MHz` relationship, and recommends margin around calculated products.
- [Shure: Selection and Operation of Wireless Microphone Systems](https://www.shure.com/en-US/insights/selection-and-operation-of-wireless-microphone-systems) documents three-transmitter third-order combinations alongside the two-transmitter products.
- [Sennheiser WSM: Coordinating intermodulation-free frequencies](https://docs.cloud.sennheiser.com/en-us/wsm/wsm/prof-coordination.html) describes professional coordination with frequency spacing and intermodulation constraints.

These sources support the implemented arithmetic and the need for a declared guard. They do not support a universal safety guarantee, so every MicCoord report repeats the third-order-only limitation.

## Deliberate boundary

MicCoord's distinction is the combination of:

1. generic ranges supplied by the caller rather than a bundled regulatory or device database;
2. one shared, explainable third-order audit engine for both existing and proposed carrier sets;
3. deterministic bounded search with separate `INFEASIBLE` and `EXHAUSTED` outcomes;
4. offline, dependency-free runtime and stable JSON suitable for rehearsal paperwork or CI.

Hardware scanning, vendor profiles, fifth-order products, legal-band advice, a graphical interface, accounts, and cloud features remain outside v0.1. Adding any of them would change the product boundary rather than merely extend the current implementation.
