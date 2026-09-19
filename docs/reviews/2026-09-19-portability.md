# Guildhall portability candidate — September 19, 2026

## Outcome

Prepared a local **0.9.0** candidate from main `5286df9`, on
`codex/portable-guildhall`, in `/tmp/guildhall-portability`. The original local
feature checkout is unchanged. No Guildhall push, PR, release or personal install
was performed in this work.

Implemented shared maintenance guidance; a complete portable quest skill with
nineteen role references, host capabilities and IDD lifecycle bookkeeping;
reproducible assembly; native Codex/portable manifests; repository-owned catalogs;
version alignment; packaging tests and CI extensions; installation documentation.

Claude's nineteen agent files, quest command, character reference and plugin hooks
remain byte-for-byte unchanged from the baseline. Its manifest changes only the
version from 0.8.1 to 0.9.0. All three manifests share that version. Portable
references intentionally adapt Claude-specific conventions and several discovered
contract conflicts; the source transformations are explicit in the assembler.

## Independent instruction review

A separate reviewer traced the Codex feature, no-delegation host, missing-browser
and existing-Claude scenarios without editing files or running a live quest.
It found missing lifecycle/report ownership, committed-diff-only inputs,
conflicting refactor rollback instructions, a missing-server UI-trigger loophole,
late closing-review discovery, overclaiming from green tests, inconsistent runbook
headings, and docs-only/implementation-reading role contradictions.

The revised contracts resolve these textually:

- Mordain remains the decision owner and plan-only writer; a bounded orchestration
  recorder performs verified status/report operations. Worker self-verification
  is retained, report assembly and review transition are separate, invalid gates
  refuse before writes and failed execution stays in-progress.
- Review inputs include the full baseline-to-current worktree, untracked outputs
  and attribution of pre-existing changes. No commit is needed to enable review.
- Failed refactors preserve the diff for a recovery decision.
- UI work selects the needed checks; missing browser/server prerequisites block
  them rather than causing an unnoticed skip. Static accessibility still applies.
- Closing IDD capability is discovered before feature execution.
- Green tests establish tested behavior only, not complete Spec validation.
- Runbook structure is consistent; documentation-only corrections use a scoped
  ask/source of truth, and all documentation/source writes are explicitly named.

Final independent recheck reported no remaining blockers in those textual
scenarios. This is not a model/host execution observation or human approval.

## Mechanical validation

- Baseline/native validator: 19 agents, zero errors, zero warnings.
- Complete portable bundle: 25 files, including the skill, host/quest/lifecycle
  protocols, roster, nineteen generated role references and MIT license.
- Build/check idempotence and internal resource links pass.
- Twelve regression tests pass, covering copied-source independence, generated
  drift, unknown-file preservation, symlink refusal, manifest disagreement,
  catalog escape, resource escape/missing links and inventory changes.
- The bundled Codex plugin validator and skill-creator validator pass using the
  existing Python 3.12 environment with PyYAML. The repository's own checks and
  tests use Python's standard library only.

## Actual installation observations

The no-model probe used temporary HOME, Codex/Claude/XDG state and an explicit
child-environment allowlist with no copied credentials. It used the existing
pinned `skills@1.5.25` CLI. Personal installations/settings were not changed.

Final-candidate successful receipt (the earlier `guildhall-install-j8hbb01c`
installation also passed before final documentation/formatting edits):
`/private/var/folders/f0/_sscvrpd48s9srngb0d0l_mh0000gn/T/guildhall-install-3xuvqujh/report.json`

- Native Codex: registered the local repository catalog, installed and enabled
  `guildhall@guildhall-local` at 0.9.0, verified every cached file byte and mode,
  deleted the fixture source and verified the complete cache again.
- Standalone Codex copy: installed the complete skill, verified exact bytes/modes,
  removed its source and verified independence.
- Standalone Claude Code copy: same checks, with explicit Claude target.

Two original failed harness receipts remain in neighboring temporary directories:
`guildhall-install-mfhdtksl` (Codex profile directory not created) and
`guildhall-install-mv5r7gtw` (macOS /var versus /private/var containment comparison).
The harness fixes created its owned profile folders and resolved its temp root;
no product behavior was weakened, no success was inferred from those failures,
and no personal fixture repair occurred.

## Remaining before production certification/publication

1. Run installed feature, prototype and debug quests in fresh Codex sessions;
   independently inspect actual worker contexts/transcripts, RED/GREEN and
   additional verification, state preservation, review gates and recorder results.
2. Exercise negative execution cases: malformed/missing IDD gate, unavailable
   delegation, missing UI capabilities, out-of-scope writer, retry exhaustion,
   lifecycle owner conflict and interrupted-run recovery.
3. Smoke-test the unchanged native Claude quest after adding the skill surface;
   native installation/discovery is distinct from native command behavior.
4. Verify another named skill-compatible host before promising full support for
   it. Do not equate skill installation with available delegation or enforcement.
5. On user instruction, push/open a PR, inspect hosted CI and verify published-ref
   installation. External marketplace updates, release tags and personal
   installations remain separate actions.

This candidate is installable and mechanically checked. It is **not yet certified
for end-to-end quest execution on non-Claude hosts**. No hook parity, enforced
filesystem isolation, model-routing equivalence or broad host support is inferred.

## Actual Codex prototype output observation

A fresh `codex exec --ephemeral --json -s workspace-write` invocation used the
configured model and existing authentication against a disposable project with
a copied skill. Prompt requested a prototype-only `hello.py`, an independent Pip
worker, two shell assertions, no Spec/tests/PR, no commits or network activity,
and preservation of installed resources, `AGENTS.md` and `KEEP.txt`.

Evidence directory:
`/private/var/folders/f0/_sscvrpd48s9srngb0d0l_mh0000gn/T/guildhall-prototype-ezd5_a9y`

The process exited 0. Independent artifact checks confirmed:

- `greet('  Jason  ')` returns `Hello, Jason!`;
- whitespace-only input returns `Hello, adventurer!`;
- all 27 original files retain exact bytes and modes;
- the only new files are `hello.py` and the quest plan;
- the visible parent shell writes target only the plan.

Receipt SHA-256:
`47a56a94ec7cbba131edca789aedc60fdd0b2908e119022385097b7c3ed097ab`

JSONL transcript SHA-256:
`be30a610062d6cbe54348d888d228a7a8b031e80080b053e71efb3180e7b1c69`

The parent reports a successful fresh Pip dispatch, but the JSONL lacks a
complete spawn/worker trace. That assertion is **not accepted as proof of worker
independence or role-write enforcement**. This is an output/preservation
observation, not full Guildhall execution certification.

The receipt reports 1073.97 seconds of wall-clock elapsed time despite the harness
requesting a 420-second subprocess timeout. The reason was not established; do
not claim that this observation met a seven-minute wall-clock bound. Original
logs and the fixture are preserved. The original probe driver is
`/tmp/guildhall-prototype-probe.py`; it is evaluation scaffolding, not part of the
shipped skill or a production execution controller.
