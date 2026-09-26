# Guildhall installation and host support

Version **0.16.0 is a release candidate**, available through the `main` commands
below after merge. It includes all-role routing eligibility, usage/evidence/study tools, independent
`guildhall-quest` and `guildhall-routing-setup` skills and native Codex metadata. Claude's `/guildhall:quest`, nineteen agent definitions
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

From the project you want to work on:

```bash
claude plugin marketplace add https://github.com/GrillerGeek/guildhall.git --scope project
claude plugin install guildhall@guildhall-local --scope project
```

Restart Claude Code and use `/guildhall:quest`. To update:

```bash
claude plugin marketplace update guildhall-local
claude plugin update guildhall@guildhall-local --scope project
```

Restart again after updates. For a session using local development files:

```bash
claude --plugin-dir /absolute/path/to/guildhall/plugin
```

The separate `GrillerGeek/skills` marketplace remains another distribution route;
the commands above use this repository directly. Do not install both copies in
the same client merely to update one.

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
npx --yes skills@1.5.25 add GrillerGeek/guildhall --skill guildhall-routing-setup --agent codex --copy --yes
npx skills@1.5.25 list --agent codex
```

The second add command installs the optional setup wizard. Each skill can be
installed alone; the wizard does not dispatch workers or require the quest skill.
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
repeat the corresponding `add` command above instead. To update the setup wizard,
use `update guildhall-routing-setup --project --yes` with the same installer. Restart the app afterward. Updates
replace installed resources; keep project instructions in your project rather
than editing the installed bundle.

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

To remove only the wizard, replace `guildhall-quest` with `guildhall-routing-setup`
in the remove command. Configuration/approvals remain in their user-owned location.

Removal of the quest skill was verified in single-host copy fixtures, preserving an unrelated
skill. In projects sharing `.agents/skills` across hosts, a copy may remain for
another host; inspect the listing and selected path rather than assuming success
means every shared copy was deleted. Avoid `--all` when keeping other skills.

### Local sources and advanced discovery

Replace `GrillerGeek/guildhall` with `/absolute/path/to/guildhall` or the direct
`plugin/skills/guildhall-quest` or `plugin/skills/guildhall-routing-setup` directory
to install that skill’s local development files.
To inspect available skills without installing:

```bash
npx skills@1.5.25 add GrillerGeek/guildhall --list
```

The complete bundle includes its MIT license and role references. Loading it
needs no consumer Python dependencies. Executing an IDD Spec requires a safe YAML
parser and actual recorded readiness approval. Native agents, model aliases and
hooks are not installed by this route.

## Optional routing setup after installation

With the wizard installed, restart the host and ask **“Set up Guildhall routing”**,
or invoke `$guildhall-routing-setup` in Codex. It detects the executing host, offers
global/project scope and a goal, checks profiles and prerequisites, then presents
a plain-language proposal. You choose whether to save and enable shadow mode, save
off, change choices or cancel. It never treats missing evidence as qualification
or runs a paid test automatically. A returning user can ask the same skill to
change, diagnose or disable routing.

For manual setup or the wizard’s underlying contract:

Restart the host after installing or updating. Locate the installed
`guildhall-quest` directory containing `SKILL.md`, `resources/` and `scripts/`.
Native Claude uses `${CLAUDE_PLUGIN_ROOT}/skills/guildhall-quest`; standalone and
Codex paths depend on the selected installation scope. Use the installed bundle,
not `plugin/portable`, which is an authoring source.

Follow [global routing setup](../plugin/skills/guildhall-quest/references/global-routing.md)
to prepare and approve one policy per host in `~/.config/guildhall/routing.json`
(or the absolute XDG_CONFIG_HOME location). Projects inherit it without setup.
Optional `.guildhall/routing.json` files replace those defaults; an explicit project
opt-out disables routing. Removing a project policy restores global inheritance.
Package updates and removal leave user configuration and approval files alone.
The [routing guide](model-routing.md) covers qualification and outbound data. Python **3.12+** is required only for the optional routing helper;
normal skill loading and off-mode dispatch do not need it. Native Claude's
existing Python hooks retain their separate prerequisites. Set
`TYPESAFE_API_KEY` in the environment of the terminal/process launching the host
when external routing calls are wanted. Never put the key in the policy, prompt,
receipt or command arguments. A GUI app may not inherit your terminal environment.

Start with explicitly activated shadow mode. Shadow uses supported host profiles
without adaptive qualification and preserves baseline dispatch. Schema v4 makes all 18 specialists eligible for adaptive routing with explicit
role allowlists and scoped qualification; no live-qualified profiles ship. Read
the [role matrix and migration guide](../plugin/skills/guildhall-quest/references/role-eligibility.md)
before expanding an existing policy.
Neither installation, a policy file nor an API key is activation. Ordinary
Guildhall and IDD integration remain independent of Jev.

## Published installation check

The following published checks describe **0.9.1**, not live qualification of the
current router. Current candidate checks and remaining limits are tracked in the
[routing issue implementation report](reviews/2026-09-22-routing-issues.md).

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
