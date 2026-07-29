# Milestone 9 — Resource estimation and target planning

Milestone 9 compares the logical E7Q program with its topology-routed form
before any vendor SDK or hardware boundary is crossed.

## Produce a planning report

```bash
e7q plan examples/nonlocal-cx.e7q --topology linear \
  --proof plan.proof.json
```

The report contains gate counts, dependency-aware depth, two-qubit depth,
inserted SWAPs, and logical-to-compiled overhead. Linear, ring, and all-to-all
coupling maps use the same compiler semantics introduced in Milestone 7.

## Scheduling semantics

Operations sharing a qubit are serialized. Operations on disjoint qubits may
occupy the same layer. Terminal measurement forms a barrier. Assertions and
declared noise evidence are not silently converted into hardware gates.

## Boundary

The planner reports static reference estimates only. It does not use
credentials, submit jobs, inspect live calibration, predict queue time or
monetary cost, or claim physical fidelity.
