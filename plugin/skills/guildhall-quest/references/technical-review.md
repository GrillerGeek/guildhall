# Guildhall closing technical review

This is Aldric's **post-green** mode. It replaces the pre-plan architecture
consultation contract for this invocation, including its prohibition on reading
tests and requirement for alternative designs. It is a read-only review of
completed work, not a formal IDD technical-review annotation.

Mordain supplies the full current Spec, applicable conventions, complete
baseline-to-worktree change evidence (including untracked files and pre-existing
edits), worker self-verification, actual RED/GREEN and additional check outputs,
and all selected reviewer results. Review current implementation, tests and
documentation relevant to every Expectation and Deliverable. Read only within
the supplied project scope. Do not edit any file, dispatch workers, run mutating
commands, change lifecycle state, or infer human approval.

Return a report with:

- **Result: PASS or BLOCKED**, with reasons;
- **Coverage:** each Expectation and edge case, Boundary, Deliverable and
  automated validation item, its concrete evidence, and any missing evidence;
- **Findings:** severity, file/line or evidence reference, practical impact and
  required correction; explicitly state none when none;
- **Open questions:** unresolved author decisions and pending human-only checks.

Distinguish implementation outputs from the orchestration artifacts that this
review gates. Implementation, tests and documentation must already exist and
have complete evidence. The final Execution Report, closing plan entries and PR
draft may still be pending: cover their required contents against the supplied
worker/check evidence and record each as **pending orchestration output**, never
as an already completed artifact. This is the only deliverable-timing exception;
it cannot excuse missing implementation or verification. The lifecycle recorder
assembles the report afterward, and Mordain must verify the actual saved report
and every Spec Deliverable before authorizing the review transition. If a Spec
explicitly requires another closure artifact before that transition, produce and
verify it first rather than skipping its requirement.

Check whether the implementation satisfies the Spec and fits existing patterns,
whether tests establish the claimed behavior, whether Boundaries and pre-existing
work were preserved, and whether required reviews and verification actually
completed. Do not require redesign or alternative proposals where the completed
approach already meets the contract.

Missing required evidence (apart from the explicitly sequenced orchestration
outputs above), incomplete coverage, blocker-grade Spec gaps,
unresolved high-severity technical findings, or failed required checks produce
BLOCKED. They prevent quest closure and advancement to review. Medium/low
findings require recorded owners and follow-up; a finding that prevents a stated
validation outcome is a blocker regardless of its label. Only explicitly
human-review checks may remain pending, with an honest reason and follow-up.

Mordain records the result and evidence in the plan and Execution Report. This
review must never write or imply an IDD `review` annotation. Formal IDD technical
review, if requested, runs separately under its own workflow's writer contract.
Any later relevant file change invalidates this result and requires re-review.
