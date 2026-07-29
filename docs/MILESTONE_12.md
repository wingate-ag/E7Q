# Milestone 12 — Reproducible execution bundles

Milestone 12 creates a provider-neutral, offline handoff artifact from an E7Q
program and a supplied calibration snapshot.

```bash
e7q bundle examples/nonlocal-cx.e7q \
  --snapshot examples/calibration-snapshot.json \
  --shots 1000 -o execution-bundle.json
```

The bundle records the selected target, routed OpenQASM, resource plan,
calibration timestamp, shot count, source and snapshot hashes, and a
Proof-of-Path. Identical inputs produce identical bundles.

A bundle is preparation evidence, not execution evidence. It stores no
credentials, performs no network access, submits no job, and makes no claim
about queue time, price, physical fidelity, or measured results.
