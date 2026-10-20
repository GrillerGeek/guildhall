# Guildhall quest plans

Mordain writes one plan file per quest here, following the template documented in `plugin/commands/quest.md` Step 3. Each file is named `YYYY-MM-DD-<slug>.md` and is committed to the repo as the canonical record of that quest.

## Optional review workspace

Substantial planning can add a sibling bundle and one stable hosted review
surface where callable tools support it:

```text
YYYY-MM-DD-slug.md
YYYY-MM-DD-slug/
  review.md
  review.html
  review-state.json
  snapshots/
    common.md
    pending.md
```

The plan links to portable review prose, standalone HTML and the observed hosted
URL when available. The snapshot filenames are alternating slots; the record
identifies which is last-common and which is pending. Do not infer their roles
from filenames or add arbitrary files to a helper-owned bundle. Helpers refuse
unexpected files/symlinks before mutation and never delete user-created content.

Mordain still edits only the plan. Cassian owns explicitly named review outputs
in review-document mode, with creation permission. The helper supplies maintained
scaffolding and bounded persistence; native supported file/host tools can save
the same record without Python. Python 3.12+ on POSIX is required only when
choosing the optional helper/local companion. Runtime processes, machine paths,
tokens, request journals, private session bindings and raw logs stay outside the
repository and durable bundle.

Use one private-by-default surface per quest or the supplied writable destination.
Resume the recorded identity; lost access, deletion or an uncertain creation
requires an explicit recovery choice before replacement. Retrieve all available
comments and substantive Page-chat write-back; report partial coverage and
detached anchors honestly. Unknown authors/revisions remain null.

Reconcile on save/proceed, handoff, resume and closure. Read-only inspection
does not advance a baseline. Disjoint changes can merge; conflicts retain local,
hosted and last-common versions for owner resolution. Complete only observed
saves, retaining pending state when either side fails. `clean` describes
synchronization, never acceptance. Decisions retain their source and rationale;
only the project-designated owner, otherwise initiating user, supplies acceptance.
Model replies, selections and controls are proposals. IDD changes return to the
project's actual authoring/review flow and cannot be accepted by browser controls.

Review prose is bounded at 256 KiB UTF-8, feedback/decision lists at 200 entries
each and comments/selections at 4,000 characters. Preserve overflow material for
explicit splitting/archival rather than truncation. Standalone `review.html`
opens offline with local editing, comparison and downloads; agent chat and
checkpoint synchronization remain unavailable. Unsaved browser drafts require
download. Regenerate the HTML with a fresh review hash after saved prose changes.

For setup, serialized request limits, exact-session delivery recovery and export,
see [installation](../../installation.md#optional-planning-review-helper) and the
[canonical contract](../../../plugin/portable/references/collaborative-planning.md).
The [verification report](../../reviews/2026-10-19-collaborative-planning-verification.md)
distinguishes local fixtures from pending live-host acceptance.
