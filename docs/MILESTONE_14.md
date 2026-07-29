# Milestone 14 — Statistical result assessment

Milestone 14 compares an execution receipt with an explicit reference
distribution while preserving the boundary between statistical consistency
and physical proof.

## Command

```bash
e7q assess execution-receipt.json \
  --reference examples/bell-reference.json \
  -o execution-assessment.json
```

The reference declares expected probabilities, a maximum total-variation
distance, and a significance level. E7Q reports total-variation distance,
Pearson's chi-square statistic, degrees of freedom, the asymptotic p-value,
threshold checks, and any warning about expected cells below five.

## Interpretation boundary

PASS means that this finite sample satisfies both declared thresholds. It does
not prove provider authenticity, device correctness, the reference model,
quantum advantage, or physical fidelity. The chi-square p-value is an
asymptotic diagnostic and becomes less dependable when expected cell counts
are small.
