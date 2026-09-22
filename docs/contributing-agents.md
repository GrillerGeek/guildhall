# Contributing with coding agents

Read `AGENTS.md` first. `CLAUDE.md` retains the established native Claude
architecture and model-routing conventions. Ordinary repository maintenance is
not a quest invocation and does not automatically activate quest dispatch rules.

## Ownership

- `plugin/commands/quest.md`, `plugin/agents/`, `plugin/hooks/`: established Claude
  command, nineteen role/diagnostic definitions and native hooks. Preserve these
  when maintaining the portable route unless the change explicitly owns both.
- `plugin/portable/`: maintained portable quest entry and host/lifecycle protocol.
- `plugin/portable/scripts/route_model.py`, its routing reference, schemas and
  examples: canonical optional routing implementation and public contract.
  Native Claude and both skill hosts consume the same generated helper.
- `scripts/evaluate_routing.py`: offline comparison of supplied observations;
  synthetic demonstrations never qualify a model or activate policy.
- `scripts/build_portable.py`: explicit transformation from canonical role bodies
  into portable references. Host metadata is stripped; narrow substitutions adapt
  guidance, evidence, recovery and runbook contracts. These differences are
  intentional and must be reviewed whenever the native role contract changes.
- `plugin/skills/guildhall-quest/`: generated complete bundle; never hand-edit.
- Three manifests: portable `plugin/plugin.json`, Codex
  `plugin/.codex-plugin/plugin.json`, Claude `plugin/.claude-plugin/plugin.json`.
  Keep identity and versions aligned. Claude's existing tier description remains
  specific to its route; portable/Codex descriptions describe their own route.
- `.agents/plugins/marketplace.json`, `.claude-plugin/marketplace.json`: catalogs
  owned by this repository, resolving `./plugin` from the repository root.
- `docs/plans/2026-09-19-portability.md`: assessment, decisions and milestones.

The portable orchestration recorder is a bounded bookkeeping function within
orchestration, not a twentieth native adventurer. It cannot invent approvals,
write implementation or advance status beyond review. Role-specific worker
self-verification remains mandatory.

## Checks

Python 3.12+ with the standard library is sufficient for repository checks:

```bash
python3 scripts/build_portable.py
python3 scripts/build_portable.py --check
python3 scripts/validate_plugin.py
python3 scripts/validate_portable.py
python3 -m unittest discover -s tests -v
git diff --check
```

Assembly rejects unknown generated files and symlinks before writes, never
deletes them, and is idempotent. Tests verify resource drift, copied-bundle
independence, inventory, version agreement and non-destructive refusal. These
are packaging checks, not proof of actual model behavior or enforcement.

Optional install probes run no models and use isolated temporary home/client
profiles, with no copied credentials or personal configuration. They retain
receipts and verify installed contents/modes after source removal:

```bash
python3 scripts/test_install.py --native-codex
python3 scripts/test_install.py --native-claude
python3 scripts/test_install.py --skills-cli /absolute/path/to/skills-1.5.25/bin/cli.mjs
```

The skills CLI path must resolve into an already acquired `skills` package;
the probe checks its identity and version (1.5.25 by default). It exercises both an explicit complete
bundle path and repository-root discovery for Codex and Claude, ensuring the
canonical authoring source cannot accidentally replace the generated bundle. Acquire development dependencies explicitly;
no network/install step is hidden in normal validation. Consumer projects do not
need this repository's Python tooling to invoke a skill. The optional routing
helper separately requires Python 3.12+ when enabled; absent/off policy skips it.

A behavioral review of instructions is not a real host run. Before calling a
host production-verified, exercise an installed quest in an isolated fixture,
inspect dispatch/transcript and actual file changes, and independently verify
RED/GREEN counts, worker separation, scope preservation, review gating and IDD
lifecycle/report evidence. Missing capabilities must refuse truthfully.

## Opt-in model observations

These probes use the existing Codex CLI, authentication and configured model.
They consume model usage and write ordinary Codex session records plus a retained
temporary fixture. They never install into a personal profile or edit client
settings. Unlike the install probes, they are not credential-free processes.
Do not run them in CI or assume a zero exit certifies behavior.

```bash
python3 scripts/evaluate_portable.py --scenario prototype --timeout 420
python3 scripts/evaluate_portable.py --scenario debug --timeout 420
python3 scripts/evaluate_portable.py --scenario missing-gate --timeout 180
python3 scripts/evaluate_portable.py --scenario red-runtime --timeout 420
python3 scripts/evaluate_portable.py --scenario red-setup-error --timeout 420
python3 scripts/evaluate_portable.py --scenario feature --timeout 1800 --yaml-python /absolute/path/to/python-with-pyyaml
python3 scripts/evaluate_portable.py --scenario no-delegation --timeout 180 --yaml-python /absolute/path/to/python-with-pyyaml
python3 scripts/evaluate_portable.py --scenario owner-conflict --timeout 180 --yaml-python /absolute/path/to/python-with-pyyaml
```

The feature scenario uses explicitly synthetic readiness and gap-check inputs;
no human approval is asserted. It exercises real worker calls, files, checks and
status transitions after those supplied fixture inputs. The no-delegation and owner-conflict scenarios reuse these labeled inputs;
prototype, debug and missing-gate scenarios require no YAML dependency. Do not silently install PyYAML; point to an existing runtime.

The two `red-*` scenarios evaluate the test-author role alone, with a fresh
worker, without invoking a feature quest or its lifecycle. They distinguish
promised-but-unimplemented behavior from unrelated broken test setup; no approval
is inferred and no implementation is performed.

Receipts identify baseline changes, additions, process exits and available
session hashes. Review the actual files and records independently. Protected
worker payloads remain opaque; missing child records limit claims about reads
and write attribution. Raw logs can contain project content: keep them local
and publish only reviewed summaries. A timeout or interruption preserves partial
state and does not authorize automatic lifecycle reset. On macOS a process-scoped
sleep assertion lasts only for the child run; no persistent power settings change.

## Routing checks and qualification

Read [the routing guide](model-routing.md) and the generated
[routing contract](../plugin/skills/guildhall-quest/references/routing.md).
Edit canonical resources under `plugin/portable/`, then regenerate. The validator
checks bundled schemas against runtime definitions and ensures examples stay off
and unqualified. Tests use fake transport and exercise failure, eligibility,
attribution and packaging contracts without Jev calls.

The offline evaluator accepts supplied JSON records on stdin or a synthetic demo:

```bash
python3 scripts/evaluate_routing.py --demo
python3 scripts/evaluate_routing.py < reviewed-routing-records.json
```

It compares held-out Jev records against static and deterministic baselines for
each role/category, with paired repeats, no lower acceptance, zero critical
misses/violations and at least 10% improvement on the selected objective against
both baselines. Missing pairs or measurements remain inconclusive; quality
regressions fail. Invalid/overflowing data is rejected. `eligible_for_review`
is arithmetic evidence, not qualification: the output always says
`qualification: false`. The demo's 32 fixtures, two repeats and three strategies
produce 48 development and 144 holdout records; all are synthetic.

Review real host attribution and independent task-quality evidence before
approving qualification hashes. No live Jev or cross-host model qualification
has been performed for 0.10.0. Do not use this feature to route its own evaluation
workers or claim synthetic savings as observed results. See the
[release verification](reviews/2026-09-21-jev-routing.md).

## Distribution and versioning

This routing release candidate is 0.10.0; increment all three manifests for further
installer-visible changes. Existing native Claude agents/commands/hooks remain
preserved. Never rewrite historical plans to claim newer evidence. No repository
change implicitly installs personally, publishes a release or edits the separate
`GrillerGeek/skills` marketplace. All new files follow the repository's MIT license.

## Skills installer compatibility

The documented installer remains `skills@1.5.25`. CI tests that pin and runs a
separate, advisory `latest` check in `skills-compatibility.yml`; a future upstream
failure does not silently change the supported pin or block unrelated work.
The workflow records the resolved version and disables acquisition lifecycle
scripts and installer telemetry. It can also be run through workflow_dispatch.
These are package installation checks, not model execution certification.

Acquire a candidate installer explicitly into a disposable directory:

```bash
npm install --prefix /tmp/skills-candidate --ignore-scripts --no-audit --no-fund --package-lock=false skills@1.7.0
```

Test it without changing the documented default:

```bash
python3 scripts/test_install.py --skills-cli /tmp/skills-candidate/node_modules/skills/bin/cli.mjs --skills-version 1.7.0
```

Omitting `--skills-version` still requires 1.5.25. The supplied CLI must match
both the package name and requested version. CI exercises explicit-bundle and
repository-root copy installs for Codex and Claude without native clients.

See [the onboarding verification](reviews/2026-09-20-skills-onboarding.md) for
remote refresh/removal evidence and the separate directory-discovery limitation.
