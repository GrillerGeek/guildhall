# Collaborative planning verification

Status: corrected backend, isolated browser checks and fresh closing technical
review passed. The [PR draft is ready](../guildhall/plans/2026-10-18-planning-artifacts-issue-64.md#pr-draft). This report does not establish
live-host acceptance, release approval or production readiness.

## Scope and evidence

Issue [64](https://github.com/GrillerGeek/guildhall/issues/64) adds a bounded
planning review bundle, Cassian's explicit review-document mode and optional
local companion/checkpoint helper. The
[Spec](../plans/2026-10-18-collaborative-planning-spec.md) supplies E01–E12,
edge cases and Boundaries. The
[quest plan](../guildhall/plans/2026-10-18-planning-artifacts-issue-64.md)
records explicit user approval and the accepted public API, superseding the
historical draft header. It also records repair/review handoffs and retained
source/test hashes.

The original pinned comparison baseline was `origin/main`
`6bca2ad00db1ebf8a4453264618a51b9f44ff4ff`; the current PR base advanced to
`e13f3d0` during this turn, differing only in the tavern manifest's 0.3 version.
Bruga synchronized those exact incoming bytes; the tavern has no diff against
the current base. That change is upstream synchronization, not feature work.
The review includes source HEAD `087204c` and the complete working tree,
including untracked outputs and uncommitted repairs. Historical planning
and spike commits are part of this PR scope. The orchestration plan was already
dirty at resume; it belongs to Mordain. Independent test additions belong to
Seraphine/Vera, source/generated output to Bruga and the six named documentation
surfaces to Cassian. This report is an explicitly authorized new surface.

Upstream removal of routing setup and Jev integration supersedes historical E12
references to routing resources. They remain absent. Installer-facing manifests
are aligned at 0.19.0. This work does not publish, install globally, change an
external marketplace or certify a released installation.

## Automated and isolated checks

The resumed root baseline ran `python3 -B -m unittest discover -s tests` with
localhost permitted: 85 methods, 37.758 seconds, OK, exit 0. Its default-sandbox
attempt had socket PermissionError failures; those are environment/setup evidence,
not attributable feature RED. This baseline precedes the final cancellation,
provider-error/diagnostic and keyboard/focus repairs.

Independent repair RED evidence was recorded before implementation:

| Regression stage | Observed result |
|---|---|
| Six cancellation/provider/diagnostic cases | Six methods, four assertion failures, zero errors, two passes; 4.764 seconds. |
| Sustained abort timeout | One assertion failure, zero errors; 2.711 seconds. A recovered answer reopened chat while abort remained unresolved. |
| Duplicate cancellation | One assertion failure, zero errors; 2.675 seconds. Two aborts were observed instead of one. |
| Hosted feedback arriving between checkpoint prepare/complete | Two finite-CLI methods, two assertion failures, zero errors; 1.892 seconds. |

The final root run of `python3 -B -m unittest discover -s tests` passed **95
methods in 48.182 seconds**, OK, exit 0. Bruga independently reported 95 methods
in 48.469 seconds, OK. The tests were frozen without weakened assertions; all
four regression stages now pass. Earlier 91/40.093, 92/42.311 and 93/44.229
root runs, like the resumed 85-method baseline, are historical evidence only.

Root's final checks passed: `python3 scripts/build_portable.py --check` reported
33 generated files and zero drift; `python3 scripts/validate_plugin.py` reported
19 agents, zero errors and zero warnings; `python3 scripts/validate_portable.py`
and `git diff --check` passed. Canonical/generated helper copies are equal.

| Frozen output | SHA-256 |
|---|---|
| Canonical/generated `scripts/review.py` | `75bfdcf38f74deb4ead9b9e52ef21d98966cfdd0d1b64a98113793b627e42fc4` |
| Canonical review template | `01961995554159e22cae06f7ccc3f1bbf476661cac72e395c472540e82950977` |
| `tests/test_review_adapters.py` | `5b2e96c042251e810c56186ecd39aed9f1da6b4af4ab8afc2335e757c210eff7` |
| `tests/test_review_contract.py` | `3cf2cd3472a303d1d756cd3a84c526163e34d998539f4e4556435fac3793d770` |
| `tests/fixtures/review/review.spec.cjs` (0644) | `b66a04fb17e56473e894758a432a062faaeba3f90a1fb1e38643193fefe3d9bf` |

Final backend repairs cover terminal provider errors, retained safe send
diagnostics, exact-request cancellation, a durable unacknowledged-cancellation
barrier and duplicate-abort suppression. Keyboard access to conflict comparison
and light-theme focus contrast were repaired. Thalia and Vance returned zero
final findings; Lior confirmed the focus/contrast repair. Oriana found no new
findings while retaining the two disclosed performance concerns below. Tabs'
structural review was clean, root reran validators and Garran's final runbook
agreed with the operational guidance.

The first closing Aldric review was **BLOCKED** on hosted feedback arriving
between checkpoint prepare and complete (E04/E06/E07 and approved API lines
398–399), with no other new blocker. Two independent finite-CLI regressions
observed RED before the corrective implementation. Completion now merges the
fresh validated hosted feedback with current and pending entries before publishing
the common baseline. Differing same-ID entries safely refuse; the 200-entry cap
and provenance checks remain intact. Thalia/Vance's scoped correction reviews
returned zero findings; Oriana found no new concern and retained the same two
performance follow-ups. The subsequent fresh closing review passed after this
corrective cycle; the historical initial BLOCKED result remains recorded above.

Fresh Aldric closing review returned **PASS**, covering all 12 Expectations,
13 edge cases, nine Boundaries, Deliverables and Validation requirements, with
no new blockers. It independently matched 47 frozen path hashes/modes (the
mutable plan excepted) and 27 protected upstream files. The final helper and
three test hashes above were unchanged; the 95-unit/8-browser-test and packaging
evidence remains current. The medium Pi memory and low state-history findings
remain owned by Bruga/Cassia. All four live-host acceptances and optional
screen-reader acceptance remain pending. Rook's PR draft is ready in the linked plan;
closing PASS does not grant release or live-host acceptance.

Vera's isolated Playwright fixture passed **eight browser tests in 4.5 seconds**,
independently repeated by root. After the hosted-feedback correction, root
restarted the fixture with the latest helper and reran all eight tests: **eight
passed in 4.1 seconds**, exit 0. The existing Playwright runner and
`tests/fixtures/review/playwright.config.cjs` were used with the explicit fixture
origin, startup receipt and offline export. The final helper/template hashes above
identify the tested source; the 95-method unit GREEN remains current.

| Browser coverage | Observed behavior |
|---|---|
| E05 | Offline HTML at 1280/390 widths makes no network request; editing, selection, comparison and downloads work, with chat disabled. |
| E06 | Two tabs detect stale saves, retain the draft and allow keyboard scrolling of conflict comparison. |
| E07 | Comments remain proposed, retain provenance and survive reload. |
| E09 | Checkpointing preserves the exact quest-plan hash. |
| E11 | Connection, session identity/unavailable reason, editing and reconnect work in the synthetic fixture. |
| Accessibility | Focus contrast meets 3:1 in both themes. |

Two initial runs had seven passes and one macOS keyboard-cursor setup failure.
Using the harness sequence SelectAll, ArrowLeft, then ShiftArrowRight resolved
that setup issue; assertions were unchanged. A later intermediate replay had
three offline passes and five ERR_CONNECTION_REFUSED setup failures because the
fixture had stopped after its worker turn. Keeping the fixture worker active
resolved setup without source changes; those failures do not establish feature
assertion failures. These setup runs are not attributed feature RED. Browser
evidence is isolated and synthetic,
not any of the four live-host acceptance paths. Fresh closing Aldric review has
passed as recorded above; Rook's PR draft is ready in the linked plan.

Cassian read the current canonical helper/template, collaborative contract,
schema/example, role/host handoffs, approved API and Spec, and matched the existing
README/installation style. Documentation-only `git diff --check` passed for the
five updated existing docs. Cassian did not run models, tests, host sessions or
installation probes and did not commit. The CLI examples describe source-verified
payloads; their execution validation is pending. Root's earlier six-document local
link QA found 31 links and zero missing targets; the `optional-cli` anchor exists.
Final link QA after these report edits remains to be rerun by root.

## Support and acceptance limits

| Surface | Established evidence | Remaining live acceptance |
|---|---|---|
| Claude artifact | Native role allowlist and scoped workflow contract. | Actual writer tool access, rich interactions, feedback retrieval, guarded reconciliation/export and unchanged quest-hook behavior. |
| Codex Space Page | Capability-discovered editable-prose/write-back contract. | Live Page creation/reuse, anchored comments, separate Page-chat write-back, interactive embed and guarded repository checkpoint. |
| OpenCode companion | Synthetic isolated HTTP transport fixtures and historical labeled probe. | Configured real tool-free session, passage chat, prose editing, reconnect, checkpoint and offline export. |
| Pi companion | Synthetic isolated JSONL RPC fixtures and historical labeled probe. | Dedicated real tool-free planning session, exact-session recovery, local interaction and graceful shutdown. |
| Portable documents | Maintained Markdown/HTML, bounded schema/helper and eight passing isolated browser tests, independently rerun by root. | Native account/model behavior is outside these fixtures. |

All four live-host acceptance paths remain pending. Mock responses, source
inspection, installed manifests and package validation do not establish actual
model quality, account access or host enforcement. Worker read restrictions are
role instructions where the host exposes no access-control boundary. Required
input-delivery completeness cannot be certified solely from worker assertions;
the quest plan preserves available evidence and unknown visibility.

## Ownership and operating limits

Mordain writes only the plan. Cassian's review-document mode owns named review
files/records/snapshots and the selected hosted surface with creation permission.
The helper never writes the main plan, accepts proposals or changes IDD readiness.
Actual owner decisions retain sources; AI responses and controls remain proposals.
Seraphine receives only the independent Spec/API/test handoff.

Ordinary/native review paths retain their existing prerequisites. The optional
helper requires POSIX Python 3.12+ (`fcntl`), uses loopback transport and explicit
private runtime storage outside the repository, and starts without a model call.
Runtime credentials/tokens, private bindings, request journals and raw logs do
not belong in portable records. Review documents are limited to 256 KiB UTF-8;
browser saves also fit 264 KiB serialized JSON. Feedback/control requests fit
32 KiB, comments/selections 4,000 characters and substantive lists 200 entries.
Runtime requests also stop at 200; no automated archival command is provided.

One last-common and one pending snapshot preserve reconciliation evidence.
Conflicts require explicit owner resolution; incomplete saves retain observed
success and pending work. Unknown sends require exact-session history inspection,
never blind replay, journal deletion or automatic new-session recovery. For
rollback, stop only owned companion/Pi resources and preserve runtime plus review
bundle. An unrelated OpenCode server remains outside helper shutdown ownership.

Unacknowledged cancellation persists independently of answer delivery. Recovering
an answer or restarting the companion does not clear that barrier: new sends and
rebind remain blocked indefinitely without safe host confirmation. No force-clear,
replay or automatic barrier recovery is provided. Preserve runtime and bundle,
inspect the exact session and use document/comment fallback while blocked.

Two disclosed findings remain follow-up: medium Pi event retention lacks an
aggregate byte budget despite per-event/count limits; low maximum `/state`
response history can approach 50 MiB. No repair or production-readiness claim is
made for either; follow-up owners are Bruga/Cassia. Operational activation remains
explicit opt-in, with no new central service, feature flag, migration or existing
dashboard/SLO.

See [setup and recovery](../installation.md#optional-planning-review-helper) and
the [canonical contract](../../plugin/portable/references/collaborative-planning.md)
for payloads, safeguards and rejection behavior.
