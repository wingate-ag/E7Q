# Milestone 10 — Calibration snapshots and target selection

Milestone 10 ranks compatible targets using a user-supplied, timestamped
calibration snapshot.

## Select a target

```bash
e7q select examples/nonlocal-cx.e7q \
  --snapshot examples/calibration-snapshot.json \
  --proof selection.proof.json
```

Each candidate is topology-compiled before scoring. The transparent success
proxy combines the compiled single-qubit gate count, two-qubit gate count,
measured-qubit count, and supplied error rates. Ties use queue depth and then
target name for deterministic results.

## Evidence boundary

The report separates snapshot observations from calculated estimates. E7Q does
not fetch live calibration, authenticate to a vendor, submit a job, predict
price, or guarantee physical fidelity.
