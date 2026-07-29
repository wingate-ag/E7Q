# Milestone 15 — Replication campaigns

Milestone 15 evaluates repeatability across multiple independently supplied
execution receipts that link to the same bundle and target.

## Command

```bash
e7q replicate receipt-1.json receipt-2.json receipt-3.json \
  --max-pairwise-tvd 0.1 \
  --significance-level 0.05 \
  -o replication-report.json
```

E7Q rejects duplicate result digests and mismatched bundle or target linkage.
It reports pooled counts and probabilities, every pairwise total-variation
distance, the maximum distance, and a Pearson chi-square homogeneity test.

## Interpretation boundary

PASS means that the supplied runs satisfy both declared consistency thresholds.
It does not prove that the runs were independent, authenticate their provider,
establish device correctness, validate a reference model, demonstrate quantum
advantage, or establish physical fidelity. Small expected cells weaken the
chi-square approximation and are reported explicitly.
