# E7Q Language Specification

**Version:** 0.3.0-dev  
**Status:** experimental draft  
**Documentation licence:** CC-BY-SA-4.0

## 1. Purpose

E7Q describes quantum computations with intended invariants, equivalence
criteria, measurement context, and an auditable execution path. Standard
quantum mathematics is normative for execution. E7G-T supplies the
modelling and accountability vocabulary.

## 2. Program model

A program contains a context, one quantum register, one classical register,
invariants, a named path, and a verification target. A path is an ordered
sequence of unitary transformations, measurements, and classically
conditioned transformations.

## 3. Core types and context

- `qubits q[n]`: an n-qubit register initially in `|0…0⟩`;
- `bits c[n]`: an n-bit classical register initially containing zeroes;
- context settings: `backend`, `shots`, and optional deterministic `seed`.

## 4. Operations

The gates `X`, `Y`, `Z`, `H`, `S`, `T`, `CX`, `CZ`, and `SWAP` have their
conventional matrix semantics.

`measure q -> c` measures the complete quantum register into the classical
register and must terminate the path. `measure q[i] -> c[j]` measures and
collapses one qubit, stores the result, and permits subsequent operations.

`if c[j] == b G q[i]` applies the one-qubit gate `G` only when classical bit
`c[j]` equals `b`, where `b` is zero or one.

## 5. Invariants

`normalized` requires the final per-shot state norm to be one within numerical
tolerance. `outcomes in {…}` constrains classical-register-width bitstrings.
For dynamic execution, the constraint applies to all observed shot outcomes.

## 6. Execution

Purely unitary paths followed by full-register measurement retain exact ideal
probabilities. Dynamic paths execute shot by shot: each measurement samples
the Born distribution, collapses and renormalizes the state, records its
classical result, and controls later conditional gates.

## 7. Equivalence profiles

The implemented profiles are exact unitary equality, equality up to global
phase, computational-basis measurement equivalence, and tolerance equality.
Programs containing partial measurement or classical control are not
unitaries and must be rejected by these profiles. Future channel-level
profiles may compare non-unitary dynamic programs.

## 8. Proof-of-Path

A report records initialization, ordered transformations, projections,
classical conditions, executed and skipped branch counts, final outcomes,
and invariant results. This is evidence for the declared execution, not proof
of a new physical theory.

## 9. Conformance

A v0.3 implementation must retain Bell and equivalence behaviour, execute the
reference teleportation and Deutsch–Jozsa programs, export their supported
operations to OpenQASM 3, reject invalid references, and reject dynamic
programs from unitary comparison.
