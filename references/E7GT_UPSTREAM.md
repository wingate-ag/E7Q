# E7G-T upstream relationship

E7Q is a downstream experimental application of the E7G-T Unified
Geometry-Thinking Kernel. The upstream kernel contributes a disciplined
vocabulary for configuration, possibility families, transformations, paths,
structured objects, processes, projections, results, contexts, invariants,
operational equivalence, Proof-of-Path, and temporal geometry.

E7Q pins the following upstream reference for this release candidate:

- **Version:** E7G-T v0.11-UC4
- **Title:** *E7G-T Unified Geometry-Thinking Kernel — Extensional–Projective–Phase Geometry of Configurations and Time*
- **Immutable source:** [kernel at commit `1ff8fb95958b3ada1b25b380ecf5f6cd7b59fad4`](https://github.com/wingate-ag/E7G-T/blob/1ff8fb95958b3ada1b25b380ecf5f6cd7b59fad4/E7G-T_Kernel_v0.11_UC4_Unified_Public_Reference_Specification.md)
- **Git blob:** `d97225feb8a79b6a90cdf073ec215cdd07992ef7`
- **Compatibility review:** 2026-08-05

E7Q operationalizes a bounded subset of the upstream temporal architecture:
temporal carriers, declared order, temporal projection, preservation and loss,
inquiry-relative temporal phase, and boundary-crossing evidence. It does not
copy the complete upstream kernel.

UC2 preserves the UC1 normative core and adds an informative observational-
claim pilot module. E7Q exposes that module only through the opt-in
`e7q.observational-claim-pilot/v1alpha1` profile. Omission of the pilot does not
make an E7Q artifact non-conforming. The pilot distinguishes observer-indexed
records, bounded observational claims, interpretations, shared divergence and
unknowns, and any declared temporal-extension bridge.

UC3 preserves the normative core and the UC2 pilot, and adds a separate
informative temporal-orientation module. E7Q exposes it only through the
opt-in `e7q.temporal-orientation-pilot/v1alpha1` profile. The pilot declares
observer locality and directional relation kinds, separates reverse
representation from time-reversal symmetry and causal reversal, distinguishes
history-whole membership from simultaneity, and treats compatible-history
relevance narrowing as epistemic unless a stronger bridge is supplied.

The UC3 profile is independent of E7Q's computational-basis measurement update.
It does not reinterpret quantum state update as observer-relative history
relevance, retrocausation, time neutrality, or ontological collapse.

UC4 retains the UC3 temporal-orientation module, including Candidate Law T0:
temporal extension, admitted order, representational orientation, and
directional meaning are distinct modelling ingredients. E7Q already reflects
this separation by emitting temporal evidence independently while the
orientation pilot remains explicitly opt-in; a temporal carrier or ordered
artifact does not by itself select an orientation.

UC4 additionally introduces an informative topological-overlay pilot. E7Q does
not invoke that pilot merely by using its established `topology` option or JSON
field. In those legacy E7Q interfaces, `topology` means an undirected quantum
hardware coupling graph used for adjacency and SWAP routing. It is not a
declared mathematical topological space `(X, tau)`, and graph adjacency,
routing paths, and routing boundaries are not asserted to be topological
neighbourhoods, topological paths, or topological boundaries. A future E7Q use
of the UC4 overlay would require an explicit carrier, topology, construction,
and inquiry-relevant topological claim.

E7Q does not infer quantum physics from that vocabulary. Executable meaning
comes from established quantum theory: Hilbert spaces, tensor products,
unitary operators, channels where supported, the Born rule, classical control,
and declared backend constraints.

This repository must not silently fork or rewrite the upstream kernel. A future
upstream pin requires an explicit compatibility review and release note.
