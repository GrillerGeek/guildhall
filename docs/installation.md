# Guildhall installation and host support

The 0.9.1 portability candidate adds one complete `guildhall-quest` skill and
native Codex metadata. Claude's `/guildhall:quest`, nineteen agent definitions
and hooks remain available. Choose one route per quest to avoid duplicate entry
points. This branch is not yet published; use its built local checkout below.

## Native Codex

```bash
codex plugin marketplace add /absolute/path/to/guildhall --json
codex plugin add guildhall@guildhall-local --json
codex plugin list --marketplace guildhall-local --json
```

The repository catalog resolves `./plugin`. Start a new session and invoke
`$guildhall-quest` with a concrete coding task. A complete feature quest needs
independent worker contexts and shell verification. A host with only skill
loading can read/plan but cannot provide Guildhall's independent execution.

After a local source/version update, repeat the plugin add command to refresh
the cached package. A Git-backed marketplace must be refreshed through its
supported marketplace update before reinstalling. Published-main installation
and external marketplace propagation require separate verification.

## Native Claude Code

The established marketplace route remains unchanged. For this local candidate:

```bash
claude --plugin-dir /absolute/path/to/guildhall/plugin
```

Use `/guildhall:quest` in a fresh session. A repository-owned Claude catalog is
also provided for project-scoped installation:

```bash
claude plugin marketplace add /absolute/path/to/guildhall --scope project
claude plugin install guildhall@guildhall-local --scope project
```

Claude's existing native model aliases and hooks belong to this native route;
installing the standalone skill does not install its native agents or hooks.
The portable entry point may also be visible in a native Claude install; select
only one entry point for a given quest.

## Standalone skill

In the consuming project, choose the host explicitly:

```bash
npx --yes skills@1.5.25 add /absolute/path/to/guildhall/plugin/skills/guildhall-quest --skill guildhall-quest --agent codex --copy --yes
```

Repository-root discovery is also verified with the pinned installer:

```bash
npx --yes skills@1.5.25 add /absolute/path/to/guildhall --skill guildhall-quest --agent codex --copy --yes
```

It selects the complete generated bundle. The published GitHub-ref equivalent
still needs verification after this branch is published.

Use `--agent claude-code` for Claude. Other agent targets may install Agent
Skills; consult the installer's offered targets. Installability does not certify
that an app has fresh worker contexts, browser tools or model-routing controls.
The bundle includes its role references, workflow and MIT license; it does not
need the source checkout after a copy install. There are no consumer npm or
Python dependencies merely to load the skill. IDD execution requires a safe YAML
parser available in the host and actual, recorded human readiness approval.

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
