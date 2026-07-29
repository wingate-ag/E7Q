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

## v0.7 — Topology-aware compilation

- [x] backend-neutral linear, ring, and all-to-all coupling maps;
- [x] shortest-path routing for non-adjacent two-qubit gates;
- [x] semantics-preserving SWAP insertion with restored logical layout;
- [x] native-gate capability validation;
- [x] compilation Proof-of-Path with routing and overhead evidence;
- [x] IBM Qiskit and Google Cirq source adapters;
- [ ] credential-dependent hardware submission;
- [ ] calibrated cost models and hardware-derived fidelity estimates.

## v0.8 — Vendor SDK adapters

- [x] dependency-free IBM Qiskit Python source export;
- [x] dependency-free Google Cirq Python source export;
- [x] adapter Proof-of-Path evidence and CLI integration;
- [x] explicit rejection of unsupported dynamic and noisy programs;
- [ ] credential-dependent hardware submission;
- [ ] calibrated cost models and hardware-derived fidelity estimates.


## v0.9 — Resource estimation and target planning

- [x] deterministic logical and routed gate counts;
- [x] dependency-aware circuit depth and two-qubit depth;
- [x] routing-overhead comparison;
- [x] machine-readable planning Proof-of-Path;
- [x] explicit static-estimate boundary;
- [ ] credential-dependent hardware submission;
- [ ] calibration-derived cost and fidelity estimates.

## v0.10 — Calibration snapshots and target selection

- [x] versioned, timestamped offline calibration snapshots;
- [x] compatibility filtering and topology-aware candidate planning;
- [x] transparent success-proxy ranking with deterministic ties;
- [x] observed-versus-estimated Proof-of-Path evidence;
- [x] explicit rejection of live-data, submission, cost, and fidelity claims;
- [ ] credential-dependent hardware submission;
- [x] vendor calibration ingestion adapters.

## v0.11 — Offline calibration ingestion

- [x] IBM/Qiskit-style supplied-export normalization;
- [x] Google/Cirq-style supplied-export normalization;
- [x] schema, timestamp, error-rate, and freshness validation;
- [x] provider and source-schema provenance;
- [x] CLI integration and normalized snapshot output;
- [x] explicit offline and authenticity boundary;
- [ ] credential-dependent live vendor retrieval;
- [ ] credential-dependent hardware submission.


## v0.12 — Reproducible execution bundles

- [x] deterministic provider-neutral execution bundle schema;
- [x] selected-target and routed OpenQASM capture;
- [x] source, snapshot, and compiled-artifact hashes;
- [x] resource plan, shot count, and Proof-of-Path evidence;
- [x] explicit ready-versus-submitted state;
- [x] CLI integration and regression tests;
- [ ] credential-dependent live vendor retrieval;
- [ ] credential-dependent hardware submission.

## v0.13 — Execution-result receipts

- [x] provider-neutral supplied-result schema;
- [x] strict bundle, target, shot, and count linkage validation;
- [x] deterministic receipt with empirical probabilities and input digests;
- [x] Proof-of-Path provenance and evidence boundary;
- [x] CLI integration, documentation, and regression tests;
- [ ] credential-dependent provider authentication and hardware submission.


## v0.14 — Statistical result assessment

- [x] explicit reference-distribution schema and validation;
- [x] total-variation distance and Pearson chi-square evidence;
- [x] dependency-free asymptotic p-value calculation;
- [x] configurable distance and significance thresholds;
- [x] deterministic assessment report and Proof-of-Path boundary;
- [x] CLI integration, documentation, examples, and regression tests;
- [ ] provider-authenticated result retrieval and hardware attribution.

## v0.15 — Replication campaigns

- [x] same-bundle and same-target receipt validation;
- [x] duplicate-result rejection and pooled count evidence;
- [x] pairwise total-variation repeatability diagnostics;
- [x] chi-square homogeneity assessment and low-cell warnings;
- [x] deterministic replication Proof-of-Path and CLI integration;
- [x] explicit offline, independence, authenticity, and fidelity boundary;
- [ ] provider-authenticated campaign retrieval and run independence attestation.
