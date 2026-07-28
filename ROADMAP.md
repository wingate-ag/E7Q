# Roadmap

## v0.1 — Minimum Executable Language

- grammar and semantic model;
- qubits, classical bits, X/Y/Z/H/S/T/CX/CZ/SWAP, and measurement;
- state-vector simulation;
- invariant declarations and checks;
- executable parser, simulator, verifier, and CLI;
- OpenQASM export;
- JSON Proof-of-Path reports;
- Bell-state reference tests.

## v0.2 — Composition and verification

- [x] circuit comparison;
- [x] exact, global-phase, computational-basis measurement, and tolerance equivalence;
- [x] comparison Proof-of-Path reports;
- [ ] reusable paths and stronger properties;
- [ ] density matrices and basic noise channels;
- [ ] partial measurement;
- [ ] first-failing-transformation diagnostics;
- [ ] OpenQASM import and round-trip validation.

## v0.3 — Backend bridge

IR adapters, topology-aware mapping, capability profiles, compilation traces, and noise-aware evidence.
