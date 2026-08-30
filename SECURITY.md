# Security policy

## Supported versions

The latest GitHub Release is supported. Before the first stable release, fixes may require upgrading to the newest `0.x` version.

## Reporting a vulnerability

Use [GitHub private vulnerability reporting](https://github.com/KanadeK/miccoord/security/advisories/new). Do not open a public issue for a vulnerability that could expose users before a fix is available.

Include the affected version, operating system, minimal input, observed behavior, and impact. Never include real venue scans, credentials, or other sensitive operational data unless they are essential and have been sanitized.

## Security boundary

MicCoord reads local JSON/CSV files and writes a report. It performs no network requests, executes no user-provided commands, loads no plugins, and has no third-party runtime dependencies. Input sizes, candidate counts, requested channels, and search work are bounded. These controls limit accidental or hostile resource use; they do not make RF transmissions legal or operationally safe.
