# E7Q v0.1 Quickstart

E7Q Milestone 1 executes the Bell-state source file end to end.

## Install

```bash
python -m pip install -e ".[test]"
```

## Run

```bash
e7q run examples/bell.e7q
```

This prints seeded measurement counts.

## Verify and record Proof-of-Path

```bash
e7q verify examples/bell.e7q --proof bell.proof.json
```

The verifier checks every declared invariant. The JSON report records
initialization, each transformation, measurement, probabilities, counts, and
the resulting pass/fail status.

## Export OpenQASM 3

```bash
e7q export examples/bell.e7q --format openqasm -o bell.qasm
```

## Current boundary

The v0.1 engine supports one quantum register, one classical register,
terminal full-register measurement, state-vector execution, and gates
`X`, `Y`, `Z`, `H`, `S`, `T`, `CX`, `CZ`, and `SWAP`. It is an experimental
reference implementation, not a production quantum runtime.
