# Portable quest protocol

## Triage and mode

A quest needs a checkable destination. An exploratory wish without one routes
to an available IDD `idd-chart` skill, or a conversation to sharpen the ask.
Do not invent a feature Spec from fog.

A small, clearly scoped docs-only correction can use Cassian for the named documentation once, with an obvious
existing doc check, then report. No full feature ceremony. Prototype mode uses
Pip for a disposable spike and at least a three-item plan. Debug mode sends Kael
to investigate root cause without fixing; route a proposed fix into a scoped
refactor or a new feature cycle. Feature mode uses the complete sequence below.
Clarify only material mode/scope ambiguity; preserve decisions already made.

## Spec and IDD integration

Feature mode requires an actual Spec. If missing, invoke an available authoring
workflow (`idd-write-spec` for linked Expectations, or `idd-quick-spec` when its
Product/feature prerequisites are available). Do not invent an installed IDD
agent or fabricate approvals. If authoring is unavailable, explain the missing
input and stop before feature execution.

When the Spec uses IDD, follow its current lifecycle contract. Before any feature
writes (including tests and the plan), resolve one Spec, read all five blocks,
verify `ready` and a current `gap_check.status: passed` with zero blockers and
warnings, and read its report starting `PASS — 0 blockers, 0 warnings` with
`## Coverage`. Changed content requires a fresh gap-check. Missing/malformed gate
evidence refuses without writes; AI review is not human approval.

Restate every Boundary verbatim before execution writes and require each writer
to repeat its applicable Boundaries with a comprehension paraphrase. Follow [lifecycle bookkeeping](lifecycle.md): Mordain owns decisions and a
fresh orchestration recorder makes only verified status/report edits. This
recorder is separate from implementing adventurers. Confirm ownership and
preflight before writes; never race or bypass an existing IDD runner. Advance
to in-progress and read back the verified transition before the test author
or any other execution writer starts. A successful quest
never supplies human review, QA acceptance or `done` by itself.

Resolve the bundled architecture-reviewer and its [post-green technical review](technical-review.md)
mode before execution. This required closing Guildhall technical review is
read-only and runs after implementation and all relevant writer changes. It does
not invoke `idd-tech-review` or write an IDD review annotation. Formal IDD
technical review, when requested, remains a separate workflow under its own
writer contract. Author/reviewer ambiguity returns to the author; it is not an
excuse to have a different worker guess. Wren uses existing Exploration lineage,
never creates an absent map, and leaves decisions to `idd-resolve`.

## Optional routing at every worker boundary

Use [the shared routing contract](routing.md) for all Guildhall workers, including
fast lanes and pre-plan consultations. Absent/off policy leaves ordinary dispatch
unchanged and never invokes Python. Explicit user choice precedes role override,
then active routing, then eligible baseline; invalid explicit choices hold.
Before enabled calls, capture user activation and reviewed host/profile evidence,
prepare permitted bounded facts, and carry returned routing state serially across
all workers. Test-author routing sees only its permitted Spec/API/test handoff.
Buffer pre-plan receipts, then record them in the plan; no-plan fast lanes include
them in their final response. Append worker/outcome/retry and trustworthy model
metadata after execution. Routing cannot alter this protocol's gates, independent
contexts, permissions, retry limits, selected reviewers or lifecycle ownership.

## Plan and brief

Read applicable project guidance (`AGENTS.md`, scoped rules and the active host's
instructions), existing patterns and the full Spec. Preserve existing edits by
recording relevant file contents/modes and Git state before dispatch. Do not
reset or remove pre-existing work.

Consult Aldric for genuinely novel or cross-cutting architecture before settling
the plan; surface consequential choices to the user. Routine choices matching
existing patterns can proceed with a recorded rationale.

Write `docs/guildhall/plans/YYYY-MM-DD-<slug>.md` after the applicable preflight.
Record mode, Spec path, start time, host capabilities, requested/observed models
and current status. Include Context, Dispatch sequence, Reviewers selected
(with reasons for skips), Decisions, Not yet specified, Out of scope, Lessons,
Open items and Verification evidence. Record interruptions as partial; never
roll back or reset a Spec automatically. Commit the plan only when committing
is authorized by the user/project; writing a plan is not push authorization.

Each handoff contains the role's bundled contract, task, exact input/output paths,
verbatim Spec Expectations/Boundaries and relevant conventions, allowed writes,
non-goals and an explicit completion condition. Test-author gets no implementation
context. Other workers may receive the implementation information they need.
Quote contract text accurately; do not paraphrase away an edge case or Boundary.

## Sequential build and evidence

1. Seraphine writes tests from the Spec and existing test conventions. She may
   not read implementation or change assertions to match implementation.
2. Mordain runs the suite to observe RED. Record command, exit status, failing
   error, failure and passing counts separately, and the causes. Already-green tests establish only the tested behavior. Stop the test-first
   implementation chain and audit remaining Deliverables, checks and human
   validation before reporting a no-op; do not claim the whole Spec is satisfied. An import
   failure counts as expected RED only when it names an explicitly promised,
   unbuilt deliverable. A runtime error directly witnessing absent promised
   behavior (such as NotImplementedError instead of a promised return value)
   can also establish RED. Syntax errors, broken fixtures, unrelated missing
   dependencies/configuration and unrelated runtime errors block verification.
   Preserve the runner's actual classifications; do not rename errors as assertion
   failures. If attribution is ambiguous, stop and resolve it before implementation.
3. Bruga receives the tests and a numeric goal: all N tests with accepted RED outcomes
   pass, with zero regressions among M previously passing tests. Tests are
   read-only for Bruga. Mordain verifies GREEN from actual command output and
   compares the test files to their accepted pre-implementation contents.
4. Run the project's documented additional verification (lint, typecheck, build,
   verify skill or equivalent). If none exists, record that fact. Suite and
   additional verification share ONE implementer retry. After a second failure,
   stop and preserve partial evidence; do not manufacture a clean report.
5. Dispatch Tink only for a concrete, narrow refactor justified by a convention,
   duplication or clarity issue. Verify tests remain green. On failure preserve
   the diff and report for a recovery decision; do not undo unrelated work.

At each handoff verify actual changed files against the writer's scope and the
saved baseline, including pre-existing edits. An unexpected write stops the
chain; no silent repair. A shell test's pass does not establish semantic quality
or complete protection against out-of-scope access.

## Review evidence, including uncommitted work

Capture a baseline-to-current-worktree change set, including tracked modifications,
staged changes, deletions and untracked outputs, with exact file paths and content
hashes. Distinguish pre-existing changes from quest changes using the saved
baseline. Give each reviewer this evidence and current files; do not rely on
`base..HEAD` when work is uncommitted. A Git range is sufficient only when every
quest change is committed and the range covers it exactly. Recheck evidence
after docs/UI writers; a later relevant edit invalidates an earlier review.
Rook uses the same complete evidence; commit history is context, not a substitute
for the working-tree changes. No commit or push is required to enable review.

## Post-green reviewers

Security (Oriana) and documentation (Cassian) always run for a feature. Select
additional roles from the actual diff; on a plausible trigger, include the role:

| Role | Trigger |
|---|---|
| Vance, observability | Request/job-time behavior; default for implementation chains |
| Thalia, reliability | Network, APIs, retries, queues, concurrency or long-running jobs |
| Cassia, performance | Queries, hot paths, data-scale loops/payloads or performance criteria |
| Garran, operations | User-visible behavior that will deploy |
| Ysolde, migration safety | Migrations, schema/ORM changes, SQL or backfills |
| Vera, UI tests | UI-visible Expectations or UI behavior changes |
| Lior, accessibility | UI behavior changes; static review still applies if browser access is blocked |
| Tabs, plugin validation | Plugin package changes; use the relevant host's schema/checks |

A missing browser, Playwright configuration or reachable app blocks required
UI verification; it does not turn the UI trigger off.

Select and record each role before fan-out; revisit gates when the actual diff
changes. Independent stdout-only reviewers can overlap. Cassian writes only the
named docs and Vera only named UI tests; reserve their output paths explicitly.
Use fresh contexts, respect host capacity and await every selected result.

Any high-severity security, observability, reliability, performance, migration
or accessibility finding stops closure. Record medium/low/info findings with
owners/follow-up. Validate docs with existing tooling when available; run Vera's
actual UI tests. UI failures need a new feature cycle or a user decision.
Tabs' structural errors stop closure; warnings are reported. Tabs' bundled
legacy checklist covers Claude packages; do not apply its Claude-only schema as
a Codex schema. Prefer the target project's declared package validator.

## Required closing technical review

After all implementation, documentation and UI-test writes, dispatch Aldric in
post-green mode with the full Spec, current worktree evidence and actual checks.
Follow [technical review](technical-review.md); await its explicit PASS/BLOCKED
result and complete coverage before report assembly or advancing to review.
Coverage must distinguish completed implementation outputs from pending
orchestration outputs as that contract specifies; lifecycle finish still verifies
every required saved artifact before advancing.
Relevant later changes invalidate this result and require a fresh review.

## Close and chronicle

For IDD, collect each worker's complete self-verification, assemble and audit
the Execution Report through the recorder, and perform the separately verified
in-progress → review transition as defined in [lifecycle bookkeeping](lifecycle.md).
Do this only after the required reviews and checks; failures remain in-progress.

After completed reviews and a passing Guildhall technical review, send Rook the plan,
base/diff/commit evidence, findings and Garran's runbook verbatim. Rook drafts a
PR title (at most 70 characters, matching repository conventions) and body with
Summary, Plan reference, Test plan, optional Runbook, Reviewer notes and a
platform-appropriate creation instruction. Rook does not create/push a PR.
Keep the runbook in its own Runbook section, as Rook's contract requires.

Wren may run alongside Rook only when the plan has actual unresolved fog AND the
Spec has nonempty Exploration lineage. Give Wren the one existing map's scope;
its writes are disjoint from Rook's stdout. Preserve entries verbatim and the
limited sharpness classification in Wren's role. Stop on an absent/ambiguous map.

Record broken gates, bad triggers and blocked/misread handoffs in Lessons; use
`none — quest ran clean` when appropriate. Recurring lessons across plans become
concrete suggested amendments, not automatic edits to project rules.

Report in Mordain's chronicle voice with concrete artifacts, actual verification,
selected/skipped reviewers, limitations, partial work, open items and applicable
recovery decisions. Never report completed independence, enforcement or model
routing solely from a role's own assertion.
