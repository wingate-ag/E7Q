# Roadmap

## v0.1 — Minimum Executable Language

- [x] parser, state-vector simulator, verifier, CLI, and CI;
- [x] core gates, terminal measurement, invariants, OpenQASM export;
- [x] JSON Proof-of-Path and Bell-state reference test.

## v0.2 — Circuit equivalence

- [x] exact, global-phase, computational-basis measurement, and tolerance equivalence;
- [x] comparison CLI and Proof-of-Path reports;
- [x] optimisation examples and regression tests.

## v0.3 — Dynamic algorithms

- [x] partial and mid-circuit measurement;
- [x] classical-bit feed-forward;
- [x] quantum teleportation reference program;
- [x] Deutsch–Jozsa balanced-oracle reference program;
- [x] aggregate dynamic Proof-of-Path tracing;
- [x] OpenQASM 3 export for dynamic operations;
- [ ] channel-level equivalence for non-unitary programs.

## v0.4 — Composition and diagnostics

Reusable paths, stronger properties, first-failing-transformation
diagnostics, OpenQASM import and round-trip validation.

## v0.5 — Noise and backend bridge

Density matrices, basic noise channels, IR adapters, topology-aware mapping,
capability profiles, compilation traces, and noise-aware evidence.
