# Routing eligibility and qualification by role

Schema v4 makes every operational Guildhall specialist representable in
`policy.adaptive_roles`. This is permission to evaluate and explicitly enable a
role, not evidence that a model is suitable for it. **No live-qualified profiles
ship.** No role is enabled automatically, and Guildhall still works without Jev
or IDD. Parent coordination, model-echo and external IDD workers are excluded.

| Specialist | Typical study category | Eligible in v4/v5 | Qualified by this package |
|---|---|---|---|
| accessibility-reviewer | review | Yes | No |
| architecture-reviewer | review | Yes | No |
| debug-investigator | debug | Yes | No |
| docs-writer | docs | Yes | No |
| feature-implementer | implementation | Yes | No |
| fog-cartographer | review | Yes | No |
| migration-safety-reviewer | review | Yes | No |
| observability-reviewer | review | Yes | No |
| ops-readiness-reviewer | review | Yes | No |
| performance-reviewer | review | Yes | No |
| plugin-validator | review | Yes | No |
| pr-author | pr | Yes | No |
| prototype-builder | prototype | Yes | No |
| refactorer | refactor | Yes | No |
| reliability-reviewer | review | Yes | No |
| security-reviewer | review | Yes | No |
| test-author | tests | Yes | No |
| ui-test-author | tests | Yes | No |

Categories describe the actual assignment. The examples above are study starting
points; qualification only covers the exact role/category actually evaluated.
A docs result cannot qualify security review, and a review result cannot qualify
implementation. Candidate model and effort, profile/measurement revision, host
configuration, router version, objective, evidence lane and expiry also bind the
qualification. Changes require reevaluation and renewed policy activation.

## New setup and explicit migration

Use the [v5 policy](../resources/examples/off-policy-v5.json) and
[request](../resources/examples/off-request-v5.json) for Dynamic routing. All 18
roles above are representable in `routing_roles`; none are enabled by installing.
Review the selected scope, supported candidates, fallbacks and intentional role
locks. Dynamic uses [catalog/task preferences](task-routing.md), not qualification.
Parent, model-echo and external IDD assignments stay excluded on every host.

Schemas v1–v4 keep their existing behavior. On an explicitly requested v5
migration, copy the policy into a review proposal, retain limits/objective and
supported candidates, and review copying `adaptive_roles` to `routing_roles`.
An empty list is not permission to enable all roles. Add `fallback_candidate`,
`role_baselines` (native Claude roster defaults) and `role_locks` (intentional
user overrides only), reviewed profile/fact provenance and the compiled catalog
hash. Record a fresh control snapshot and obtain new mode/data/scope approval.
Do not silently switch adaptive to dynamic or reuse its approval.

Preserve original study results and qualifications unchanged. Import optional
measurements only when their scope/count/completeness/provenance are known; leave
others empty in the new proposal. Changed profiles invalidate old qualification
hashes. Advanced benchmark-qualified adaptive still needs separately reviewed
role/category/host evidence and an appropriate required_evidence level. A failed
study does not prevent Dynamic routing and does not authorize another study.

## Preserve the job while changing the model

Routing selects supported model/effort arguments only. Every worker still gets
its original role contract, write scope, tools, permitted handoff, fresh context
and retry budget. Test authors remain independent from implementation context;
RED → GREEN → conditional refactor remains sequential. Required independent
reviewers are not removed, combined or replaced. IDD lifecycle gates and ownership
are unchanged. Model choice cannot justify an extra retry or broader file access.

The [synthetic fixture seeds](../resources/examples/role-study-fixtures.json)
cover authoring, implementation, review, diagnostics and operations. Each includes
starter files, an allowed write scope and explicit grading criteria. They are
small construction examples, not a benchmark or qualification set. Materialize
one clean fixture repository per class, replace or extend the seeds with actual
project tasks and prespecify at least three development fixtures plus held-out
fixtures per role/category. Freeze candidate sets and rubrics before running;
never tune on holdout. Test-author studies must derive tests from independently
supplied Specs/API contracts rather than exposing implementation files.
