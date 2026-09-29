# Practical dynamic routing verification

The four-PR stack implements task-level Jev routing on Codex, native Claude and
standalone Claude. Final package version is 0.17.3. Installation remains off;
users can explicitly approve Dynamic routing without a qualification study.
Advanced adaptive retains its benchmark requirements. No personal settings,
marketplaces or saved study results were changed during this implementation.

## Stack and behavior

1. [PR 47](https://github.com/GrillerGeek/guildhall/pull/47): v5 dynamic contracts,
   reviewed controls, versioned approvals, fallback and router-identity handling.
2. [PR 48](https://github.com/GrillerGeek/guildhall/pull/48): pinned host catalogs,
   controlled task briefs, meaningful choice criteria and privacy boundaries.
3. [PR 49](https://github.com/GrillerGeek/guildhall/pull/49): wizard and all three
   host routes, explicit role locks versus Claude/default fallbacks, migration.
4. `routing/delivery-integrity`: bounded handoffs, study delivery guards and local
   feedback from ordinary work. This branch targets PR 49's branch for review.

Review and merge in order. The first three PRs have passing GitHub validation and
pinned/latest installer checks. The final PR should ship with the feature, while
benchmark qualification remains optional. These intermediate package versions
are a review stack, not a request to publish or install each step personally.

## Delivery and feedback

Required references become bounded identified chunks. Host-visible content is
checked for omissions, changed bytes, explicit/recognized truncation, duplicate
attempts and cumulative read budgets. Recovery appends only missing authorized
chunks without resetting time/attempt counts or replaying a worker. All three
host routes share the checker; instructions specify actual host output controls.

New live studies cannot claim workers without a frozen expected-input manifest.
Invalid prior live delivery stops further claims before spending on later trials.
Incomplete/unknown live inputs are excluded from blind grading; grading refuses
them, and export withholds the whole model comparison rather than cherry-picking
valid-looking outputs. Original outcomes, grades and consumed usage remain.
Legacy live delivery without evidence stays unknown; historical synthetic
arithmetic remains explicitly synthetic.

Ordinary-work feedback reuses existing test/review outcomes, requested/trusted
observed settings and normalized usage. It correlates task, host, policy and
worker scope, keeps cache/reasoning accounting, leaves unknown subscription
allowance/cost unknown, and proposes reviewed catalog updates only. Known forced
substitution suspends choices without replay; unknown served identity does not.
No helper launches models, adds graders, trains or automatically edits policy.

## Validation and limits

Offline suite: 178 tests on Python 3.12 and 3.14, including all-role/all-host
routing, distinct same-role tasks, approval/scope/lock/fallback behavior, installed
wizard operations, privacy, truncation/recovery, invalid study exclusion and
normal-work feedback. Native validator: 19 agents, no errors/warnings. Portable
validator, generated drift checks, skill validation and whitespace checks pass.

Isolated native Codex and Claude installs passed exact bytes/modes and removal of
the source fixture. The pinned skills 1.5.25 installer passed both skills
independently, for Codex and Claude, from explicit bundle paths and repository-root
discovery, with source removal. Installer receipts are local temporary artifacts;
no personal profile or credentials were copied into those fixtures.

Fake providers and supplied synthetic host records establish wiring and failure
handling, not live recommendation quality or savings. No paid workers, Jev calls,
qualification studies or regrading runs were started. Delivery checks validate
supplied host-visible evidence; they cannot authenticate a fabricated source
label or prove comprehension. Hosts lacking visibility report unknown. Codex
catalog setup uses the actual exposed roster; no universal model list is shipped.
