# Bounded input delivery and ordinary-work feedback

A correct source file and its hash do not prove that a worker received the whole
file. Treat delivery as a separate fact from model identity and output quality.
Use this procedure for required role/reference material on all three hosts and
for optional study inputs. It does not authorize another worker or paid grader.

## Freeze and read bounded material

1. Inventory only the role contract and references authorized by the handoff.
   Identify required sections with stable material IDs. Test-author inventory
   comes only from its Spec/API/test handoff, never implementation context.
   Preserve the source revision and permitted read scope. Do not load unrelated
   documents just to create an inventory.
2. `scripts/routing_delivery.py` accepts JSON stdin operations `plan`, `emit` and
   `assess`. Plan takes `materials: [{id, text}]`, `max_read_attempts` and
   `max_read_ms`; derive these limits from the task's remaining authorized budget,
   not a new retry allowance. It returns chunk IDs, byte lengths and SHA256 values.
   Store a large manifest in task-owned temporary storage; do not print it through
   an undersized tool output. The helper reads no files and launches no models.
3. Emit takes the same authorized `materials` and one `chunk_id`. It returns only
   that identified chunk: at most 512 Unicode characters / 2048 UTF-8 bytes. Read
   one chunk at a time with enough actual tool output budget, including the JSON
   wrapper. A prose request for a larger output limit does not set the limit.
4. On Codex, set the actual shell tool's `max_output_tokens` and the orchestration
   tool's own output cap. When functions.exec is present, use a literal first-line
   pragma, e.g. `// @exec: {"max_output_tokens": 3000}`, plus the nested command's
   `max_output_tokens: 3000` for a single chunk. Do not combine a whole reference
   bundle into that one capped call. On Claude native/skill routes, use the actual
   Read offset/limit or bounded shell output supported by that worker tool; names
   and controls vary, so do not copy Codex parameters into Claude.
5. Inspect the visible result for omissions, truncation markers and the complete
   identified content. Source-side hashes alone and a worker saying “read it all”
   are insufficient. If trusted host output is unavailable, record `unknown`.
   Do not relabel source-file bytes as the observed tool output.

## Assess, recover and preserve limits

Assess takes `packet: {schema_version: 1, host, worker_id, manifest, observations}`.
Each observation has `chunk_id`, zero-based `attempt`, the actual visible `text`,
`truncated` (boolean or null), `source` (`host_tool_output`, `worker_assertion`,
`unavailable`), local evidence reference (or null), and `elapsed_ms` (or null).
Use `host_tool_output` only for host-visible evidence you actually inspected.
These are supplied records: the helper cannot authenticate a fabricated source
label or prove worker comprehension. Inspect the underlying evidence honestly.

The helper checks visible content/length/hash, duplicate attempts, truncation
flags/markers, omissions and cumulative read budgets. It returns complete,
incomplete, unknown or budget_exceeded, missing IDs and the recoverable subset.
Append only missing chunk reads within the remaining budget; retain all earlier
attempts. Unknown timing does not authorize budgeted recovery. A complete later
read can repair a truncated chunk, but does not erase consumed attempts/time.
A duplicate attempt is invalid input. Never automatically restart the worker.

For ordinary work, repair required missing inputs within scope or report the
input-delivery failure. Unknown completeness must be reported as unknown; it
is not proof of complete delivery, and does not itself reinstate a study gate
for Dynamic routing. Existing tests/review still determine the work's outcome.
Keep these receipts in the permitted quest plan (or final fast-lane report).

## Optional study integration

New study state uses version 2; existing manifests/state remain readable and
original outcomes/grades stay unchanged. New live trials cannot be claimed without a frozen delivery manifest, and an
invalid prior live trial stops further claims before more model usage. Before claiming a trial, freeze the
expected manifest with `study_runner.py delivery_plan --directory … --run …
--input manifest.json`. All trials for one fixture must use the same manifest.
After actual reads, append the cumulative assess packet with the `delivery`
operation. It must match that manifest, host and worker; earlier observations
cannot be removed. Record the ordinary outcome and actual consumption normally.

`blind` excludes incomplete/unknown live delivery before paying for grading.
`grade` refuses those trials. `export` returns `invalid_input_delivery` and no
comparison dataset if any trial is invalid, even if an old grade exists; it does
not cherry-pick a favorable subset or manufacture quality failures. Missing
legacy live delivery is unknown. Historical synthetic fixtures keep explicitly
synthetic arithmetic compatibility; this is not live delivery evidence.
Keep prior exported reports unchanged and annotate their limits separately.
No new study or regrading run is required for ordinary Dynamic activation.

## Feedback from work already performed

`scripts/routing_feedback.py` accepts the v5 request, its decision, a worker
outcome, observation and optional existing usage packet. Outcome fields are
worker_id, status (completed/failed/interrupted), tests
(passed/failed/unknown/not_applicable), review
(accepted/rejected/unknown/not_applicable), retries, local evidence references
and delivery status. Observation fields are source
(host_metadata/worker_assertion/unknown), evidence, requested_resolved and
observed model/effort pairs (nullable), and configuration_supported (nullable).

Reuse trusted host metadata, actual tests/reviews/retries and complete usage from
that work. Compare resolved identities only when known; requested aliases are not
served names. Worker assertions never become observed identity. Known forced
substitution/unsupported configuration suspends future choices without resetting
counters or replaying work. Unknown identity alone does not suspend Dynamic mode.

Optional usage input uses the existing routing_usage schema, correlated to this
worker and host/role/category. Cache/reasoning semantics and incomplete counts
remain intact. Raw tokens are a subscription proxy; account-wide percentages do
not establish per-task allowance or monetary cost. The result leaves subscription
allowance percent null, requests zero extra runs and proposes catalog review only.
It never trains, mutates a policy/catalog, gives qualification or writes files.
Do not schedule duplicate runs, independent grading or extra retries for feedback.
