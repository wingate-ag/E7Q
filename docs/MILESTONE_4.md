# Milestone 4 — Composition and Diagnostics

E7Q v0.4 adds reusable paths, runtime assertions, first-failure diagnostics,
and import of the OpenQASM 3 subset emitted by E7Q.

`use Prepare` expands a declared path into the verified path. Recursive or
unknown path references are rejected during parsing.

`assert c[0] == 1` evaluates after classical information exists. Verification
reports the assertion's Proof-of-Path step, failed-shot count, and earliest
failure. This is an operational diagnostic: it identifies where a declared
expectation first fails, not why physical hardware behaved in a particular way.

`from_openqasm` imports E7Q's supported gate, measurement, classical-control,
and assertion-comment subset. Round-trip tests require deterministic behavior
to survive `E7Q → OpenQASM → E7Q`.
