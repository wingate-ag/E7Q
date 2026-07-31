# E7Q

**Auditable verification and evidence for quantum programs and experimental results.**

E7Q helps you state what must remain true, run or hand off quantum work, and
produce a reproducible Proof-of-Path showing what the evidence supports—and
what it does not.

It complements quantum SDKs rather than replacing them.

## See the difference

Suppose two sets of quantum runs look similar. Did the observed distribution
remain within your declared limits, or did it materially change?

```bash
e7q drift baseline-replication.json candidate-replication.json \
  --max-total-variation 0.10 \
  --significance-level 0.05 \
  -o drift-report.json
```

E7Q validates that the campaigns are comparable, recomputes their pooled
distributions, measures total-variation distance, applies a two-sample
chi-square test, and records the result in a deterministic report.

```json
{
  "schema": "e7q.drift-report/v1",
  "status": "NO_DRIFT",
  "drift_detected": false,
  "total_variation": 0.02,
  "max_total_variation": 0.1,
  "significance_level": 0.05
}
```

`NO_DRIFT` has a deliberately narrow meaning: neither declared threshold was
breached in the supplied data. It does not authenticate the provider or
timeline, prove hardware stability, establish physical fidelity, or rule out
an undetected change.

That distinction is the point of E7Q: useful conclusions, explicit limits, and
a reviewable evidence trail.

## Why E7Q instead of just X?

| Tool | What it is primarily for | What E7Q adds |
| --- | --- | --- |
| Qiskit / Cirq | Building and executing quantum circuits | Declared invariants, verification targets, offline handoff artifacts, and bounded evidence reports |
| OpenQASM | Representing quantum programs | Higher-level intent, executable assertions, and Proof-of-Path |
| Unit tests | Checking expected software behavior | Quantum-aware equivalence criteria, evidence provenance, and explicit limits on every verdict |
| Provider dashboards | Viewing provider-specific jobs and results | Portable receipts, replication, drift, and trend reports that can be reviewed offline |
| E7G-T | General invariant-aware reasoning and projection discipline | A concrete, executable quantum-domain implementation |

Use Qiskit, Cirq, OpenQASM, and provider services for what they do well. Use E7Q
when you also need to answer:

- What was supposed to remain invariant?
- Which transformation and backend assumptions were used?
- Which evidence supports the result?
- Can another reviewer reproduce the assessment?
- What does the result not establish?

## What E7Q does

- Executes and verifies invariant-aware quantum programs.
- Compares circuits under explicit equivalence criteria.
- Supports state-vector and density-matrix reference execution.
- Represents noise channels and backend capabilities.
- Compiles against declared topologies with auditable SWAP-routing traces.
- Exports dependency-free Qiskit, Cirq, and OpenQASM source.
- Estimates resources and selects targets from offline calibration snapshots.
- Produces execution bundles for credentialed handoff.
- Links returned counts to execution receipts.
- Assesses distributions, replication, campaign drift, and longitudinal trends.
- Records temporal carrier, ordering, projection loss, phase criteria, and
  boundary crossings in machine-readable evidence.
- Validates the structure of registered E7Q artifacts.

## What E7Q does not establish

E7Q is not a new physical theory or a replacement for established quantum
mathematics. It does not by itself:

- execute on authenticated quantum hardware;
- authenticate providers, timestamps, calibration data, or returned results;
- prove that a device is stable or physically faithful;
- establish causation from a detected statistical change;
- turn finite-sample non-detection into proof of equivalence;
- make a structurally conformant artifact semantically true.

## Five-minute start

Requires Python 3.11 or later.

```bash
git clone https://github.com/wingate-ag/E7Q.git
cd E7Q
python -m pip install -e ".[test]"

e7q verify examples/bell.e7q --proof bell.proof.json
```

The verifier checks every declared invariant. The generated JSON records the
initialization, transformations, measurements, probabilities, counts, and
pass/fail result.

Compare two unitary circuits under an explicit criterion:

```bash
e7q compare examples/identity-direct.e7q \
  examples/identity-optimized.e7q \
  --criterion global-phase \
  --proof equivalence.proof.json
```

Prepare an offline execution handoff and assess the returned result:

```bash
e7q bundle examples/nonlocal-cx.e7q \
  --snapshot examples/calibration-snapshot.json \
  --shots 1000 \
  -o execution-bundle.json

e7q receipt execution-bundle.json \
  --result provider-result.json \
  -o execution-receipt.json

e7q assess execution-receipt.json \
  --reference examples/bell-reference.json \
  -o execution-assessment.json
```

## Evidence and validation

E7Q's credential-free core is complete as a v1.0 release candidate.

- The parser is fail-closed for unconsumed input and ambiguous duplicate
  declarations.
- The repository test suite passes across Python 3.11–3.13.
- Independent validation compares tested behavior with NumPy, Qiskit, Cirq,
  and SciPy routes.
- Proof-of-Path artifacts are deterministic for the tested workflows.

These results support the tested software behavior within the stated
environment. They do not constitute comprehensive mathematical validation,
provider authentication, real-hardware validation, or evidence for a new
physical theory.

Artifact validation reports `PASS` with
`conformance: STRUCTURALLY_CONFORMANT` and `validation_scope: structure-only`
only when the registered schema and required top-level evidence are present.

## Documentation

- [Quickstart](docs/QUICKSTART.md)
- [Language specification](docs/E7Q_Language_Specification.md)
- [E7G-T to E7Q mapping](docs/E7GT_Quantum_Mapping.md)
- [Temporal-evidence profile](docs/TEMPORAL_EVIDENCE_PROFILE.md)
- [Roadmap](ROADMAP.md)
- [Offline completion boundary](docs/MILESTONE_18.md)
- [E7G-T upstream relationship](references/E7GT_UPSTREAM.md)

The milestone guides in [`docs/`](docs/) preserve the implementation history
and detailed usage of each capability.

## Relationship to E7G-T

E7Q is a downstream implementation of E7G-T's invariant, transformation,
projection, measurement-accountability, temporal-geometry, and Proof-of-Path
principles. E7Q v1.0rc2 pins E7G-T v0.11-UC1 and implements a bounded
temporal-evidence profile for quantum workflows. The canonical E7G-T kernel
remains a separate upstream project and is not silently modified by E7Q.

## License

Copyright © 2026 Alexander Gregory Wingate and Oleksandr Razinkov.

- Source code: [Apache License 2.0](LICENSE)
- Specifications, documentation, examples as expressive works, and
  explanatory material: [CC BY-SA 4.0](LICENSE-DOCS)

See [`NOTICE`](NOTICE) for the controlling licensing notice.

> Experimental software. Do not use E7Q as the sole basis for safety-critical,
> security-critical, financial, medical, or physical-system decisions.
