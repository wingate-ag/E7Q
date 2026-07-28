# Milestone 7 — Topology-aware compilation

Milestone 7 introduces a backend-neutral compilation boundary between a
logical E7Q program and a physically constrained coupling graph.

## Compile a program

```bash
e7q compile examples/nonlocal-cx.e7q \
  --topology linear \
  --output nonlocal-cx.qasm \
  --proof compilation.proof.json
```

Named topologies are `linear`, `ring`, and `all-to-all`. The optional
`--native-gates` argument declares the backend gate set.

For a non-adjacent two-qubit operation, the reference compiler finds a shortest
coupling path, inserts SWAPs to make the operands adjacent, applies the gate,
and reverses the SWAPs. The logical layout is therefore restored before the
next source operation.

The proof records the coupling map, native-gate assumptions, physical route,
inserted SWAP overhead, and the restored-layout invariant.

## Boundary

This compiler does not submit jobs, use vendor credentials, model calibration,
or predict physical fidelity. Its output is a reference OpenQASM 3 program and
an auditable mapping trace.
