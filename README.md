# E7Q

**An experimental E7G-T-based, invariant-aware quantum programming and verification language.**

E7Q explores a practical division of labour:

- established quantum mathematics supplies executable semantics;
- E7G-T supplies explicit composition, transformation, equivalence, projection, measurement accountability, and Proof-of-Path.

E7Q is **not** a new physical theory and does not replace Hilbert spaces, unitary evolution, quantum channels, the Born rule, or hardware-specific compilation. It is a research and engineering project for describing what a quantum computation is intended to preserve, why implementations count as equivalent, what measurement discards, and how execution evidence supports a conclusion.

## Status

Pre-alpha / specification-first. The initial milestone is **v0.1 — Minimum Executable Language**.

## Intended capabilities

- textual quantum DSL;
- quantum and classical registers;
- core gates and measurement;
- invariant declarations;
- explicit equivalence criteria;
- state-vector simulation;
- OpenQASM export;
- E7G-T Proof-of-Path reports;
- backend-aware verification and optimisation in later milestones.

## Example

```e7q
context BellExperiment {
  shots: 1000
  backend: statevector
}

qubits q[2]
bits c[2]

invariant normalized
invariant outcomes in {00, 11}

path CreateBellPair {
  H q[0]
  CX q[0], q[1]
  measure q -> c
}

verify CreateBellPair
```

See [`examples/bell.e7q`](examples/bell.e7q), the [language specification](docs/E7Q_Language_Specification.md), and the [roadmap](ROADMAP.md).

## Relationship to E7G-T

E7Q is a separate downstream project. The canonical E7G-T kernel remains upstream and is not silently modified here. See [`references/E7GT_UPSTREAM.md`](references/E7GT_UPSTREAM.md).

## Licensing

Copyright © 2026 Alexander Gregory Wingate.

- Source code is licensed under the [Apache License 2.0](LICENSE).
- Specifications, documentation, examples as expressive works, and explanatory material are licensed under [CC BY-SA 4.0](LICENSE-DOCS).

Where a file is ambiguous, its SPDX header or the repository licensing notice controls. See [`NOTICE`](NOTICE).

## Contributing

The project welcomes careful, testable contributions. Read [`CONTRIBUTING.md`](CONTRIBUTING.md) and [`GOVERNANCE.md`](GOVERNANCE.md) before proposing changes.

> Experimental software. Do not use E7Q as the sole basis for safety-critical, security-critical, financial, medical, or physical-system decisions.
