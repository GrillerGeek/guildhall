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

## Host evidence — 0.12.0

Addresses #36 and #37 finding4. Added read-only preflight, bounded task-owned
Claude transcript and Codex app-server capture inspection, explicit evidence
levels in routing schema3, and alias/configuration/evidence-loss suspension.
The decision record documents the user-approved configuration lane and retains
execution-observed as setup default. No project was activated by this work.

104 tests pass, including mixed/missing responses, wrong-worker/session rejection,
interruption, repeated telemetry, rerouting, alias drift, objective binding and
explicit stronger/weaker qualification. Existing v1/v2 tests remain intact.
Local Codex schemas were generated and inspected without model calls. Running
ChatGPT-owned runtime0.154.0-alpha.6.2 and separately installed Codex.app0.142.0-alpha.1
are distinguished; neither certifies issue #36's different0.155 build. The desktop
collaboration interface does not itself expose the required capture. That route
remains unsupported for this adapter unless task-owned capture access is established.

Ten isolated installation checks passed with both evidence collectors executing
synthetic inputs after source removal. Receipts are retained in the OS temp
installation directories. No personal transcript search, provider probe or live
adaptive qualification occurred. PR #39's four hosted checks passed.

## Qualification studies — 0.13.0

Addresses the remaining #37 findings 1/2. Development analysis uses the complete
candidate matrix, paired repeats, quality checks, measured overhead and a frozen
noise tolerance. It distinguishes insufficient evidence, no measured headroom and
observed headroom; none is automatic qualification. Held-out quality and 10%
improvement requirements remain unchanged, with explicit failure reasons.

The installed controller prepares disposable Git worktrees, persists one-time
claims, imports actual host outcomes, checks file boundaries including ignored
files, supplies actual artifacts for blind grading, freezes grades and detects
subsequent changes. Budgets and immutable manifests carry into holdout. Host
worker dispatch remains explicit; no desktop-to-CLI substitution is performed.
First-time studies use correlated shadow recommendations and explicitly approved
study overrides rather than fabricated qualification. Host permissions, actual
measurement and independent graders remain external responsibilities.

116 tests pass, including 12 study tests with real temporary worktrees and
synthetic worker outcomes. Both validators and generated/whitespace checks pass.
Ten isolated installs pass; installed headroom/controller tools execute after
source removal. Receipts: `guildhall-install-hgsinows/report.json` and
`guildhall-install-e5n7_rkj/report.json`. PR #40's four hosted checks passed.
No live provider call, paid study or real profile qualification was performed.

## All specialist roles — 0.14.0

Addresses #35. Schema v4 permits an explicit adaptive allowlist drawn from all
18 operational roles. Schemas v1/v2/v3 retain their previous behavior and role
limits. The v4 example starts off, with an empty adaptive allowlist, unknown host
evidence and no qualifications. Migration changes the policy hash and therefore
requires renewed activation. No role definitions, native model aliases or hooks
were changed. Model-echo, parent coordination and external IDD remain excluded.

New tests first failed because schema4 was unsupported (55 subtest failures and
18 missing-dispatch errors). Final suite: 121 tests pass. Parameterized checks
exercise all 18 roles across native Claude, standalone Claude and Codex routes,
plus explicit overrides, absent qualifications/permissions/evidence/controls,
wrong scope and unchanged legacy behavior. These are synthetic helper checks,
not proof of host execution or model quality. Role inventory matches the existing
19 native definitions minus model-echo. Fixture seeds cover authoring, build,
review, diagnosis and operations; read-only roles retain stdout-only reporting.

Ten isolated installations passed, including the installed v4 off-mode check;
receipts `guildhall-install-vk9zbsp2/report.json` and
`guildhall-install-3ib0lo4o/report.json` precede a fixture-prompt clarification
preserving read-only contracts. All validators, generated checks and whitespace
checks pass. PR #41's four hosted checks passed, including Python3.12.

## Delivery and decisions

The approved implementation is split into five ordered PRs. Merge in this order,
retargeting dependent bases if required by GitHub after each merge:

| Order | Change | Version | PR |
|---|---|---|---|
| 1 | Installed guide/evaluator, opaque labels, interpreter floor | 0.10.1 | [#38](https://github.com/GrillerGeek/guildhall/pull/38) |
| 2 | Subscription usage and scoped measurements | 0.11.0 | [#39](https://github.com/GrillerGeek/guildhall/pull/39) |
| 3 | Host evidence lanes, capture inspection and drift | 0.12.0 | [#40](https://github.com/GrillerGeek/guildhall/pull/40) |
| 4 | Reproducible study controller and headroom | 0.13.0 | [#41](https://github.com/GrillerGeek/guildhall/pull/41) |
| 5 | All-role eligibility, migration and fixture seeds | 0.14.0 | `codex/routing-all-roles` |

All three installer manifests advance together at every step. The existing
skills1.5.25 pin is retained; 1.7.0 was an explicitly tested candidate, not a
silent dependency upgrade. Canonical portable resources were regenerated into
complete installation bundles. The original checkout and personal installations
were not changed. No changes to IDD were needed for these Guildhall issues.

Decisions made within the approved plan: retain Python3.12; use request-local
opaque labels rather than name filtering; keep subscription tokens separate from
Jev and unknown dollars; use explicit schema revisions instead of reinterpreting
old policy hashes; retain execution-observed as the default while documenting
the approved weaker configuration lane; produce native-host dispatch packets
instead of silently substituting CLI workers; keep first-time study selection
explicit; preserve all role contracts and require scope-specific qualification.

Remaining release/operation work is deliberately outside this implementation:
review and merge the stack, update installations from main, and separately
approve a project-specific live study if desired. This work neither merges nor
publishes a release, activates routing, spends on models or certifies a model.
The current desktop collaboration interface still lacks the task-owned capture
required by this adapter; configuration-based eligibility is not evidence that
this particular desktop worker interface can supply it. Incomplete evidence
continues to prevent qualification. Controller packets cannot enforce OS-level
isolation or kill native workers; actual hosts enforce permissions and budgets.
