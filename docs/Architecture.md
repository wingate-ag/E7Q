# Architecture

1. **E7Q source** declares context, registers, invariants, paths, views, and criteria.
2. **Parser and typed IR** resolve syntax, resources, types, and source locations.
3. **Quantum semantics engine** uses standard linear algebra for evolution and measurement.
4. **Verification engine** checks invariants and equivalence profiles at declared stages.
5. **Adapters** lower verified IR to simulators, OpenQASM, and later hardware-oriented IRs.
6. **Proof-of-Path reporter** records operations, assumptions, property status, projection loss, backend changes, and evidence.
7. **Temporal-evidence profile** records the temporal carrier, declared order,
   chronology status, temporal projection, preservation and loss, criterion,
   phase, and boundary crossing supported by each offline artifact.

## Boundary

The E7G-T mapping organises modelling and accountability. It does not manufacture amplitudes, probabilities, unitary dynamics, or empirical validity. Those originate in the declared quantum semantics profile.

The temporal profile organises evidence about order and history. It does not
authenticate a timestamp, infer elapsed physical time, establish causation, or
claim additional physical time dimensions.

## v0.1 implementation

The first implementation uses a deliberately small parser, typed structures, a NumPy state-vector engine, deterministic seeded measurement, invariant checks, and JSON/Markdown reports.
