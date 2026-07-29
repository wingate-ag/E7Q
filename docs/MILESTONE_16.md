# Milestone 16 — Campaign Drift

Milestone 16 compares the pooled finite-sample distributions of two supplied
replication campaigns.

## Command

```bash
e7q drift baseline-replication.json candidate-replication.json \
  --max-total-variation 0.1 --significance-level 0.05 \
  -o drift-report.json
```

The command validates a common target and outcome width, recomputes
probabilities from pooled counts, reports total-variation distance, and applies
a two-sample Pearson chi-square homogeneity test.

`NO_DRIFT` means both declared thresholds pass. `DRIFT` means at least one
fails. Neither verdict authenticates chronology, identifies a cause,
authenticates a provider, proves hardware stability, or establishes fidelity.
Low expected counts are disclosed because they weaken the asymptotic test.
