# Milestone 18 — Offline Release Conformance

Milestone 18 closes the credential-free E7Q roadmap as a v1.0 release
candidate. It adds a stable registry for the offline artifact families produced
from calibration ingestion through longitudinal trend assessment.

## Command

```bash
e7q validate-artifact trend-report.json -o conformance-report.json
```

The command checks that an artifact declares a registered schema and contains
the required top-level evidence for that artifact family. It emits a
deterministic `e7q.conformance-report/v1`.

This is structural conformance, not full semantic recomputation. A PASS does
not authenticate a provider, attest chronology or run independence, prove that
hardware executed a bundle, or establish correctness or physical fidelity.

## Completion boundary

E7Q v1.0rc1 is complete as an offline, provider-neutral language, simulator,
compiler, evidence, and analysis toolchain. Live retrieval, authenticated
submission, and vendor attestations are integrations requiring provider
credentials, contracts, and external service access; they are explicitly
outside the offline release.
