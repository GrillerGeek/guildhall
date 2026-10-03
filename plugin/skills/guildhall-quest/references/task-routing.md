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


## Sonnet 5.5 and reviewed model mappings

The Claude catalogs include an optional `claude-sonnet-5-5` profile. Its scoped
coding, debugging and documentation preferences come from Anthropic's
[Sonnet 5.5 announcement](https://www.anthropic.com/claude-sonnet-5-5), checked
2026-09-29. These are documented priors, not Guildhall measurements or guaranteed
savings. Capacity stays null until the actual host's limits are established;
a model's advertised window does not override a gateway or configured cap.

Keep native agent frontmatter as `sonnet`. According to the
[Claude Code model configuration guide](https://code.claude.com/docs/en/model-config),
Sonnet 5.5 needs Claude Code 2.1.284+; the Anthropic API's `sonnet` alias resolves
to 5.5, while other providers may still use older models. Verify the executing
client and current provider mapping without paid probes. Do not infer a mapping
from the alias, another installed CLI, or a generic documentation table.

Schema-v5 hosts can now supply optional `model_resolutions`, for example:

```json
[{"requested_model":"sonnet","resolved_model":"claude-sonnet-5-5",
  "default_effort":"medium","source":"configuration",
  "reference":"reviewed current provider model configuration"}]
```

Use only actually reviewed facts. Each requested model must occur in the current
allowed settings; records are unique by requested model. `source` is
`configuration`, `host_metadata` or `unknown`. A known fact needs a local source
reference; a wholly unknown record has null resolved_model/default_effort/reference
and source unknown. Use a stable configuration reference, not a changing tool-call
ID. Model resolution describes configuration, never proof of served identity.

Mappings and known default effort are included in the control fingerprint and
local receipts, never Jev's payload. Recheck them at each worker boundary. A known
version/default change, provider change or loss of a known mapping invalidates
that host's approval; refresh its catalog and review the affected host entry once.
Reordering records does not invalidate approval. Legacy v5 packets without this
optional field keep their previous fingerprints and cannot detect changes they
do not report. The wizard adds reviewed mappings on an explicit setup refresh;
installation does not invent mappings or silently activate a new policy.

Catalog compilation specializes the generic documented Sonnet starter using the
5.5 template only when a supplied mapping resolves exactly to that model. Older
or unknown mappings retain generic priors. User-authored preferences remain intact.
An explicitly supported pinned ID can be selected independently. In the setup
proposal, prefer either the alias or the pin for an otherwise identical profile.
Keep distinct scopes and user preferences intact; the compiler does not merge
them just because they currently resolve to the same model.

Claude Code defaults Sonnet 5.5 effort to medium; the API defaults to high. Record
the actual configured default when known. Default metadata does not authorize
an effort override: keep effort null unless the worker interface explicitly
supports the requested value. Never carry over high/max just because an older
model used it. Codex's starter remains unchanged; discover only models exposed
by that actual interface. No new benchmark or paid smoke test is required.
