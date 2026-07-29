# Milestone 11 — Offline vendor calibration ingestion

Milestone 11 converts user-supplied IBM/Qiskit-style or Google/Cirq-style
calibration exports into the `e7q.calibration/v1` snapshot used by target
selection.

```bash
e7q ingest-calibration examples/ibm-calibration-export.json \
  --provider ibm --max-age-hours 24 -o calibration-snapshot.json
e7q select examples/nonlocal-cx.e7q \
  --snapshot calibration-snapshot.json --proof selection.proof.json
```

The adapter validates the provider schema, timestamp, target fields, error
rates, topology profile, native gates, and optional freshness limit. The
normalized snapshot retains provider and source-schema provenance.

This workflow is deliberately offline. E7Q does not authenticate to IBM or
Google, fetch calibration, verify vendor authenticity, submit jobs, or turn
the selection score into a fidelity guarantee.
