# Guildhall installation and host support

Version **0.9.1**, published on `main`, provides one complete `guildhall-quest` skill and
native Codex metadata. Claude's `/guildhall:quest`, nineteen agent definitions
and hooks remain available. Choose one route per quest to avoid duplicate entry
points. For both tools together, use the [main README](../README.md#install).
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

## Standalone skill

In the consuming project, choose the host explicitly:

```bash
npx --yes skills@1.5.25 add https://github.com/GrillerGeek/guildhall/tree/main --skill guildhall-quest --agent codex --copy --yes
```

Repository-root discovery selects the complete generated bundle. Local development
also supports `/absolute/path/to/guildhall` or the direct
`/absolute/path/to/guildhall/plugin/skills/guildhall-quest` source. Repeat the
original `add` command to refresh a copy. Published-ref installation was verified;
remote update behavior is a separate check.

Use `--agent claude-code` for Claude. Other agent targets may install Agent
Skills; consult the installer's offered targets. Installability does not certify
that an app has fresh worker contexts, browser tools or model-routing controls.
The bundle includes its role references, workflow and MIT license; it does not
need the source checkout after a copy install. There are no consumer npm or
Python dependencies merely to load the skill. IDD execution requires a safe YAML
parser available in the host and actual, recorded human readiness approval.

## Published installation check

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
