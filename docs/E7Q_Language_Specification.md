# E7Q Language Specification

**Version:** 0.13.0-dev
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
unitaries and must be rejected by these profiles. Compatible density-matrix
programs additionally support exact and tolerance-based superoperator
equality and computational-basis measurement-behaviour equality. Channel
comparison excludes mid-circuit measurement, classical control, and
assertions.

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

Topology compilation accepts an explicit undirected coupling graph and native
gate set. A non-adjacent two-qubit operation is routed along a shortest path by
inserting a forward SWAP chain, applying the operation, and reversing the
chain. Restoring the logical layout preserves later measurement and classical
control semantics. The compilation report records the physical path, inserted
SWAP count, capability assumptions, and boundary between compilation evidence
and physical execution.

Vendor adapters translate supported static E7Q programs into dependency-free
Python source for IBM Qiskit or Google Cirq. They accept the core gate set and
terminal full-register measurement. Noise, assertions, partial measurement,
and classical control are rejected explicitly. Adapter evidence identifies the
target and operation count, and does not imply SDK installation, job submission,
device calibration, execution, or fidelity.

## 9. Conformance

A v0.5 implementation must retain Bell and equivalence behaviour, execute the
reference teleportation and Deutsch–Jozsa programs, export their supported
operations to OpenQASM 3, compose non-recursive paths, diagnose failed
assertions, round-trip the supported OpenQASM subset, reject invalid
references, and reject dynamic programs from unitary comparison.
It must additionally preserve density-matrix trace under all supported
channels, expose noise-aware evidence and capability requirements, and reject
noise on the state-vector backend.
Topology conformance requires rejection of disconnected coupling graphs and
unsupported native gates, semantics preservation after routing, and an
auditable compilation trace. It does not imply hardware fidelity.
Vendor-adapter conformance requires syntactically valid Python output, complete
static gate and measurement coverage, Proof-of-Path evidence, and explicit
rejection of unsupported program features.


## 10. Resource planning

Resource planning schedules quantum operations into dependency-safe layers,
reports logical and routed gate counts, total depth, two-qubit depth, and SWAP
overhead, and preserves the compilation trace. These values are static
properties of the reference program and selected topology. They do not predict
queue time, monetary cost, device calibration, execution success, or fidelity.

Planning conformance requires deterministic estimates, serialization of gates
sharing a qubit, parallel eligibility for disjoint gates, terminal-measurement
barriers, and a machine-readable boundary statement.

## 11. Calibration snapshots and target selection

A calibration snapshot is a user-supplied, timestamped document declaring
target availability, qubit capacity, topology, native gates, queue depth, and
aggregate single-qubit, two-qubit, and readout error rates. E7Q validates the
snapshot, rejects incompatible targets, topology-compiles each viable target,
and ranks candidates using a documented success proxy.

Selection evidence must distinguish supplied observations from calculated
estimates and include rejected-target reasons. A selection is advisory: it
does not establish live calibration, vendor authenticity, execution cost,
queue time at submission, or physical fidelity.


## 12. Offline vendor calibration ingestion

E7Q may normalize user-supplied IBM/Qiskit-style and Google/Cirq-style
calibration exports into `e7q.calibration/v1`. An adapter must validate its
provider-specific schema, an ISO 8601 timestamp with timezone, target fields,
probability ranges, and an optional maximum-age policy. It must retain provider
and source-schema provenance in the normalized snapshot.

Ingestion is an offline transformation of supplied evidence. Conformance does
not imply network access, vendor authentication, authenticity verification,
live calibration retrieval, job submission, cost knowledge, or guaranteed
hardware fidelity.


## 13. Reproducible execution bundles

E7Q may combine a source program and a supplied calibration snapshot into an
`e7q.execution-bundle/v1` artifact. The bundle must identify its inputs with
SHA-256 digests, name the selected target, contain the topology-routed OpenQASM,
record the shot count and resource plan, and include Proof-of-Path evidence.

Bundle creation is deterministic for identical inputs. A conforming bundle must
distinguish `READY` from `submitted` and default to `submitted: false`.
It is an offline handoff artifact: it does not establish vendor authentication,
job acceptance, queue state, price, physical fidelity, or measured results.


## 14. Execution-result receipts

E7Q may normalize a user-supplied `e7q.execution-result/v1` document against
an `e7q.execution-bundle/v1` artifact. It must validate target and shot
linkage, require non-negative integer counts whose total equals the declared
shots, and record empirical probabilities, input digests, provider metadata,
and Proof-of-Path evidence in `e7q.execution-receipt/v1`.

Receipt conformance establishes internal consistency of the supplied files
only. It does not authenticate the provider, prove that E7Q submitted or
witnessed the job, establish live calibration, or claim cost or physical
fidelity.
