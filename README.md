# Guildhall

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Plugin](https://img.shields.io/badge/plugin-v0.9.1-green.svg)](plugin/README.md)

**Give a coding task to a team of AI specialists that writes tests, implements the
change, reviews it and prepares a PR draft.**

Guildhall is a coding workflow for **Codex and Claude Code**, also distributed as
a portable Agent Skill. Its coordinator, Mordain, maintains a durable plan and
dispatches independent specialists. Feature work follows tests → implementation
→ optional refactoring → reviews. Prototype mode explores an idea with less
ceremony; debug mode investigates the cause before a fix is planned.

Plans are saved under `docs/guildhall/plans/`. A completed feature quest produces
code, tests, review evidence and a PR draft. Publishing a PR is a separate action.

## Guildhall and IDD: which do I need?

| Tool | What it provides | Start here when |
|---|---|---|
| **Guildhall** — this repository | A coordinated build with independent test authors, implementers and reviewers. | Your task is concrete enough to implement, prototype or investigate. |
| **[Intent-Driven Development (IDD)](https://github.com/GrillerGeek/idd-framework)** | Guided discovery, linked requirements and reviewed Specs, followed by lifecycle tracking and validation. | The purpose, behavior or acceptance criteria still need definition. |

They work independently or together: **define and review with IDD → build with
Guildhall → validate with IDD**. A Guildhall quest does not require IDD for every
task. When executing an IDD Spec, it honors readiness approval, gap-check evidence,
Boundaries and human review gates. IDD also offers an implementation runner;
choose one execution owner instead of running both on the same Spec.

## Install

The following commands install **Guildhall 0.9.1 and IDD 1.7.1 from their published
main branches**. Choose your coding app. If you only want Guildhall, run just its
two commands. No repository clone or build is needed.

### Codex

Run in a terminal with the Codex CLI and Git installed:

```bash
codex plugin marketplace add GrillerGeek/idd-framework --ref main --json
codex plugin add idd-framework@idd-framework-local --json

codex plugin marketplace add GrillerGeek/guildhall --ref main --json
codex plugin add guildhall@guildhall-local --json
```

Start a new Codex session in the project you want to work on. The catalog names
end in `-local` for compatibility; these commands download from GitHub and do not
require a local clone.

### Claude Code

Run in a terminal from the project you want to work on, with Claude Code and Git installed:

```bash
claude plugin marketplace add https://github.com/GrillerGeek/idd-framework.git --scope project
claude plugin install idd-framework@idd-framework-local --scope project

claude plugin marketplace add https://github.com/GrillerGeek/guildhall.git --scope project
claude plugin install guildhall@guildhall-local --scope project
```

Restart Claude Code in that project. These commands use project scope; omit the
other tool's pair of commands if you only want one. The catalogs are maintained
in the two source repositories.

### Alternative: `npx skills`

For a skill-only installation, run these in your project with Node.js and npm
available:

```bash
npx --yes skills@1.5.25 add https://github.com/GrillerGeek/idd-framework/tree/main --skill idd-orchestration --agent codex --copy --yes
npx --yes skills@1.5.25 add https://github.com/GrillerGeek/guildhall/tree/main --skill guildhall-quest --agent codex --copy --yes
```

The IDD router includes all fifteen workflow stages. Replace `--agent codex` with
`--agent claude-code` for Claude. Other installer targets may support skills, but
Guildhall execution also needs independent worker contexts and shell tools.
Standalone skills do not install Claude's native agents or hooks. Choose either
the native plugin or standalone skills for each tool in a client to avoid duplicate
entry points. After restarting your app, ask it to use `idd-orchestration` to
interview you about your product, or `guildhall-quest` to prototype a small task.
The `/idd-framework:*` and `/guildhall:quest` examples below are native Claude
plugin commands; skill-only installs use the installed skill names instead.

See [installation, updates and host support](docs/installation.md) for details,
and the [IDD installation guide](https://github.com/GrillerGeek/idd-framework/blob/main/docs/installation.md)
for IDD-specific requirements.

## Your first quest

Start a new session in the project you want to change. Try a small prototype:

```text
# Codex
$guildhall-quest Prototype a Python CLI that summarizes a local CSV file.

# Claude Code native plugin
/guildhall:quest Prototype a Python CLI that summarizes a local CSV file.
```

For feature work, describe the desired behavior and how it should be tested.
Guildhall plans the work, dispatches a separate test author before the implementer,
and selects reviews based on the change. It uses your host's configured model;
Claude's native route also retains its role-specific model aliases.

If you need help defining the feature first, start IDD:

```text
# Codex
$idd-orchestration Interview me about a tool that helps volunteers schedule shifts.

# Claude Code native plugin
/idd-framework:interview I want to build a tool that helps volunteers schedule shifts.
```

After IDD produces a ready Spec with recorded human readiness approval and a
current clean gap-check, use `$guildhall-quest Implement SPEC-<your-id>` in Codex
or `/guildhall:quest Implement SPEC-<your-id>` in Claude, replacing the placeholder
with your actual Spec ID. Guildhall's execution ends at `review`; human approval
and subsequent validation remain required.

## What happens during a feature quest?

1. **Plan:** clarify the task, inspect project guidance and save a durable plan.
2. **Test:** a fresh worker writes the acceptance tests and observes expected RED.
3. **Build:** an implementation worker makes those tests pass; refactor if needed.
4. **Review:** independent reviewers assess the relevant security, documentation
   and production concerns. Conditional reviews run when the change calls for them.
5. **Close:** verify the project, record the outcome and prepare a PR draft.

The test → build → refactor sequence stays ordered. Independent reviews may run
in parallel when the host supports it. For IDD work, a bounded recorder handles
approved status/report edits while Mordain's own edits remain limited to the plan.

## Host support and limits

| Route | What has been checked |
|---|---|
| Codex | Native and standalone installation; portable feature, prototype, debug and selected refusal workflows. |
| Claude Code native plugin | Installation and native prototype execution; existing command, agents and hooks preserved. |
| Claude Code standalone skill | Installation checked; portable quest execution in Claude remains unverified. |
| Other Agent Skills apps | Require host-specific verification, especially independent workers and shell execution. |

Skill loading alone is not enough to execute a quest. Missing required worker or
verification capabilities must stop execution. Portable role scopes are
instructions; they do not reproduce Claude's native hooks or create an OS sandbox.
The feature evaluation used explicitly synthetic readiness inputs, not real human
approval. See the [verification report](docs/reviews/2026-09-19-portability-execution.md)
for evidence and remaining limits.

## Reference and contributing

- [Plugin reference](plugin/README.md): native Claude usage and detailed workflows.
- [Character roster](plugin/CHARACTERS.md): eighteen specialists and one diagnostic agent.
- [Portable workflow](plugin/portable/references/quest.md): host-neutral execution contract.
- [Contributor guide](docs/contributing-agents.md) and [AGENTS.md](AGENTS.md): source ownership and checks.
- [Design history](docs/superpowers/): previous architecture and model-routing decisions.

Native Claude components live in `plugin/agents/`, `plugin/commands/` and
`plugin/hooks/`. Portable sources live in `plugin/portable/`; the complete
`plugin/skills/guildhall-quest/` bundle is generated by `scripts/build_portable.py`.
Contributors use Python 3.12+; users do not need the build tooling to load the skill.

## License

[MIT](LICENSE).
