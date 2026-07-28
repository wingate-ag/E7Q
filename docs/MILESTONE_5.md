# Milestone 5 — Noise and Backend Boundary

E7Q v0.5 introduces mixed-state execution through a density-matrix reference
backend. Programs may declare bit-flip, phase-flip, and depolarizing channels.

```text
context NoisyBell {
    backend: densitymatrix
    shots: 4096
}

noise bit_flip(0.10) q[1]
```

Proof-of-Path keeps unitary transformations, quantum channels, and measurement
projections distinct. Each density-matrix step records trace and purity; final
verification reports the number of declared channels.

`e7q capabilities program.e7q` emits the execution capabilities required by a
program. The profile explicitly says that the built-in backend is a reference
simulator and does not imply physical-hardware fidelity.

This milestone does not yet map circuits to a vendor topology or claim a device
noise model. Vendor IR adapters, physical compilation traces, and non-unitary
channel equivalence remain future work.
