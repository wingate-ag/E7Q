# Milestone 17 — Longitudinal Trends

Milestone 17 compares an ordered series of supplied replication campaigns with
the first campaign as the declared baseline.

## Command

```bash
e7q trend baseline.json campaign-1.json campaign-2.json \
  --max-total-variation 0.1 --significance-level 0.05 \
  -o trend-report.json
```

The command validates a common target and outcome space, performs a
baseline-relative drift assessment for every later campaign, and applies a
Bonferroni-adjusted significance level across the repeated chi-square tests.
It records the first campaign index that breaches either the distance or
adjusted significance threshold.

`NO_TREND_DETECTED` means no supplied candidate breached the declared
thresholds. `TREND_DETECTED` means at least one did. Input order is treated as
declared sequence only; E7Q does not authenticate timestamps, continuous
monitoring, provider provenance, causation, device stability, or fidelity.
