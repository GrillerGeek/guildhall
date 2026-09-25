# Host capabilities and dispatch

Record a capability summary in the quest plan: host, actual delegation tool,
fresh-context support, concurrency capacity, model metadata, browser access,
permission enforcement and unavailable capabilities. Discover the tools exposed
in this session; a installed manifest does not establish a callable tool.

## Codex

Use the actual available agent dispatch interface, for example `spawn_agent`
when exposed. Start each specialist with a fresh context: use `fork_turns: none`
if that interface offers it, and send the role contract plus the minimal handoff.
Do not fork Mordain's transcript into test-author: it may contain source reads.
Use the host's wait/message interfaces to collect results. Do not create
user-visible tasks as a substitute for workers unless the user requests them.

Leave model/effort overrides unset to inherit user configuration unless the user
has selected an available override for this role or has explicitly activated
the [routing contract](routing.md) with reviewed qualification. Apply its validated
nonnull dispatch settings only when the actual callable interface supports them. A role's Claude tier is not an
instruction to pick a Codex model. The role's effort description explains the
work; it is not evidence that any requested effort level was actually applied.

Mordain may read and run checks with the available terminal/file tools. A plan
edit through `apply_patch` is still a write: keep it in the plan's scope. Codex
installation does not imply Claude `PreToolUse` hooks execute or prevent edits.

## Claude Code

The existing native `/guildhall:quest` remains the established Claude path, with
its explicit model aliases and native hooks. Invoke one route per quest. When
using this standalone portable skill instead, use fresh native worker contexts
and the bundled role body; do not assume the named Guildhall agents or plugin
hooks are installed. A standalone skill does not register them.

When actually using native agents, retain explicit model arguments and roster
baselines, subject to the shared user → role → routing → baseline precedence. Do not infer that a
model override worked from the worker guessing its own identity. Use actual host
metadata if exposed; otherwise record requested model separately from observed
model, with observed `unknown`.

## Other skill-compatible hosts

Map operations to tools actually offered: read/search, write, shell verification,
independent workers, result collection, user questions and browser inspection.
Do not call Claude tool names or MCP identifiers copied from its frontmatter.
No native worker tool means no independent execution. Explain the limitation;
you may discuss the plan but must not claim a completed Guildhall feature quest.
A user's explicit request for ordinary single-agent help is a different workflow
and should be described as such.

## Independence, write scopes and capacity

Send test-author the Spec, public API contract, relevant project conventions and
existing test paths. Exclude implementation snippets, implementation analysis,
other workers' solution proposals and inherited transcripts. Give it only the
read/write capabilities and files its role needs where the host can restrict
these. If the host cannot restrict file reads, state that the prohibition is a
role instruction, not enforced isolation. If the task requires enforced access
control and it is unavailable, stop.

Keep test-author → implementer → optional refactor sequential. Each review gets
its own context. Run independent reviews concurrently up to the actual worker
limit; use batches when needed and report the scheduling limitation. Serialize
any overlapping write scope. Read-only reviewers may inspect the completed diff;
docs-writer and UI-test-author get explicitly named, disjoint output paths.
Await every selected reviewer before the closer. A missing or failed review is
not a passing result. Stop on an unresolved required capability, permission or
role-contract failure; do not route around it with a less constrained worker.

Browser tools vary by host. Discover a supported browser tool/skill; retain
Vera's requirement for an existing Playwright setup and reachable app. Missing
browser access makes the UI check blocked, not passed. Do not install a browser
plugin or modify user configuration just to make the report green.

## Shared optional routing adapter

For all three routes, resolve [global/project configuration](global-routing.md)
and reusable source-bound activation with current host evidence, then follow
[routing](routing.md) before each new worker,
including fast lanes, pre-plan consultation, prototype/debug workers, review
fan-out and PR drafting. Serialize helper decisions and carry its returned quest
state forward before dispatching concurrent workers. A policy file or API key
is not consent: capture explicit activation, exact summary preview consent when
used, and hashes of reviewed baseline/qualification evidence. Only actual host
metadata can establish observed identity. Keep requested, recommended and observed
settings separate; lost attribution or substitution suspends further adaptive
choices while preserving in-flight work. The model-echo diagnostic and external
IDD assignments remain outside adaptive routing.

Use the helper at this installed skill's `scripts/route_model.py`; native Claude
uses the same generated helper through its plugin root. Never select a different
skill or modify host configuration to obtain controls. Unknown runtime/credential
or unsupported controls uses an eligible baseline or holds, according to the
shared contract. Absent/off policy skips Python entirely.

Use [host preflight and evidence](host-evidence.md) for optional schema-v3 routing;
retain worker scopes, gates, state and explicit activation.
