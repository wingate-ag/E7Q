# E7Q

**An E7G-T-based, invariant-aware quantum programming and verification language.**

E7Q combines established quantum mathematics for execution with E7G-T
composition, transformation, equivalence, projection, measurement
accountability, and Proof-of-Path.

E7Q is **not** a new physical theory. It does not replace Hilbert spaces,
unitary evolution, quantum channels, the Born rule, or hardware-specific
compilation.

## Status

v1.0 release candidate. Milestones 1–3 provide the executable language, circuit
equivalence, partial measurement, classical feed-forward, quantum
teleportation, and Deutsch–Jozsa reference programs. Milestone 4 adds
reusable paths, executable assertions, first-failure diagnostics, and
OpenQASM subset round trips.
Milestone 5 adds a density-matrix reference backend, declared noise channels,
noise-aware evidence, and machine-readable backend capability profiles.
Milestone 6 adds superoperator-based equivalence for declared quantum channels.
Milestone 7 adds backend-neutral topology-aware compilation and auditable
SWAP-routing traces. Milestone 8 adds dependency-free IBM Qiskit and Google
Cirq source adapters with explicit capability boundaries. Milestone 9 adds
backend-neutral resource estimation and auditable target planning. Milestone
10 adds offline calibration snapshots and evidence-bounded target selection.
Milestone 11 adds offline IBM and Google calibration-export normalization with
provenance and freshness validation. Milestone 12 adds reproducible offline
execution bundles for credentialed handoff. Milestone 13 adds offline execution-result
receipts with strict bundle linkage and empirical count evidence. Milestone 14 adds
evidence-bounded statistical assessment against an explicit reference distribution.
Milestone 15 adds repeatability assessment across linked execution receipts.
Milestone 16 adds evidence-bounded drift assessment between replication campaigns.
Milestone 17 adds multiplicity-controlled longitudinal trend assessment.
Milestone 18 closes the credential-free roadmap with machine-readable artifact
conformance and an explicit offline completion boundary.

## Quick examples

```bash
e7q verify examples/bell.e7q --proof bell.proof.json
e7q verify examples/teleportation.e7q --proof teleportation.proof.json
e7q verify examples/deutsch-jozsa-balanced.e7q
e7q verify examples/diagnostic-composition.e7q --proof diagnostic.proof.json
e7q verify examples/noisy-bell.e7q --proof noisy-bell.proof.json
e7q capabilities examples/noisy-bell.e7q
e7q compile examples/nonlocal-cx.e7q --topology linear \
  -o nonlocal-cx.qasm --proof compilation.proof.json
e7q export examples/bell.e7q --format qiskit -o bell_qiskit.py \\
  --proof adapter.proof.json
e7q ingest-calibration examples/ibm-calibration-export.json \\
  --provider ibm -o normalized-calibration.json
e7q select examples/nonlocal-cx.e7q \\
  --snapshot examples/calibration-snapshot.json \\
  --proof selection.proof.json
e7q bundle examples/nonlocal-cx.e7q \\
  --snapshot examples/calibration-snapshot.json \\
  --shots 1000 -o execution-bundle.json
e7q receipt execution-bundle.json \\
  --result provider-result.json -o execution-receipt.json
e7q assess execution-receipt.json \\
  --reference examples/bell-reference.json -o execution-assessment.json
e7q replicate receipt-1.json receipt-2.json receipt-3.json \\
  -o replication-report.json
e7q drift baseline-replication.json candidate-replication.json \\
  -o drift-report.json
e7q trend baseline.json campaign-1.json campaign-2.json \\
  -o trend-report.json
e7q validate-artifact trend-report.json -o conformance-report.json
```

Compare unitary circuits under an explicit criterion:

```bash
e7q compare examples/identity-direct.e7q \
  examples/identity-optimized.e7q \
  --criterion global-phase \
  --proof equivalence.proof.json
```

Supported comparison criteria are exact unitary equality, equality up to
global phase, computational-basis measurement equivalence, and
tolerance-based equality. Dynamic paths containing mid-circuit measurement
or classical control are deliberately excluded from unitary comparison.
Compatible density-matrix programs can additionally use `channel-exact`,
`channel-tolerance`, or `channel-measurement`.

See the [quickstart](docs/QUICKSTART.md), [Milestone 3 guide](docs/MILESTONE_3.md),
[Milestone 4 guide](docs/MILESTONE_4.md),
[Milestone 5 guide](docs/MILESTONE_5.md),
[Milestone 6 guide](docs/MILESTONE_6.md),
[Milestone 7 guide](docs/MILESTONE_7.md),
[Milestone 8 guide](docs/MILESTONE_8.md),
[Milestone 9 guide](docs/MILESTONE_9.md),
[Milestone 10 guide](docs/MILESTONE_10.md),
[Milestone 11 guide](docs/MILESTONE_11.md),
[Milestone 12 guide](docs/MILESTONE_12.md),
[Milestone 13 guide](docs/MILESTONE_13.md),
[Milestone 14 guide](docs/MILESTONE_14.md),
[Milestone 15 guide](docs/MILESTONE_15.md),
[Milestone 16 guide](docs/MILESTONE_16.md),
[Milestone 17 guide](docs/MILESTONE_17.md),
[Milestone 18 guide](docs/MILESTONE_18.md),
[language specification](docs/E7Q_Language_Specification.md), and [roadmap](ROADMAP.md).

## Relationship to E7G-T

E7Q is a separate downstream project. The canonical E7G-T kernel remains
upstream and is not silently modified here. See
[`references/E7GT_UPSTREAM.md`](references/E7GT_UPSTREAM.md).

## Licensing

Copyright © 2026 Alexander Gregory Wingate.

- Source code is licensed under the [Apache License 2.0](LICENSE).
- Specifications, documentation, examples as expressive works, and
  explanatory material are licensed under [CC BY-SA 4.0](LICENSE-DOCS).

See [`NOTICE`](NOTICE) for the controlling licensing notice.

> Experimental software. Do not use E7Q as the sole basis for safety-critical,
> security-critical, financial, medical, or physical-system decisions.
