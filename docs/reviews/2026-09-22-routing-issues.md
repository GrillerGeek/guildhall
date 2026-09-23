# Routing issue implementation record

The user approved the five-PR plan on September 22. This is repository maintenance,
not an IDD lifecycle transition or a claim of live model qualification.

## Installed tooling — 0.10.1

Addresses #37 findings 3, 5 and 6. Full guide and evaluator are canonical bundled
resources; the root evaluator API remains compatible. Transport uses local opaque
labels instead of policy candidate names. Unsupported Python returns a hold
without requests and preserves independently valid incoming state.

New regression witnesses initially produced three assertion failures in four
cases. Final suite: 81 passing tests. Existing provider fixtures changed only for
the intentional label protocol; dispatch, gate and privacy assertions remain.
Native/portable validators and generated drift/whitespace checks passed.

Ten isolated installation cases passed (native Claude/Codex, pinned skills1.5.25
and candidate1.7.0). Probes now execute the installed helper/evaluator and check
installed guide links after source removal. Local receipts:
`guildhall-install-ny7wrjbr/report.json` and `guildhall-install-dqtsany0/report.json`
in the OS temporary directory. The former precedes a plugin README version-text
correction; implementation and bundled tools are identical. The actual system
Python3.9 helper returned unsupported_runtime with exit2 and no provider call.
GitHub CI supplies the minimum Python3.12 lane; local tests used Python3.14.

No live Jev calls, personal installation or qualification was performed. Remaining
#37 components and issues #34–#36 are addressed by the following planned PRs.

## Subscription usage — 0.11.0

Addresses #34. The bundled normalizer separates host/router meters, deduplicates
response/cumulative updates, rejects conflicts/resets, counts retries and leaves
incomplete totals/cost unknown. Routing schema2 binds measurements to role/category;
v1 remains unchanged. Migration is explicit and invalidates old qualifications.

Eight normalizer witnesses initially failed on the missing module; the scoped
contract witness rejected unsupported v2 before implementation. Final suite:
93 tests pass. Native/portable validation, build/whitespace checks and ten isolated
installations pass. Installed probes execute the normalizer after source removal.
Receipts: `guildhall-install-5cvv_j4o/report.json` (native+pinned) and
`guildhall-install-s0r7n7dj/report.json` (skills1.7.0). Synthetic usage example gives
120 host tokens, null monetary cost and unknown router usage. No quota conversion
or real savings is claimed. PR #38's four GitHub checks passed, including Python3.12.
