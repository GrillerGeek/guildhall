# Guildhall

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Plugin](https://img.shields.io/badge/plugin-v0.10.0-green.svg)](plugin/README.md)

**Give a coding task to a team of AI specialists that writes tests, implements the
change, reviews it and prepares a PR draft.**

Guildhall is a coding workflow for **Codex and Claude Code**, also distributed as
a portable Agent Skill. Its coordinator, Mordain, maintains a durable plan and
dispatches independent specialists. Feature work follows tests → implementation
→ optional refactoring → reviews. Prototype mode explores an idea with less
ceremony; debug mode investigates the cause before a fix is planned.

Plans are saved under `docs/guildhall/plans/`. A completed feature quest produces
code, tests, review evidence and a PR draft. Publishing a PR is a separate action.

**Guildhall works on its own. IDD is an optional companion, not a dependency.**

## Install

The commands below install Guildhall from its published main branch. **Version
0.10.0 is the routing release candidate; it becomes available there after merge.**
Choose one route for your coding app. No repository clone, build or IDD
installation is required.

### Codex

Run in a terminal with the Codex CLI and Git installed:

```bash
codex plugin marketplace add GrillerGeek/guildhall --ref main --json
codex plugin add guildhall@guildhall-local --json
```

Start a new Codex session in the project you want to work on. The catalog name
ends in `-local` for compatibility; these commands download from GitHub and do not
require a local clone.

### Claude Code

Run in a terminal from the project you want to work on, with Claude Code and Git installed:

```bash
claude plugin marketplace add https://github.com/GrillerGeek/guildhall.git --scope project
claude plugin install guildhall@guildhall-local --scope project
```

Restart Claude Code in that project. These commands install the plugin for that
project using the catalog maintained in this repository.

### Alternative: `npx skills`

With **Node.js 22.20.0+**, npm and Git available, run this in your project:

```bash
npx skills@1.5.25 add GrillerGeek/guildhall
```

The interactive installer lets you choose your coding app and installation scope.
Choose **project** to keep the skill with this project; choose **global** if you
want it available across projects. Version `1.5.25` is the tested installer pin,
not the Guildhall version.

The repository contains one installable skill: `guildhall-quest`, including its
workflow and role references. Standalone skills do not install Claude's native
agents or hooks. After restarting your app, ask it to use `guildhall-quest` to
prototype a small task. The `/guildhall:quest` examples below are native Claude
plugin commands; skill-only installs use `guildhall-quest` instead.

Guildhall execution needs independent worker contexts and shell tools. Being
listed as an installer target does not establish that an app supports a quest.

Choose the native plugin or standalone skill route in a client to avoid duplicate
entry points. The [installation guide](docs/installation.md#standalone-skills)
covers explicit app selection, verification, updates and removal.

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

A concrete task description is enough to start. You do not need IDD artifacts or
an IDD plugin installation to use these prototype, feature or debug workflows.

## What happens during a feature quest?

1. **Plan:** clarify the task, inspect project guidance and save a durable plan.
2. **Test:** a fresh worker writes the acceptance tests and observes expected RED.
3. **Build:** an implementation worker makes those tests pass; refactor if needed.
4. **Review:** independent reviewers assess the relevant security, documentation
   and production concerns. Conditional reviews run when the change calls for them.
5. **Close:** verify the project, record the outcome and prepare a PR draft.

The test → build → refactor sequence stays ordered. Independent reviews may run
in parallel when the host supports it. Mordain's own edits remain limited to the
plan; specialists carry out the implementation and review work.

## Optional: Jev-assisted model routing

Version 0.10.0 adds an optional helper shared by native Claude and the portable
Claude/Codex skill. Routing is **off by default**. Ordinary quests retain their
existing model defaults without a Jev key or the routing Python runtime.

- **Shadow** records recommendations while keeping baseline dispatch. It needs
  explicit activation, supported candidate profiles and Python 3.12+; it does
  not require adaptive qualification.
- **Adaptive** may apply recommendations only for evaluated `docs-writer` and
  `pr-author` assignments with reviewed host and model evidence. No qualified
  profiles ship with this release.

An API key alone enables nothing. Prepare the project policy before starting a
quest, then explicitly activate it. The [routing guide](docs/model-routing.md)
includes a setup prompt, safe smoke command, data-sharing details, receipts and
disable instructions. There are no measured Jev savings or live qualification
claims; see the [verification report](docs/reviews/2026-09-21-jev-routing.md).

## Optional: use with IDD

[Intent-Driven Development (IDD)](https://github.com/GrillerGeek/idd-framework)
helps define a product's purpose, expected behavior and acceptance criteria in
reviewed Specs. Add it if you want that structured planning and validation
workflow. Follow [IDD's installation instructions](https://github.com/GrillerGeek/idd-framework#install);
Guildhall remains usable without it.

With IDD installed, begin discovery with `$idd-orchestration` in Codex or
`/idd-framework:interview` in the native Claude plugin. The paired workflow is
**define and review with IDD → build with Guildhall → validate with IDD**.

When an IDD Spec is ready, has recorded human readiness approval and a current
clean gap-check, use `$guildhall-quest Implement SPEC-<your-id>` in Codex or
`/guildhall:quest Implement SPEC-<your-id>` in Claude. Replace the placeholder with
your actual Spec ID. Guildhall honors the Spec's Boundaries and uses a bounded
recorder for status/report edits. Execution ends at `review`; human approval and
subsequent validation remain required.

IDD also has its own implementation runner. Choose one execution owner for a
Spec instead of running both simultaneously.

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
- [Model routing](docs/model-routing.md): optional Jev setup and operation.
- [Contributor guide](docs/contributing-agents.md) and [AGENTS.md](AGENTS.md): source ownership and checks.
- [Design history](docs/superpowers/): previous architecture and model-routing decisions.

Native Claude components live in `plugin/agents/`, `plugin/commands/` and
`plugin/hooks/`. Portable sources live in `plugin/portable/`; the complete
`plugin/skills/guildhall-quest/` bundle is generated by `scripts/build_portable.py`.
Contributors use Python 3.12+; users do not need the build tooling to load the skill.

## License

[MIT](LICENSE).
