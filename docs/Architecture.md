# Architecture

1. **E7Q source** declares context, registers, invariants, paths, views, and criteria.
2. **Parser and typed IR** resolve syntax, resources, types, and source locations.
3. **Quantum semantics engine** uses standard linear algebra for evolution and measurement.
4. **Verification engine** checks invariants and equivalence profiles at declared stages.
5. **Adapters** lower verified IR to simulators, OpenQASM, and later hardware-oriented IRs.
6. **Proof-of-Path reporter** records operations, assumptions, property status, projection loss, backend changes, and evidence.
7. **Temporal-evidence profile** records the concrete carrier description,
   TD0--TD7 order roles, declared order, chronology status, temporal
   projection, preservation and loss, versioned criterion, phase, and boundary
   crossing supported by each offline artifact.
8. **Observational-claim pilot** optionally separates supplied records and
   bounded observational claims from E7Q's statistical interpretations, while
   preserving shared divergence, unknowns, and temporal-extension boundaries.

## Boundary

The E7G-T mapping organises modelling and accountability. It does not manufacture amplitudes, probabilities, unitary dynamics, or empirical validity. Those originate in the declared quantum semantics profile.

The temporal profile organises evidence about order and history. It does not
authenticate a timestamp, infer elapsed physical time, establish causation, or
claim additional physical time dimensions.

The observation pilot is an informative E7G-T UC2 experiment. It does not make
an observer's available records equivalent to reality, turn agreement into
truth, or upgrade an offline verdict into provider or hardware validation.

## v0.1 implementation

The first implementation uses a deliberately small parser, typed structures, a NumPy state-vector engine, deterministic seeded measurement, invariant checks, and JSON/Markdown reports.
