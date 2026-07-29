# Milestone 8 — Vendor SDK adapters

Milestone 8 turns a supported static E7Q program into readable Python source
for two established quantum SDKs.

## Export IBM Qiskit source

```bash
e7q export examples/bell.e7q --format qiskit \
  --output bell_qiskit.py --proof adapter.proof.json
```

## Export Google Cirq source

```bash
e7q export examples/bell.e7q --format cirq \
  --output bell_cirq.py --proof adapter.proof.json
```

The generated source contains the circuit construction only. E7Q itself does
not add Qiskit or Cirq as runtime dependencies.

## Supported boundary

The adapters support X, Y, Z, H, S, T, CX, CZ, SWAP, and terminal
full-register measurement. They reject noise, assertions, partial measurement,
and classical feed-forward instead of silently changing their meaning.

The Proof-of-Path identifies the adapter target, register sizes, and operation
count. It does not establish that an SDK is installed, submit a job, use
credentials, inspect device calibration, or claim hardware fidelity.
