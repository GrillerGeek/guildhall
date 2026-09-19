# IDD lifecycle bookkeeping

Read this only for an IDD-managed feature. Mordain is the orchestration decision
owner. A fresh **orchestration recorder** performs bounded bookkeeping on his
instructions; it is not an implementing adventurer and makes no lifecycle or
approval decisions. This is a protocol using the host's ordinary tools, not a
new sandbox or a deterministic execution controller.

Before plan creation, Mordain resolves the selected Spec, all required inputs,
its human readiness approval, current clean gap-check and bundled closing Guildhall technical review
capability. Confirm no other runner/controller owns this execution. Confirm a
safe YAML parser and output scopes are available. If required bookkeeping would
cross a Boundary, no safe status-only edit is possible, or ownership conflicts,
refuse before writes. Do not invent permission or bypass an active IDD runner.

The recorder's allowable writes are exactly the selected Spec's `status` scalar
and one new `docs/reviews/<SPEC-ID>-<UTC timestamp>-execution.md`. It cannot change
any content block, review annotation, linked artifact, approval fact, existing
report, code, test or project configuration. Supply exact absolute paths and the
expected current Spec bytes/status on every invocation. It re-reads before each
write and stops on any mismatch. Do not reserialize YAML in a way that rewrites
unrelated bytes, comments or formatting. If a scalar-only replacement is
ambiguous, stop. Use the safe parser before and after and compare all other
fields and original bytes. An interruption never causes an automatic reset.

## Readiness checklist

For the standard IDD Spec schema, check all eleven items below. Resolve inherited
context and linked Expectations from the consuming project's actual artifacts
when needed; do not fill gaps by guessing. Follow any stricter applicable project
contract. These criteria are bundled so an installed skill need not discover an
unrelated personal IDD installation merely to know the checklist.

1. Context has a nonempty stack.
2. Context has nonempty architectural patterns.
3. Context has at least one convention.
4. Context has a nonempty authentication/authorization description (including an
   explicit statement when none is needed).
5. At least one Expectation is linked.
6. Every linked Expectation has validation criteria and corresponding detail.
7. Each Expectation has at least two edge cases.
8. Boundaries has at least one entry.
9. Deliverables has at least one entry.
10. Validation includes at least one automated and one human-review item.
11. Actual recorded human peer-review approval exists; an AI review is not this fact.

Presence alone does not establish quality or substitute for the current clean
gap-check and its reviewed-content evidence.

## Begin, before test-author or implementation writes

1. Mordain verifies all execution prerequisites, including all eleven readiness
   checklist items as applicable, then restates every Boundary verbatim.
2. Dispatch only the recorder. It independently checks the selected Spec is
   `ready`, gate `passed` with zero counts, the matching readable report begins
   `PASS — 0 blockers, 0 warnings` and contains `## Coverage`, the readiness
   approval is actual human evidence, and content remains the reviewed content.
   Malformed/duplicate-key YAML, changed content, missing evidence or unexpected
   status refuses without modification.
3. The recorder repeats each Boundary verbatim with a comprehension paraphrase,
   then changes only `ready` to `in-progress` and reads back the result. Return
   the before/after byte evidence and parsed-field comparison to Mordain.
4. Mordain verifies the transition before creating the plan and dispatching
   test-author. Each writer still gives its own required Boundary acknowledgment.

## Evidence and report assembly

Every executing worker returns self-verification for each applicable Expectation,
edge case, Boundary and Deliverable, including files, checks actually performed,
outcomes and `spec_gaps_encountered`. Unsupported claims stay unverifiable;
blocker-grade gaps stop execution and return to the Spec author. A role's failure
cannot be repaired by changing the Spec during execution.

After collecting worker evidence and independently checking actual artifacts,
Mordain dispatches the recorder in **report-only** mode. It writes only the
new Execution Report, leaving status `in-progress`. Include:

- Spec ID/path, run/host identity and actual lifecycle state;
- per-Expectation and per-edge-case verification with evidence;
- each Boundary and whether/how it was preserved;
- each Deliverable, output path and result;
- every automated check, exact command, exit/outcome and observed counts;
- required human-only checks, honest pending reasons and follow-up;
- `spec_gaps_encountered` (explicitly none when none occurred);
- pre-existing edits, unexpected mutations, interruptions and open blockers.

The recorder assembles supplied evidence; it must not infer a worker's
self-verification or promote an unobserved result to a pass. On failure or
interruption, write a partial report if possible and keep `in-progress`. Resume
only after an explicit recovery decision; standard fresh execution accepts ready.

## Finish, separate from report assembly

Mordain reads the saved report, verifies every required Deliverable and Boundary,
all automated checks and required reviews pass, and no blocker-grade gap remains.
Only checks explicitly designated human review can remain pending at this point,
with their reason and follow-up. Failed/blocked automated or required host checks
cannot be reclassified as human checks.

Only then dispatch the recorder with a distinct **advance-to-review** decision
and unchanged Spec/report evidence. It verifies the expected current
`in-progress` state, applies a status-only transition to `review`, and reads it
back. Mordain checks the result. Never transition directly to `validating` or
`done`: actual human implementation approval and QA/Product Owner validation
remain separate gates.
