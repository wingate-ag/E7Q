# Milestone 6 — Channel Equivalence

E7Q v0.6 compares the complete linear maps induced by compatible
density-matrix programs before their terminal measurement.

```bash
e7q compare noisy-a.e7q noisy-b.e7q \
  --criterion channel-tolerance \
  --proof channel-equivalence.proof.json
```

The supported criteria are:

- `channel-exact`: element-for-element superoperator equality;
- `channel-tolerance`: superoperator equality within the declared tolerance;
- `channel-measurement`: equality of computational-basis measurement
  behaviour while permitting unobserved density-matrix differences.

The comparison applies each program to a complete matrix-unit basis. Its
Proof-of-Path identifies the representation as `superoperator`, records the
maximum error, and states the equivalence threshold.

Both programs must use the density-matrix backend, have the same number of
qubits, and end in full-register measurement. Mid-circuit measurement,
classical control, and assertions remain outside this equivalence profile.
This is mathematical equivalence under the declared reference channels; it
does not establish equivalence on physical hardware.
