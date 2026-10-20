# Guildhall installation and host support

This branch prepares **0.19.0**, adding collaborative planning review; these
changes reach the `main` commands below after merge. Removed model routing and
its setup skill remain absent. The generated
`guildhall-quest` skill, Claude's `/guildhall:quest`, nineteen agent definitions
and hooks remain available. Choose one route per quest to avoid duplicate entry
points. Guildhall works independently; IDD is optional. See
[using Guildhall with IDD](../README.md#optional-use-with-idd) if you want to add
structured planning and validation.
Native installation requires the host CLI and Git; `npx skills` additionally
requires Node.js and npm. No contributor build is needed. Catalog names ending
in `-local` are stable identifiers, even when downloaded from GitHub.

## Native Codex

```bash
codex plugin marketplace add GrillerGeek/guildhall --ref main --json
codex plugin add guildhall@guildhall-local --json
codex plugin list --marketplace guildhall-local --json
```

The repository catalog resolves `./plugin`. Start a new session and invoke
`$guildhall-quest` with a concrete coding task. A complete feature quest needs
independent worker contexts and shell verification. A host with only skill
loading can read/plan but cannot provide Guildhall's independent execution.

For updates to a Git-backed installation:

```bash
codex plugin marketplace upgrade guildhall-local --json
codex plugin add guildhall@guildhall-local --json
```

Start a new session after updating. To develop against a local clone, register
`/absolute/path/to/guildhall` instead of the GitHub source. After updating the
local source/version, repeat `codex plugin add`; Git marketplace upgrade does not
refresh local-path catalogs.

## Native Claude Code

Guildhall is distributed through the
[GrillerGeek plugin marketplace](https://github.com/GrillerGeek/skills):

```bash
claude plugin marketplace add https://github.com/GrillerGeek/skills.git
claude plugin install guildhall@grillergeek-plugins
```

Restart Claude Code and use `/guildhall:quest`. To update:

```bash
claude plugin marketplace update grillergeek-plugins
claude plugin update guildhall@grillergeek-plugins
```

The optional tavern pane installs from the same marketplace
([its README](../mods/guildhall-tavern/README.md)). A copy of the marketplace
added before the tavern was listed needs the `marketplace update` above first:

```bash
claude plugin install guildhall-tavern@grillergeek-plugins
```

Restart again after updates. For a session using local development files:

```bash
claude --plugin-dir /absolute/path/to/guildhall/plugin
```

### From this repository's catalog

To install one project straight from this repository's own catalog, the route
`scripts/test_install.py --native-claude` checks:

```bash
claude plugin marketplace add https://github.com/GrillerGeek/guildhall.git --scope project
claude plugin install guildhall@guildhall-local --scope project
```

Update it with `claude plugin marketplace update guildhall-local` and
`claude plugin update guildhall@guildhall-local --scope project`. Choose one
route: do not install both copies in the same client merely to update one.

Claude's existing native model aliases and hooks belong to this native route;
installing the standalone skill does not install its native agents or hooks.
The portable entry point may also be visible in a native Claude install; select
only one entry point for a given quest.

## Standalone skills

Use Node.js **22.20.0+**, npm and Git. Start in the project where you want the
skill available. For an interactive installation:

```bash
npx skills@1.5.25 add GrillerGeek/guildhall
```

Choose your app and scope in the installer. The steps below use **project scope**
and an explicit copy for Codex. Substitute `claude-code` for `codex` when using
Claude. For a global installation, add `--global` to install, list and remove;
use `--global` instead of `--project` for updates.

### Install and verify

```bash
npx --yes skills@1.5.25 add GrillerGeek/guildhall --skill guildhall-quest --agent codex --copy --yes
npx skills@1.5.25 list --agent codex
```

`guildhall-quest` is the sole generated skill.
Look for `guildhall-quest` in the listing. Restart your coding app, then ask it
to use `guildhall-quest` for a small prototype.
This verifies discovery; executing a workflow still depends on the host's tools
and the workflow's own prerequisites.

### Update

To refresh this named skill from its recorded GitHub source:

```bash
npx skills@1.5.25 update guildhall-quest --project --yes
```

This command uses the installer lockfile and detected project destinations.
To retain an explicit target app and copy method, or repair an installed copy,
repeat the corresponding `add` command above instead. Restart the app afterward.
Updates replace installed resources; keep project instructions in your project
rather than editing the installed bundle.

Both installer 1.5.25 and 1.7.0 were exercised against the current published source:
refresh retained the expected bytes and reinstallation repaired a deliberately
modified fixture. This is not evidence of an upgrade between two published
releases. Local-path sources are skipped by `skills update`; repeat their `add`
command after updating the source instead.

### Remove

```bash
npx skills@1.5.25 remove guildhall-quest --agent codex --yes
npx skills@1.5.25 list --agent codex
```

Removal of the quest skill was verified in single-host copy fixtures, preserving an unrelated
skill. In projects sharing `.agents/skills` across hosts, a copy may remain for
another host; inspect the listing and selected path rather than assuming success
means every shared copy was deleted. Avoid `--all` when keeping other skills.

### Local sources and advanced discovery

Replace `GrillerGeek/guildhall` with `/absolute/path/to/guildhall` or the direct
`plugin/skills/guildhall-quest` directory to install the skill's local development files.
To inspect available skills without installing:

```bash
npx skills@1.5.25 add GrillerGeek/guildhall --list
```

The complete bundle includes its MIT license and role references. Loading it
needs no consumer Python dependencies. Executing an IDD Spec requires a safe YAML
parser and actual recorded readiness approval. Native agents, model aliases and
hooks are not installed by this route.

## Upgrading to 0.18.0

0.18.0 removes Jev-assisted model routing and `guildhall-routing-setup`.
Previous routing policies and approvals are no longer read. Updates do not
delete or change personal configuration, policy or approval files.

Update using your installation route above, then restart the host. If you
separately installed the old setup skill with `npx skills`, remove it through
that installer in the same scope and for the same app used to install it:

```bash
npx skills@1.5.25 remove guildhall-routing-setup --agent codex --yes
npx skills@1.5.25 list --agent codex
```

For Claude, use `--agent claude-code`; for a global installation, add `--global`.
This is an explicit removal of the installed skill, not automatic deletion of
personal settings. Native plugin updates replace the plugin's bundled resources.

Guildhall uses ordinary host dispatch: Mordain inherits the configured host
model, native Claude workers retain their frontmatter defaults, and portable
workers use supported host/user model choices without inventing equivalents
for Claude aliases. Explicit supported user or role model choices remain available.

## Optional planning review helper

Ordinary quests and supported native Claude artifact/Codex Page review paths
need no Python helper. Discover actual tools in the writer's context first.
The local OpenCode/Pi companion and automated checkpoint CLI require **Python
3.12+ on POSIX**, including `fcntl`; Windows is not supported by this helper.
It uses only the standard library. No pip install, build, provider installation
or model probe is required to start document/comment mode.

Resolve `scripts/review.py` from your installed `guildhall-quest` directory. In a
repository checkout it is `plugin/skills/guildhall-quest/scripts/review.py`.
The following shell variables are illustrative; use your installed bundle and
consuming project. The plan must already exist directly in `docs/guildhall/plans/`.
Run mutations through Cassian's explicitly scoped review-document handoff;
Mordain may not use these commands to evade his plan-only writes.

```bash
review_helper=/absolute/path/to/guildhall-quest/scripts/review.py
review_root=/absolute/path/to/project
review_plan=docs/guildhall/plans/2026-10-19-example.md
python3 "$review_helper" init --root "$review_root" --plan "$review_plan" --host document --input-json - <<'JSON'
{"quest_id":"example","content":"# Proposal\n\nOptions, recommendation, tradeoffs and open questions.\n","authority":{"display_label":"Project owner","source":"Project owner designation"},"surface":{"kind":"document","id":null,"url":null}}
JSON
python3 "$review_helper" inspect --root "$review_root" --plan "$review_plan" --host document --input-json - <<'JSON'
{}
JSON
```

Replace the example authority/source with the actual designation; it is not an
approval. `init` creates only the named review bundle, refuses conflicting files
and never writes the plan. Finite operations print one JSON envelope. Exit 0
can include a content conflict: inspect `result.conflicts`. Exit 2 means invalid
input, 3 a path/identity/concurrency refusal, and 4 an unavailable operation.

Choose an explicit absolute runtime directory **outside the repository**, owned
by you with private permissions (0700 for an existing directory). An absent
directory is created privately; unsafe existing storage is refused, not chmodded.
Keep this directory for restart/recovery. For local document/comment mode:

```bash
python3 "$review_helper" serve --root "$review_root" --plan "$review_plan" --host document --input-json - <<'JSON'
{"runtime_dir":"/absolute/private/runtime/example"}
JSON
```

Open `result.origin` from the startup envelope and paste `result.write_token`
into that page. The token is per process and stays out of durable documents;
do not commit startup output. The listener is loopback-only. Writes require its
exact Host/Origin and `X-Review-Token`; browser input has no general tool/shell
endpoint. Confirm the displayed session identity before sending feedback.

For adapter-backed review, select `--host opencode` or `--host pi` consistently
from initialization onward and set the matching `surface.kind`. Supply a serve
binding alongside runtime_dir:

| Host | Binding example | Required existing capability |
|---|---|---|
| OpenCode | `{"kind":"opencode","base_url":"http://127.0.0.1:4096","session_id":"chosen-session"}` | Explicit running loopback server/session, exactly one wildcard deny-all permission rule and retrievable tool/history inventory. |
| Pi | `{"kind":"pi","session_file":"/absolute/private/runtime/example/planning.jsonl"}` | Existing `pi` on PATH and selected model; a new dedicated adapter-owned RPC session file within runtime storage. |

The adapter uses existing provider/model selection, checks tool restrictions and
has no startup prompt. It never takes over a Pi TUI, starts an OpenCode server,
copies credentials or modifies provider configuration. Missing restrictions or
identity/history capabilities disable chat visibly; documents/comments remain
usable. Bindings persist in runtime storage; reopening a page does not rebind.
Startup/request deadlines default to 30/60 seconds. Optional JSON fields
`startup_timeout_seconds` and `request_timeout_seconds` accept values above zero
up to 300; a host operation shares one total request budget.

### Checkpoint, recovery and export

Use Save review before discussing edited passages. A second tab with a stale
revision receives a conflict and retains its draft for comparison/download.
Saved comments survive browser closure; unsaved tab drafts require download.
The local Checkpoint button prepares/completes synchronization; it accepts no
proposal. Native hosted surfaces require Cassian's fresh exported observation,
guarded hosted save and actual receipt through their real connector tools.

For CLI checkpointing, call `inspect`, then `checkpoint` with phase `prepare`,
`expected_state_hash` from `state_sha256` and `expected_review_hash` from
`review_sha256`. Examine conflicts/required_saves. Preserve both sides of a
conflict for the designated owner. Complete only the returned checkpoint_id,
using fresh guards and, when hosted, the actual receipt and observation. A partial
save retains pending evidence and the prior common baseline; never replay a
completed save or fabricate an unknown revision. `clean` means synchronized,
not accepted. See the [full payload contract](../plugin/portable/references/collaborative-planning.md#optional-cli).

Delivery states are `prepared`, `sent-unknown`, `response-received` and
`failed-before-send`. Persisted request IDs correlate exact-session history.
After timeout/disconnection or cancellation, inspect the original session and
request; unknown delivery is never blindly resent or cleared by deleting the
journal. Cancellation acknowledgement does not prove no answer arrived. Restart
with the same runtime/binding; explicit rebind requires resolved in-flight work.
An unacknowledged host cancellation is a separate persisted barrier: even if its
answer is later recovered, new sends and rebind stay blocked, including after
restart. Without safe host confirmation this can remain blocked indefinitely.
There is no force-clear, replay or automatic barrier recovery operation. Preserve
the runtime and review bundle, inspect the exact host session and use document
comments or the portable Markdown/HTML fallback while confirmation is unavailable.
For read-only delivery counts, `inspect` accepts
`{"runtime_dir":"/absolute/private/runtime/example"}`. Without it counts are
null and delivery coverage is unavailable, not zero pending requests.

To refresh the standalone HTML after edits, substitute the fresh inspect result's
`review_sha256` for the placeholder below:

```bash
python3 "$review_helper" export --root "$review_root" --plan "$review_plan" --host document --input-json - <<'JSON'
{"expected_review_hash":"REPLACE_WITH_CURRENT_REVIEW_SHA256"}
JSON
```

Open the bundle's `review.html` without a provider, credentials or running server.
Reading, local editing, option comparison and downloads remain available; chat
and synchronization are disabled. Downloads are drafts until deliberately saved.

Review prose is limited to 256 KiB UTF-8. Full browser edits must also fit a
264 KiB serialized JSON request; heavy escaping can reach that limit first.
Feedback/control requests fit 32 KiB; comments/selections fit 4,000 characters;
feedback and decision lists each fit 200 entries. Runtime requests also stop at
200; no automatic safe archival operation is provided. Split/archive explicitly
without discarding unresolved evidence. Lower host limits take precedence.

The current implementation still has a disclosed medium Pi aggregate-event
memory concern and a low concern that maximum `/state` response history can
approach 50 MiB. These remain follow-up work. This is an opt-in local companion,
with live-host acceptance pending, not production certification. To roll back,
stop only the owned companion/Pi process, preserve both runtime and review bundle,
and return to Markdown/HTML plus conversation. Do not stop an unrelated OpenCode
server or erase unknown delivery to restart work.

## Published installation check

The following published checks describe **0.9.1**, not verification of 0.19.0.

On 2026-09-20, all four GitHub installation routes above passed in isolated
profiles: native Codex, native Claude, standalone Codex and standalone Claude.
Installed bytes and modes matched version 0.9.1 from main `1cfef81`. These checks
loaded no models and did not change personal plugin installations. The earlier
local-source checks additionally verified source removal.

## Verified coverage

| Route | Installation evidence | Execution evidence |
|---|---|---|
| Native Codex plugin | Installed/enabled 0.9.1 in an isolated profile; complete cache retained after source removal. | Portable execution was tested from a complete copied skill bundle; native-cache invocation after source removal was not exercised. |
| Standalone Codex skill | Explicit bundle and repository-root copy routes pass with skills 1.5.25. | Full feature quest, prototype, debugging and selected refusal cases observed. |
| Native Claude plugin | Project installation enabled 0.9.1; complete cache retained after source removal. | Native prototype command observed using session-only plugin loading. |
| Standalone Claude skill | Explicit bundle and repository-root copy routes pass with skills 1.5.25. | Portable quest execution in Claude remains unverified. |
| Other skill-capable apps | Not exercised. | Requires host capability checks; not certified. |

Feature execution used explicitly synthetic readiness and gap-check inputs;
actual human approval remains required for live Specs. The execution report
records the exact evidence and remaining limits.

Planning review has a separate acceptance boundary:

| Surface | Review evidence and remaining acceptance |
|---|---|
| Native Claude artifact | Contract/allowlist and package checks; actual writer access, native interactions, feedback retrieval and reconciliation remain pending. |
| Codex Space Page | Capability-discovered contract; live editable Page, anchored comments, separate Page chat write-back, embed and guarded checkpoint remain pending. |
| OpenCode companion | Isolated synthetic transport fixtures; configured real-host passage chat, reconnect, checkpoint and export remain pending. |
| Pi companion | Isolated synthetic RPC fixtures; real dedicated tool-free session, recovery, interaction and shutdown acceptance remain pending. |
| Portable Markdown/HTML | Local fallback/export behavior has isolated test coverage; it does not certify native host behavior or model quality. |

The [collaborative-planning verification report](reviews/2026-10-19-collaborative-planning-verification.md)
records the current checks and their limits. Historical transport spikes remain
labeled synthetic evidence; no synthetic responder is the production default.

## Operational differences

- Mordain uses the configured host model; Claude aliases are not mapped to
  invented equivalents. Requested and observed model information are separate.
- Test-author receives a fresh context without the implementation transcript.
  If the host cannot do this, execution stops before feature writes.
- Role write/read restrictions are instructions unless the host actually
  enforces them. Claude's narrow `Write` hook is not a portable sandbox.
- Closing Guildhall technical review is a bundled, read-only review of completed
  work and verification evidence. Formal IDD technical-review annotations use
  their own separate workflow and writer contract.
- Reviewers receive complete working-tree evidence, including untracked files.
  Uncommitted work does not disappear from a `base..HEAD` comparison.
- IDD lifecycle decisions remain in orchestration. A bounded recorder performs
  verified status/report edits, preserving Mordain's plan-only writes. It does
  not replace an active IDD runner or fabricate human approval.

See [the assessment](plans/2026-09-19-portability.md) and the
[initial verification report](reviews/2026-09-19-portability.md) and
[execution follow-up](reviews/2026-09-19-portability-execution.md) for evidence and limits.
