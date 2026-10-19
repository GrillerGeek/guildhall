# Bounded input delivery

A correct source file and its hash do not prove that a worker received the whole
file. Treat delivery as a separate fact from model identity and output quality.
Use this procedure for required role/reference material on every host. It does
not authorize another worker, extra retries or a paid grader.

## Freeze and read bounded material

1. Inventory only the role contract and references authorized by the handoff.
   Identify required sections with stable material IDs. Test-author inventory
   comes only from its Spec/API/test handoff, never implementation context.
   Preserve the source revision and permitted read scope. Do not load unrelated
   documents just to create an inventory.
2. The optional local helper `scripts/input_delivery.py` accepts JSON stdin
   operations `plan`, `emit` and `assess`. It is a standalone standard-library
   Python utility, not a model-selection or dispatch prerequisite. Plan takes
   `materials: [{id, text}]`, `max_read_attempts` and `max_read_ms`; derive these
   limits from the task's remaining authorized budget, not a new retry allowance.
   It returns chunk IDs, byte lengths and SHA256 values. Store a large manifest
   in task-owned temporary storage; do not print it through an undersized tool
   output. The helper reads no files and launches no models. Without the helper,
   apply the same bounded-read and visible-completeness safeguards directly.
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

Repair required missing inputs within scope or report the input-delivery failure.
Unknown completeness must be reported as unknown; it is not proof of complete
delivery. Existing tests/reviews still determine the work's outcome. Keep
delivery evidence in the permitted quest plan (or final fast-lane report).
