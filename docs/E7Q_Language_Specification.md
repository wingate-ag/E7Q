# E7Q Language Specification

**Version:** 0.5.0-dev
**Status:** experimental draft
**Documentation licence:** CC-BY-SA-4.0

## 1. Purpose

E7Q describes quantum computations with intended invariants, equivalence
criteria, measurement context, and an auditable execution path. Standard
quantum mathematics is normative for execution. E7G-T supplies the
modelling and accountability vocabulary.

## 2. Program model

A program contains a context, one quantum register, one classical register,
invariants, one or more named paths, and a verification target. A path is an
ordered sequence of unitary transformations, measurements, classically
conditioned transformations, assertions, and reusable-path references.

## 3. Core types and context

- `qubits q[n]`: an n-qubit register initially in `|0…0⟩`;
- `bits c[n]`: an n-bit classical register initially containing zeroes;
- context settings: `backend`, `shots`, and optional deterministic `seed`.
  The reference backends are `statevector` and `densitymatrix`.

## 4. Operations

The gates `X`, `Y`, `Z`, `H`, `S`, `T`, `CX`, `CZ`, and `SWAP` have their
conventional matrix semantics.

`measure q -> c` measures the complete quantum register into the classical
register and must terminate the path. `measure q[i] -> c[j]` measures and
collapses one qubit, stores the result, and permits subsequent operations.

`if c[j] == b G q[i]` applies the one-qubit gate `G` only when classical bit
`c[j]` equals `b`, where `b` is zero or one.

`use PathName` expands another declared path at the point of use. References
must exist and must not be recursive.

`assert c[j] == b` checks the classical value for every shot. It contributes a
verification check and records its failed-shot count and Proof-of-Path step.

`noise bit_flip(p) q[i]`, `noise phase_flip(p) q[i]`, and
`noise depolarizing(p) q[i]` apply declared single-qubit quantum channels with
`0 <= p <= 1`. Noise currently requires the `densitymatrix` backend and
terminal full-register measurement.

## 5. Invariants

`normalized` requires the final per-shot state norm to be one within numerical
tolerance. `outcomes in {…}` constrains classical-register-width bitstrings.
For dynamic execution, the constraint applies to all observed shot outcomes.

## 6. Execution

Purely unitary paths followed by full-register measurement retain exact ideal
probabilities. Dynamic paths execute shot by shot: each measurement samples
the Born distribution, collapses and renormalizes the state, records its
classical result, and controls later conditional gates.

The density-matrix backend evolves `ρ` by `UρU†` and noise by Kraus maps. It
reports trace and purity after every transformation or channel. This reference
model does not claim fidelity to an unspecified physical device.

## 7. Equivalence profiles

The implemented profiles are exact unitary equality, equality up to global
phase, computational-basis measurement equivalence, and tolerance equality.
Programs containing partial measurement or classical control are not
unitaries and must be rejected by these profiles. Future channel-level
profiles may compare non-unitary dynamic programs.

## 8. Proof-of-Path

A report records initialization, ordered transformations, projections,
classical conditions, assertions, executed and skipped branch counts, final
outcomes, and invariant results. When an assertion fails, `first_failure`
identifies its step and failed-shot count. This is evidence for the declared
execution, not proof of a new physical theory.

For noisy execution, the report distinguishes `transform`, `channel`, and
`project` steps and records channel probability, trace, and purity. A backend
capability profile declares required features and preserves the boundary
between reference simulation and hardware-specific compilation.

## 9. Conformance

A v0.5 implementation must retain Bell and equivalence behaviour, execute the
reference teleportation and Deutsch–Jozsa programs, export their supported
operations to OpenQASM 3, compose non-recursive paths, diagnose failed
assertions, round-trip the supported OpenQASM subset, reject invalid
references, and reject dynamic programs from unitary comparison.
It must additionally preserve density-matrix trace under all supported
channels, expose noise-aware evidence and capability requirements, and reject
noise on the state-vector backend.
