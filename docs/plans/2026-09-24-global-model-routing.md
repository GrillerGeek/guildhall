# Global model routing for Guildhall specialists

- Status: implemented in this worktree; validation passed. No personal routing
  settings changed or activated. See the [implementation report](../reviews/2026-09-24-global-model-routing.md).
- Requested outcome: configure specialist model routing once and reuse it across projects.
- Planning date: 2026-09-24.
- Assessed implementation: locally available `origin/codex/routing-all-roles`
  at `0abca43`, and installed Guildhall 0.14.0 routing resources.
- Planning worktree: `GlobalRouting` was at `2e5ad08`, before portable/Jev routing.
  Implementation fast-forwarded it to `0abca43` while preserving this plan.
  Before PR creation it was refreshed to merged `main` at `1c25444`, with all
  checks rerun against the updated baseline.

## Outcome and scope

A user configures and approves routing once for each host they use. Subsequent
Guildhall quests in other projects inherit that policy without creating project
files or repeating unchanged approvals. Projects can supply an explicit policy
override or disable routing. A status command explains the selected source,
approval status and available routing mode before a quest starts.

Cover native Claude, standalone Claude and Codex skill/plugin use. All 18
operational specialists retain their existing eligibility and contracts.
Parent-model selection, model-echo and external IDD workers remain outside this
router. Global configuration does not imply that a candidate is qualified for
every task, host or project; existing role/category, capability, evidence and
expiry checks still apply.

## Existing implementation and extension points

- `plugin/portable/scripts/route_model.py` is the canonical decision engine.
  It consumes a complete request on stdin or through `route(...)`; it does not
  discover policy files, launch workers or write configuration.
- `plugin/portable/references/routing.md` currently instructs the host adapter to
  read `.guildhall/routing.json` and prepare policy, activation and host evidence.
  Activation binds to a canonical policy hash; changing the policy requires
  renewed activation. Approval is not currently a durable cross-project store.
- `plugin/portable/references/model-routing.md` documents project setup and
  removal as a way to disable routing. Both behaviors need updating.
- `plugin/commands/quest.md` and the portable quest/host references consume the
  shared routing contract. Generated installed resources live under
  `plugin/skills/guildhall-quest/` and must be built, not edited directly.

Keep policy discovery and approval persistence in a separate bundled helper,
proposed as `plugin/portable/scripts/routing_config.py`. Retain the existing
decision engine's policy/request contract wherever possible.

## Configuration contract

### Locations and host selection

Use `$XDG_CONFIG_HOME/guildhall/routing.json` when XDG_CONFIG_HOME is an absolute
path; otherwise use `~/.config/guildhall/routing.json`. Resolve home through the
host/user environment, not relative to the repository. Document these same
locations on supported hosts; avoid an additional hidden platform-specific path.

The global file uses its own versioned configuration envelope, independent of
routing policy schema versions. A `hosts` mapping contains a complete existing
policy for each configured route: `claude-native`, `claude-skill`, `codex-skill`.
Do not translate model aliases or effort levels between routes. Unconfigured
routes use ordinary host dispatch and report that no global profile applies.

Keep credentials in the existing environment/secret-management mechanism. The
global file stores `key_env`, never a key. Bundled defaults remain off and
unqualified. Installation and package updates do not create or activate a user
configuration.

### Precedence and overrides

Resolve configuration separately from the existing per-worker model precedence:

1. Explicit session policy selection or explicit session routing-off instruction.
2. `<project-root>/.guildhall/routing.json`, when present.
3. The current host's policy in the global configuration.
4. No policy: existing ordinary host dispatch.

Resolve the project root once from the consuming project's established root;
use its Git worktree root when appropriate, or the explicitly selected workspace
root for non-Git projects. Do not walk unrelated parent directories looking for
additional policies. Worktrees have their own project policy locations.

Existing project policy schemas v1–v4 remain accepted with their current meaning.
A project policy replaces the selected global policy in full. Do not deep-merge
candidate arrays, qualifications, budgets or allowlists. For customization,
the setup helper can materialize a full editable project policy from the global
selection, without copying activation. This deliberately keeps override and
policy-hash behavior predictable.

Add a small versioned project opt-out document, distinct from a full policy,
with an explicit discriminator and `mode: off`. It suppresses global routing
without requiring a candidate catalog. Validate it strictly. Removing a project
file means inherit global defaults, so deletion is no longer the universal
disable operation. Explicit session off suppresses every configured source.
Setting a global host policy off affects inheriting projects; explicit project
overrides remain visible and take precedence.

Malformed or unreadable selected configuration produces an actionable local
error and no provider request. It must not silently fall through to an active
lower-priority policy. A valid project policy or opt-out does not require parsing
an unused global file. Missing files and malformed files are distinct cases.

After policy resolution, preserve existing model precedence: explicit worker
choice → explicit role choice → activated qualified routing → eligible baseline.
Routing off does not erase explicit user model choices.

## Persistent activation and evidence

Store approval records separately from policy, under the user configuration
directory in a versioned `routing-approvals.json`. Only an explicit setup or
activation action writes approval. Quests read it; repository policies and
bundled examples cannot grant approval by declaring themselves approved.

A global approval records all-project scope explicitly, the selected host route,
canonical effective policy hash, policy source identity, approval time, external
request/data-mode consent and reviewed evidence hashes. Bind it to the actual
host configuration fingerprint using the current host-evidence contract.
A project approval additionally binds to the canonical project root; an explicit
external policy selection binds to that source. Equal policy bytes in a different
source do not silently inherit broader approval.

Approve the chosen host entry, not the whole global envelope: editing Claude's
entry must not invalidate an unchanged Codex entry. Formatting-only changes keep
the existing canonical policy hash. Semantic policy changes, changed host
configuration, evidence expiry or revoked approval require the corresponding
review/activation before external requests resume. A missing approval makes no
provider call and follows existing activation-required/fallback behavior.

Global consent in categories mode is reusable across projects. Summary mode
continues to require approval of the exact task summary hash; global consent
does not blanket-approve future project summaries. Preserve this distinction in
setup and status output.

Reuse independently reviewed evidence only within its existing host, profile,
role/category, objective, evidence-level and expiry scope. Do not promote
project-specific findings into universal qualification, broaden roles or invent
measurements while migrating. New project constraints still filter candidates;
an ineligible baseline retains the existing hold behavior. Configuration-based
evidence never becomes observed execution identity.

Approval files use restricted permissions where supported, atomic replacement
and explicit conflict detection for concurrent updates. Define and test refusal
of unsafe approval-file symlinks/ownership before writing. A corrupt approval
store cannot enable routing. Treat this as local user-owned state, not protection
against an attacker already controlling the user's account.

## Runtime behavior and user workflow

1. During setup, discover supported controls without paid probes. Prepare an off
   global host policy from real settings and show its effective source, scope,
   candidates, objective, budget, evidence limitations and outbound fields.
2. On explicit activation, persist the reviewed approval for the exact policy and
   host. Setup writes occur outside Mordain's plan-only quest execution scope.
3. In a new project, resolve the policy and validate the existing approval and
   fresh host evidence. Pass the same policy/activation request shape to the
   routing engine. No project configuration file is created automatically.
4. Provide offline `status`, preparation, activation and revocation operations
   through the bundled configuration helper. Status reports actionable reasons
   for pending activation, unsupported host or expired evidence without making
   network calls, dumping secrets or claiming qualification.
5. Record policy source/scope and effective hash with existing quest receipts.
   Keep local paths out of Jev payloads. Preserve source metadata in the adapter
   envelope if adding it to the strict decision receipt would break compatibility.

Normal no-policy/off quests must still work without Python or credentials. The
adapter can use host file-reading tools to identify absent/off configuration;
invoke Python 3.12+ helpers only for enabled routing or explicit setup/status.
Use one documented precedence contract and fixture matrix to keep that minimal
off-path adapter behavior consistent with the configuration helper.

Global budgets are defaults for each quest, not a shared counter across projects.
Keep `calls_used`, provider failure and adaptive suspension quest-local. Retries,
resumes and policy changes never reset that state. Recheck selected source/hash,
revocation and host evidence before subsequent worker dispatches; changes cannot
authorize new calls without matching approval. Disabling affects future workers,
preserves in-flight work and never replays uncertain dispatches.

## Implementation sequence

### 1. Define and test configuration resolution

- Establish the implementation base containing 0.14.0 routing.
- Add the global envelope, opt-out and approval-store schemas/examples under
  `plugin/portable/resources/`, plus the shared configuration resolver.
- Implement explicit root/path handling, host selection, precedence, full-policy
  replacement, canonical hash reuse and stable error results.
- Add focused tests in `tests/test_routing_config.py` before implementation of
  resolution edge cases. Keep the pure routing decision API compatible.

Acceptance: fixtures select the same effective policy from all three hosts;
legacy project files retain behavior; an off marker prevents global activation;
invalid selected files cannot trigger lower-priority routing.

### 2. Add setup and persistent activation

- Implement offline preparation/status, explicit activation and revocation,
  validating source scope, policy hash, host fingerprint and evidence references.
- Add atomic user-state writes, concurrent-update handling and restricted modes.
- Implement migration preview from an existing project policy to a global host
  entry. Preserve policy semantics, validate evidence references after relocation
  and never copy secrets, activate automatically or delete the project policy.
- Explain that the original project override continues to win until deliberately
  removed or changed. Show the resulting inheritance before changing that file.

Acceptance: one approved unchanged global policy is reusable in two unrelated
projects and a fresh session; source/host/policy changes cannot inherit that
approval; exact-summary approval remains task-specific; revocation is effective
on the next worker boundary.

### 3. Integrate every Guildhall worker path

- Update canonical routing, quest, host and setup references plus native
  `plugin/commands/quest.md` to resolve global/project policy consistently.
- Carry activation and source receipts through pre-plan consultation, docs fast
  lane, prototype/debug, sequential build, review fan-out and PR drafting.
- Keep worker contracts, explicit dispatch settings, eligibility, fallback,
  independence, gates and retry limits unchanged.
- Preserve quest state across retries/resumes and settings refreshes; do not
  persist active quest counters in the global configuration or approval store.

Acceptance: adapter fixtures cover all 18 specialists, all three host routes and
no-plan paths; source changes and revocation make no unauthorized external calls;
off/no-policy behavior still needs no Python.

### 4. Package, document and verify migration

- Regenerate `plugin/skills/guildhall-quest/` using `scripts/build_portable.py`.
- Update root/plugin READMEs, installation instructions, canonical routing guide,
  contributor guidance and changelog. Document global setup, project customization,
  opt-out, revocation and the changed deletion behavior together.
- Extend installed-tool and packaging tests to exercise the configuration helper
  after source removal, using isolated temporary user directories and projects.
- For an installer-visible release, choose the next available minor version and
  align all three manifests; do not rewrite existing historical evidence reports.

Acceptance: an installed bundle supports the entire setup/status/resolution
workflow without a source checkout, and package updates preserve user settings.

## Verification and completion criteria

The regression matrix includes missing/invalid/unreadable files; XDG and fallback
paths; paths with spaces; non-Git roots and worktrees; each precedence combination;
full project replacement; opt-out; unsupported hosts; malformed global entries;
canonical hashing; source-bound approval; two projects and concurrent quests;
approval corruption/revocation; stale host evidence; expired qualification;
summary mismatch; mid-quest policy changes; migration with retained override;
runtime absence; and environment credentials never entering config or receipts.

Use fake transport and sanitized host fixtures to assert both request content
and zero calls for disabled, invalid or unapproved configurations. Existing
decision, usage, qualification, recovery and installed-tool tests must still pass.
Synthetic evidence tests do not establish live model qualification.

Run the repository checks on the updated implementation base:

```sh
python3 scripts/build_portable.py
python3 scripts/build_portable.py --check
python3 scripts/validate_plugin.py
python3 scripts/validate_portable.py
python3 -m unittest discover -s tests -v
git diff --check
```

Run the existing isolated native Claude/Codex and supported skills-installer
probes where their dependencies are available. Add a two-project installed
fixture that approves once, inherits in both, opts out in one, then revokes and
proves future external calls stop. Report fixture checks separately from any
actual host run. Test Python 3.12 and the current supported interpreter; paid
studies and personal global installation are outside implementation validation.

Complete when a supported, approved global profile is automatically inherited
across projects, project exceptions are explicit, approvals survive sessions
without silently expanding scope, and the installed documentation and tests
demonstrate that behavior. The original planning task created only this document.
The subsequent user-requested implementation is recorded in the linked report;
personal installation, activation and publication remain separate operations.
