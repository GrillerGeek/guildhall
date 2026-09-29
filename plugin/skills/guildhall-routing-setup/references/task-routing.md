# Task-level routing inputs (schema v5)

Dynamic routing is approved selection, not benchmark-proven improvement. Use
`routing_catalog.py` to compile a reviewed catalog and actual host controls on
JSON stdin: `{"catalog": <catalog-v1>, "host": <request-v5 host>}`. It returns
supported candidates, excluded IDs and their `catalog_revision`; it does not
write files, activate routing or call models. Set the policy's candidates and
revision to this snapshot. Changes require a new policy preview and approval.

## Catalogs and provenance

The [catalog schema](../resources/schemas/catalog-v1.schema.json) uses complete
host-scoped candidate records. Start with the matching resource:
[Codex](../resources/catalogs/codex-skill.json),
[native Claude](../resources/catalogs/claude-native.json), or
[standalone Claude](../resources/catalogs/claude-skill.json).
Codex's starter is deliberately empty: populate exact model/effort pairs and
permitted values from the currently callable worker tool and current host metadata.
Do not copy the setup author's personal model roster into another installation.
No paid discovery or another installed CLI is necessary or authoritative.

Claude's aliases are descriptive starting points. Their routine/extended/intensive
and efficiency descriptors are qualitative priors based on the official
[model configuration documentation](https://code.claude.com/docs/en/model-config),
reviewed 2026-09-27. Verify actual supported aliases, forced settings and provider
mappings on this host. These descriptions are not measured cost, capacity or
quality. Context and capabilities remain unknown until supported by host metadata
or documentation. Native frontmatter defaults stay unchanged. Standalone Claude
must discover its own tool controls. Keep Fable excluded.

Each `routing_profile` has controlled work types, reasoning depth, complexity,
risk and efficiency preferences plus local source/revision. Use `documented`
only when the linked source supports the description; use `user_preference` for
reviewed judgments. No universal model ranking ships. Ask for the missing preference
when metadata gives no meaningful distinction; do not label all profiles the same
and promise useful routing. Presets do not authorize any models or roles.

`facts_source` records where capacity/capabilities came from. Unknown facts remain
null/empty and cannot satisfy an enforced context/capability constraint. A task
with no established hard context minimum can use `context_bucket: unknown`;
never change a known requirement to unknown just to make a candidate eligible.
Unsupported settings are excluded. Recompile and obtain review when actual
controls or the catalog changes. Catalog updates do not silently widen policy.

Measurements remain optional and role/category-scoped. Schema v5 adds source,
sample_count, completeness and revision; partial observations cannot satisfy
numeric ceilings or become provider metrics. Unknown cost/quota remains unknown.
Raw subscription tokens do not establish weighted allowance or monetary savings.

## Task brief and privacy

From the worker's permitted handoff, set role/category, ambiguity, risk, context
bucket, reasoning depth, change breadth, expected output and verification needs.
Each field has a controlled vocabulary in the
[request schema](../resources/schemas/request-v5.schema.json); use `unknown` where
needed. Test-author facts come only from its allowed Spec/API/test inputs. Do not
read an implementation to classify that assignment. No extra classifier model
call is needed. The same specialist may receive very different briefs.

The `categories-v2` outbound contract sends these fields, objective, capability
count, known capacity, complete scoped measurements and each profile's controlled
preferences/basis. Each candidate gets different descriptive criteria when its
reviewed preferences differ. Only request-local `p0`, `p1`, … labels leave the
host; model names, catalog IDs, provenance URLs, paths, revisions and evidence
hashes stay local. The router's own model selector is necessarily sent to Jev.
Optional summary mode still needs approval of the exact text for each task.

The TypeSafe [choice API](https://docs.typesafe.ai/introduction/quickstart) supports
text state and per-choice criteria (reviewed 2026-09-27). Returned confidence is
recorded, not treated as calibrated coding success. Receipts retain local task
facts and catalog revision; do not invent a provider rationale or savings claim.
