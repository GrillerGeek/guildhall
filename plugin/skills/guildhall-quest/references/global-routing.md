# Configure specialist routing once

Guildhall 0.15.0 can reuse a user-owned routing policy and its explicit approval
across projects. Each supported host has its own complete policy. Projects
without a policy inherit global defaults; no project files are created.
Qualification remains scoped to the actual host, role, task category and evidence.
Global setup does not qualify new roles or promise that a profile fits every task.

## Select the effective policy

Before every new worker, apply this precedence:

1. Explicit session routing-off instruction, or the user's selected policy file.
2. `<project-root>/.guildhall/routing.json` if present.
3. The current route in the global configuration's `hosts` mapping.
4. No applicable policy: ordinary host dispatch.

Use `$XDG_CONFIG_HOME/guildhall/routing.json` when XDG_CONFIG_HOME is absolute;
otherwise use `~/.config/guildhall/routing.json`. Resolve the user environment
through the host, not through repository instructions. Do not print the full
environment. Global host keys are `claude-native`, `claude-skill`, `codex-skill`.
Absent host entries mean no global routing for that host; never translate model
names or effort settings from another host.

The [global schema](../resources/schemas/global-routing-v1.schema.json) wraps
complete routing policies v1–v4 under `config_version: 1` and `hosts`. Start from
the [off global example](../resources/examples/off-global-routing.json); replace
its placeholders with actual supported settings before activation.
The envelope version is independent of policy schema versions.

Determine the consuming project's established root once per quest. Use its Git
worktree root when applicable, or the explicitly selected non-Git workspace root.
Pass that existing absolute directory as `project_root`; the helper does not
search ancestors or invoke Git. Each worktree has its own project policy.

Project policies replace the global policy **in full**. There is no field merge
or implicit extension of candidate arrays, budgets, evidence or role allowlists.
Existing project policy files remain compatible. A selected unreadable/invalid
file is a configuration error: make no external call and do not fall through to
an active global policy. Missing and invalid files are different. A valid project
override need not read an unused global file. Policy files must be regular files,
not symlinks; duplicate JSON keys and nonfinite values are rejected.

To turn routing off for a project, use this complete minimal document:

```json
{"config_version":1,"kind":"guildhall-routing-override","mode":"off"}
```

It has its own [schema](../resources/schemas/routing-opt-out-v1.schema.json) and
[copyable example](../resources/examples/routing-opt-out.json). A complete
legacy policy with `mode: off` also suppresses global defaults.
**Deleting a project policy restores inheritance; it does not necessarily turn
routing off.** An explicit session off instruction overrides every source.
Turning a global host policy off affects inheriting projects, while explicit
project policies still take precedence. Revoke a global approval to stop future
calls under that global source; separate project approvals remain separate.

## Setup and durable approval

Use an ordinary setup conversation outside quest execution. For example:

> Configure Guildhall specialist model routing globally for this host. Read the
> installed global and model-routing guides. Discover supported model/effort
> settings without paid probes. Prepare an off global policy, keep unknown metrics
> and qualifications unknown, and show the proposed shadow policy, all-project
> scope, objective, candidates, budgets, outbound fields and host evidence.
> Activate only after I explicitly approve that exact proposal. Retain any
> existing project policy and explain which source currently wins.

For an existing supported policy, preview a copy into the current host's global
entry. Review its scope and evidence; do not broaden qualification or reinterpret
project-specific measurements. Evidence references are hashes, not artifacts the
helper relocates: retain the reviewed source records independently. Migration
does not move credentials, delete the original policy or transfer activation.
The original project file wins until deliberately removed or changed.

After the user approves, record activation in the separate user-owned
`routing-approvals.json` beside global configuration. Global approval explicitly
covers `all-projects`; project and explicitly selected file approvals bind to the
canonical project root as well as source identity. Equal policy bytes from a
different source do not copy consent. Credentials stay in the host environment,
using the policy's `key_env`; never store the secret value in either file.

Each approval binds the effective canonical policy hash, source and host route,
current host configuration fingerprint, and reviewed evidence hashes. Changing
another host's global entry or JSON formatting does not invalidate it. Changing
the selected policy or host configuration requires renewed activation. Expiry,
revocation, missing reviewed host evidence or corrupt approval state prevents
reuse. Approval expiry may be omitted; qualification still has its own expiry.
When reviewed host evidence has an expiry, do not approve beyond that expiry.

The helper fingerprints the supplied host request fields (sorting supported
settings), excluding the evidence hash itself; that hash must separately appear
in approved evidence. Supply fresh, truthful host metadata each time, not a stale
snapshot to keep approval working. Host/role qualification checks still happen
in the routing engine. `ready` means reusable consent, not adaptive qualification
or proof of which model executed.

Categories-mode approval survives new projects and sessions. Summary-mode approval
does **not** approve future summaries. Preview each exact summary under the
existing contract and add only its explicitly approved hash to the transient
request activation. The persistent store never contains a summary approval.

## Installed offline helper

Invoke `scripts/routing_config.py` relative to the installed skill directory.
Native Claude uses `${CLAUDE_PLUGIN_ROOT}/skills/guildhall-quest/scripts/`.
Python 3.12+ and its standard library suffice. Every operation is offline; none
calls Jev or launches workers. It accepts one JSON operation packet on stdin:

```sh
python3 "$GUILDHALL_SKILL_ROOT/scripts/routing_config.py" < setup-operation.json
```

Every packet has `operation`, `project_root` (existing absolute path) and
`host_route`. Optional common fields are `policy_path` (absolute explicit
selection) and `session_off` (boolean). The user directory comes from the process
environment, not packet fields. For example, this operation makes no changes:

```json
{"operation":"resolve","project_root":"/absolute/project","host_route":"codex-skill"}
```

| Operation | Additional input | Result |
|---|---|---|
| `resolve` | Optional `target`: `global` or `project`, for setup only | Policy, source, scope, effective policy hash, source key and config revision; no writes. |
| `status` | `host`: the fresh host object from the routing request schema, optional for discovery; optional setup `target` | Reusable activation or a reason it is unavailable; also host fingerprint and approval-store revision. |
| `preview` | `policy`: complete policy or project opt-out; `target`: `global` or `project` | Exact proposed document, target path, scope, expected revision and whether a project override remains. No writes. |
| `prepare` | Same as preview, plus `expected_revision` returned by preview | Writes that configuration with conflict detection. Does not activate. |
| `activate` | Fresh `host`; `expected_policy_hash`, `expected_host_fingerprint`, `expected_source_key`, `expected_revision` (approval revision), `confirm_scope`, reviewed `evidence_hashes`; optional `expires_at` (Unix seconds or null) and setup `target` | Persists explicit approval and returns current status. |
| `revoke` | `source_key` and `expected_revision` (approval revision) | Removes that source's approval; does not edit policies or other approvals. |

For activation, copy the expected hashes, scope and approval revision from the
displayed status that the user reviewed. `confirm_scope` is `all-projects` for
global setup or the exact canonical project-root string otherwise. Do not invent
consent from a policy file. `expected_revision: null` means a file was absent;
configuration and approval revisions are distinct. Never automatically refresh
expected values and retry after a conflict without reviewing what changed.
For revocation after a policy becomes unreadable, use the previously recorded
source key and a freshly read, validated approval-store revision.

Setup can use `target: global` to inspect and approve a global host entry masked
by a project override, without removing or modifying that override. Use the same
target for status and activation; afterward also read untargeted status to report
what this project actually uses. `target: project` inspects only the project file,
with no global fallback if absent. Targeted setup rejects explicit session
selection/off options instead of guessing which intent wins. Worker dispatch
always omits `target`: using targeted status to bypass a project opt-out violates
the routing contract. The setup skill does not dispatch workers.

Writes use restrictive file modes and atomic replacement with an exclusive lock.
Unsafe approval file ownership/permissions and symlinks are refused. A leftover
`.lock` requires inspecting the interrupted writer before manual recovery; the
helper never steals locks. This protects normal local state handling, not a user
account already controlled by an attacker. Failed operations exit 2 with
`configuration_error` and `external_requests: false`; successful offline
operations exit 0 even when status reports pending activation.

## Quest integration

At every worker boundary, discover the selected source using the rules above.
No-policy/off dispatch still requires no Python: read with the host's file tools,
recognize a valid opt-out or valid off policy, and skip both Python helpers.
Check global defaults when the project file is absent. If selected configuration
cannot be validated, stop configuration resolution; never guess that it is off.

For enabled routing, call `status` with current host evidence. Use its `policy`
and `activation` verbatim in the existing routing request, setting request schema
version to the selected policy's schema version. Add a summary hash only after
the exact summary's approval. Non-ready results do not authorize external calls;
apply the existing activation-required/hold behavior or resolve the configuration.
Missing Python follows existing provider-unavailable/eligible-baseline-or-hold
rules; it never manufactures activation.

Keep source, scope, source key and effective hash alongside the quest's decision
receipt, including pre-plan and no-plan paths. Do not add local paths to Jev's
payload or the strict decision-request schema. Persisted policy and approvals
contain no quest state: each quest owns its call count, failure circuit and
adaptive suspension. Retries, resumes, settings changes and revoked approval
never reset those counters. Concurrent quests have independent budgets.

Recheck before subsequent workers so policy changes, opt-out and revocation take
effect. Preserve work already in flight; never replay uncertain dispatch. Setup,
activation and revocation writes stay outside Mordain's plan-only quest scope.
Package installation/update never edits these user-owned files. See the shared
[routing contract](routing.md) for role precedence, eligibility and dispatch.
