# Routing eligibility and qualification by role

Schema v4 makes every operational Guildhall specialist representable in
`policy.adaptive_roles`. This is permission to evaluate and explicitly enable a
role, not evidence that a model is suitable for it. **No live-qualified profiles
ship.** No role is enabled automatically, and Guildhall still works without Jev
or IDD. Parent coordination, model-echo and external IDD workers are excluded.

| Specialist | Typical study category | Eligible in v4 | Qualified by this package |
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

## Prepare a new policy

Use the [v4 off policy](../resources/examples/off-policy-v4.json) or
[complete off request](../resources/examples/off-request-v4.json). They keep
`mode: off`, `adaptive_roles: []`, unknown evidence and null qualifications.
Replace placeholder profiles with real settings discovered through the actual
host; do not invent a cross-provider tier mapping. The policy starts with the
strong `execution_observed` evidence requirement. Choosing the weaker
`configuration_verified` lane is an explicit setup decision with its own evidence
and study requirements; see [host evidence](host-evidence.md).

A useful setup request is:

> Prepare routing schema v4 for this project in off mode. Identify the actual
> host and supported settings, keep qualifications null, and propose one role
> and task category for a bounded study. Preserve that role's full contract.
> Show candidate scope, budgets and evidence limitations before any paid calls.

Review development headroom and held-out quality/efficiency evidence through the
[study workflow](qualification-study.md). Add only independently qualified roles
to `adaptive_roles`, retain narrowly scoped candidate qualifications and explicitly
approve the new policy hash. An API key, successful schema validation or synthetic
test result grants no activation or qualification.

## Migrate an existing policy deliberately

Schemas v1/v2/v3 remain readable with their existing behavior. Their adaptive
allowlists still support docs-writer and pr-author only. The new schema is opt-in:

1. Copy the policy for review and set both request and policy `schema_version`
   to 4. Leave `mode: off` while preparing it. Keep the previous role allowlist;
   do not fill it with every eligible role.
2. From v1, move global quality/latency/cost/usage estimates into explicit
   role/category `measurements` entries, including measurement provenance in
   `basis`. Set the four old global fields to null. Unknown scope stays unknown;
   do not duplicate docs measurements across other roles.
3. From v1/v2, select `required_evidence` and supply the actual
   `host.evidence_level`. New qualification records need an objective, evidence
   level and separately observed model/effort values; missing observation stays
   null. Never relabel legacy `verified` as a stronger guarantee.
4. Revalidate against the [v4 policy schema](../resources/schemas/policy-v4.schema.json)
   and [v4 request schema](../resources/schemas/request-v4.schema.json). Review or
   renew qualification when its bound facts change. A schema change alone does
   not establish fresh measurement evidence or require fabricating it.
5. Review the final policy hash and explicitly reactivate. Changing either the
   schema version or allowlist invalidates previous activation. Adding a role
   without its qualified profiles still falls back to an eligible baseline.

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
