# MicCoord

## Problem statement

How might we help a small live-sound team turn an explicitly allowed RF range into a reviewable set of wireless-microphone frequencies without requiring vendor hardware, a proprietary device library, or a heavyweight desktop suite?

## Recommended direction

Build a small offline CLI that accepts allowed ranges, optional occupied intervals or scan points, carrier spacing, and a third-order intermodulation guard. It should either return a deterministic compatible set or fail with the strongest partial result and a machine-readable reason. A separate audit command should explain why an existing set is unsafe.

The wedge is not “replace professional coordination suites.” It is a transparent generic calculation for small jobs and reproducible CI or rehearsal paperwork. The algorithm works in integer kHz, cites the exact carrier/product conflict, and never invents local spectrum rules.

## Directions considered

- Hardware-first spectrum viewer: useful, but duplicates an established open-source analyzer and requires a scanner.
- Vendor-file bridge: useful, but an existing project already moves Wireless Workbench and WSM data.
- Full professional coordination suite: high ceiling, but device profiles, zones, licensing data, monitoring, and fifth-order modelling make it too broad for a trustworthy first release.
- Generic third-order planner and auditor: high user value for small channel counts, feasible offline, and structurally distinct from the representative GitHub projects inspected.

## Key assumptions to validate

- Small crews value a generic range-in/frequencies-out workflow; a public request describes exactly a 3–4 MHz range and roughly six desired channels.
- Third-order two-tone and three-tone evidence plus explicit margins is useful when its limitations are stated, even though it is not a substitute for manufacturer profiles or on-site scanning.
- JSON and CSV inputs are sufficient for a first release; direct hardware and proprietary project formats are not required to prove the core job.

## MVP scope

- `miccoord plan`: generate a requested number of new and spare frequencies from explicit ranges.
- `miccoord audit`: report carrier-spacing and third-order intermodulation conflicts in an existing set.
- Optional exclusion intervals and thresholded scan CSV points.
- Deterministic terminal and JSON reports with stable exit codes.
- Real infeasible, invalid-input, and search-budget failure paths.

## Not doing

- Regulatory or licensing advice: rules vary by place and time; users must supply allowed ranges.
- RF scanning or device control: no hardware dependency in v0.1.
- Manufacturer/device compatibility profiles: would create a second, hard-to-maintain truth source.
- Fifth-order or adjacent-system modelling: not claimed until backed by a tested contract.
- Web UI, accounts, cloud storage, telemetry, or automatic uploads: none are needed for the core job.

## Research distinction

- `berkon/wireless-microphone-analyzer` visualizes spectrum-analyzer data and vendor preset overlays; MicCoord performs hardware-independent generic planning and audits.
- `stoatworks-labs/wsm-wwb-bridge` translates existing Shure/Sennheiser coordination data; MicCoord computes a new generic set from explicit constraints.
- Shure Wireless Workbench and Sennheiser WSM cover professional device-aware workflows; MicCoord deliberately serves the smaller reproducible CLI case.

