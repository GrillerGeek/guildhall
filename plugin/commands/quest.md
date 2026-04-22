---
description: Dispatch the Guildhall orchestrator to handle a coding quest end-to-end
argument-hint: <task description>
allowed-tools: Task
---

A new quest has arrived at the Guildhall:

$ARGUMENTS

Dispatch the `orchestrator` agent to handle it. Use the `Task` tool with `subagent_type: orchestrator` and pass the task description above as the prompt.

The orchestrator will:

1. Pick the mode — **prototype** (fast spike, disposable), **feature** (TDD-ordered chain: test-author → feature-implementer → refactorer), or **debug** (debug-investigator first, then route).
2. Produce an implementation plan before dispatching workers.
3. Dispatch the right worker(s) in the right order. Workers are sequential by design — TDD red-green-refactor requires it.
4. Verify handoffs by running the test suite between each worker.
5. Report back what was done.

If the mode is ambiguous from the quest description, the orchestrator will ask one clarifying question before proceeding. If the task requires a genuinely novel architectural decision, the orchestrator will pause and surface the design choice before dispatching workers.

When the orchestrator completes, relay its report back to the user. Do not attempt to coordinate the workers yourself — that is the orchestrator's job.
