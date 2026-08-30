# MicCoord

Offline, explainable third-order frequency planning for small wireless-microphone setups.

MicCoord turns user-supplied allowed RF ranges and optional occupied-spectrum evidence into a deterministic carrier plan. It can also audit an existing set and name the exact carrier-spacing or third-order intermodulation witness behind each conflict.

> MicCoord does not determine which frequencies are legal, control RF hardware, or guarantee interference-free operation. A clean report means only that no conflict was found under the declared spacing and third-order model. Confirm local rules, device compatibility, and the on-site spectrum before transmitting.

## Status

`v0.1.0` is under development. The complete quick start, examples, command reference, limitations, and troubleshooting guide will be added before release.

## Design sources

- [Shure: All About Wireless — Intermodulation Distortion](https://www.shure.com/en-US/insights/all-about-wireless-intermodulation-distortion)
- [Sennheiser WSM: Coordinating intermodulation-free frequencies](https://docs.cloud.sennheiser.com/en-us/wsm/wsm/prof-coordination.html)
- [Project specification](SPEC.md)

## License

MIT

