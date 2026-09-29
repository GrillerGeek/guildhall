# Codex and Claude dynamic setup

The wizard now recommends Dynamic routing for automatic model selection. It
reviews actual controls, task/profile preferences, explicit fallback(s), role
scope, data and budgets. Ordinary setup does not require study or capture records;
advanced adaptive retains its qualification requirements. Existing modes and
project overrides remain intact unless the user requests a reviewed change.

Schema v5 distinguishes default/role fallbacks from intentional role locks.
Claude's existing roster defaults permit Jev decisions and remain fallbacks;
Codex and standalone Claude use actual exposed worker controls. Per-role fallback
selection does not invalidate the shared control approval. Unsupported fallback
or lock settings fail activation, and task constraints are rechecked at dispatch.
Native aliases, 19 definitions, hooks, namespaces and explicit model arguments
remain; standalone skills do not assume native registration or hook enforcement.

Validation: 168 offline tests passed, including setup/approval/dispatch and
project inheritance/opt-out/revocation from each independently copied skill on all
three host routes. Both skill-creator validations, native validator and portable
validator passed. Isolated native Codex and Claude installs passed byte/mode and
source-removal checks. These establish packaging and mocked integration, not
live model behavior. No study, paid worker or personal activation was performed.
