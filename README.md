# E7Q

**An experimental E7G-T-based, invariant-aware quantum programming and verification language.**

E7Q combines established quantum mathematics for execution with E7G-T
composition, transformation, equivalence, projection, measurement
accountability, and Proof-of-Path.

E7Q is **not** a new physical theory. It does not replace Hilbert spaces,
unitary evolution, quantum channels, the Born rule, or hardware-specific
compilation.

## Status

Pre-alpha. Milestones 1–3 provide the executable language, circuit
equivalence, partial measurement, classical feed-forward, quantum
teleportation, and Deutsch–Jozsa reference programs. Milestone 4 adds
reusable paths, executable assertions, first-failure diagnostics, and
OpenQASM subset round trips.
Milestone 5 adds a density-matrix reference backend, declared noise channels,
noise-aware evidence, and machine-readable backend capability profiles.

## Quick examples

```bash
e7q verify examples/bell.e7q --proof bell.proof.json
e7q verify examples/teleportation.e7q --proof teleportation.proof.json
e7q verify examples/deutsch-jozsa-balanced.e7q
e7q verify examples/diagnostic-composition.e7q --proof diagnostic.proof.json
e7q verify examples/noisy-bell.e7q --proof noisy-bell.proof.json
e7q capabilities examples/noisy-bell.e7q
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

See the [quickstart](docs/QUICKSTART.md), [Milestone 3 guide](docs/MILESTONE_3.md),
[Milestone 4 guide](docs/MILESTONE_4.md),
[Milestone 5 guide](docs/MILESTONE_5.md),
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
