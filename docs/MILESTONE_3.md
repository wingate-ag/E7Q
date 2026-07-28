# Milestone 3: Dynamic Algorithms

Milestone 3 introduces the minimum dynamic-circuit semantics needed for
quantum teleportation:

- single-qubit measurement into a selected classical bit;
- state collapse under the Born rule;
- continued quantum execution after measurement;
- single-bit classical conditions on one-qubit gates;
- aggregate Proof-of-Path evidence for executed and skipped branches.

## Syntax

```e7q
measure q[0] -> c[0]
if c[0] == 1 X q[2]
```

The reference teleportation example prepares `|1>` on `q[0]`, transfers it to
`q[2]`, and proves through allowed outcomes that the final classical bit is
always `1`. The Deutsch–Jozsa example uses a balanced oracle and proves that
the input-register result is nonzero.

Dynamic programs are not accepted by unitary circuit comparison. Measurement
and classical feed-forward are non-unitary operations, so comparing them as
unitary matrices would make a false semantic claim. A future channel-level
comparison profile can cover these programs.

## Commands

```bash
e7q verify examples/teleportation.e7q --proof teleportation.proof.json
e7q verify examples/deutsch-jozsa-balanced.e7q
e7q export examples/teleportation.e7q --format openqasm
```
