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
- [x] channel-level equivalence for non-unitary programs.

## v0.4 — Composition and diagnostics

- [x] reusable path composition with recursion rejection;
- [x] executable classical assertions;
- [x] first-failing-step diagnostics in verification reports;
- [x] OpenQASM 3 subset import and round-trip validation.

## v0.5 — Noise and backend bridge

- [x] density-matrix reference backend;
- [x] bit-flip, phase-flip, and depolarizing channels;
- [x] trace, purity, and channel evidence in Proof-of-Path;
- [x] backend capability profiles and an explicit simulator/hardware boundary;
- [ ] vendor IR adapters and topology-aware mapping;
- [ ] compilation traces for physical backends;
- [x] channel-level equivalence for non-unitary programs.

## v0.6 — Channel equivalence

- [x] exact and tolerance-based density-matrix channel comparison;
- [x] computational-basis measurement-behaviour comparison for channels;
- [x] superoperator Proof-of-Path evidence;
- [x] explicit rejection of incompatible or dynamic programs.
