# Dynamic routing contracts

Schema v5 introduces explicitly approved `dynamic` routing without benchmark
qualification. The policy pins roles, candidates, catalog revision and outbound
contract. Activation v2 binds the source and policy to a separate reviewed worker
control snapshot. Unknown execution telemetry does not prevent dynamic use.
Legacy schemas and approval records keep their original meaning; `adaptive`
still requires independently qualified profiles. A v5 policy needs new approval.

The router filters unsupported controls, validates the fallback before any call,
preserves user/role locks and budgets, and suspends on observed router identity
drift within the quest. Preflight reports dynamic prerequisites separately from
capture/study prerequisites. No credentials, personal settings or paid probes were
used. Control snapshots are host-supplied facts, not independent execution proof.

Validation: 207 offline unit tests passed on the current Python interpreter;
native validation checked 19 agents with zero errors/warnings; generated bundle,
schema and manifest checks passed. Follow-up PRs supply meaningful catalogs and
briefs, the user-facing setup flow, and input-delivery checks before release.
