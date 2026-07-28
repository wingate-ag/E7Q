# E7Q Language Specification

**Version:** 0.1.0-dev  
**Status:** experimental draft  
**Documentation licence:** CC-BY-SA-4.0

## 1. Purpose

E7Q describes quantum computations together with their intended invariants, equivalence criteria, measurement context, and auditable execution path. Standard quantum mathematics is normative for execution; E7G-T is normative only for the modelling/accountability vocabulary adopted here.

## 2. Program model

A program contains a context, register declarations, invariant declarations, named paths, and a verification target. A path is an ordered sequence of transformations and measurements.

## 3. Core types

- `qubits q[n]`: n-qubit register initially in |0…0⟩.
- `bits c[n]`: n-bit classical register.
- context values: backend, shots, seed, tolerance, and later noise/basis profiles.

## 4. Operations

v0.1 reserves X, Y, Z, H, S, T, CX, CZ, SWAP, and `measure`. Gates have their conventional matrix semantics. Measurement uses the Born rule in the declared basis; computational basis is the v0.1 default.

## 5. Invariants

`normalized` requires state norm 1 within the declared numerical tolerance. `outcomes in {…}` constrains permitted measured bitstrings. Future revisions will add typed predicates and stage-scoped properties.

## 6. Equivalence profiles

Implementations must label comparisons as one of: exact operator equality; equality up to global phase; equality on a declared input subspace; measurement equivalence in a declared basis; selected-observable equivalence; approximate equivalence within tolerance; or backend-operational equivalence. No profile implies another unless the specification states it.

## 7. Proof-of-Path

A report records source identity, semantics profile, initial configuration, ordered operations, invariant results by stage, compiler rewrites, equivalence criteria, measurement/projective loss, backend facts, output evidence, and limitations. A report is evidence of the declared execution, not proof of a new physical theory.

## 8. Conformance

A v0.1 implementation must parse the reference Bell example, reproduce its ideal state probabilities, reject forbidden outcomes under ideal simulation, expose deterministic seeding, and report invariant results.
