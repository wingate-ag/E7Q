# Milestone 13 — Execution-result receipts

Milestone 13 closes the offline handoff loop without adding vendor credentials
or claiming live hardware access.

## Command

```bash
e7q receipt execution-bundle.json \
  --result provider-result.json \
  -o execution-receipt.json
```

The supplied result uses `e7q.execution-result/v1`:

```json
{
  "schema": "e7q.execution-result/v1",
  "provider": "example-provider",
  "job_id": "job-123",
  "target": "reference-all-to-all-3",
  "shots": 1000,
  "counts": {"00": 496, "11": 504},
  "completed_at": "2026-07-29T12:00:00Z"
}
```

E7Q verifies target and shot linkage, count integrity, binary outcome shape,
and an optional bundle digest. It then records normalized counts, empirical
probabilities, input digests, and Proof-of-Path evidence.

## Boundary

The receipt proves internal consistency of supplied files. It does not prove
provider authenticity, job submission, observation by E7Q, device calibration,
cost, or physical fidelity.
