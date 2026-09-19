# Portable execution follow-up — candidate 0.9.1

This report supplements, rather than rewrites, the [0.9.0 assessment](2026-09-19-portability.md).
Work remains on the local `codex/portable-guildhall` branch. No publication,
release or personal Guildhall installation is implied by these observations.

## Changes and decisions

The installed IDD technical-review procedure assigns Spec annotation writes to
its main conversation. Calling it as Guildhall's closing gate conflicts with
Mordain's plan-only write scope. Portable Guildhall now dispatches Aldric in an
explicit post-green technical-review mode: read-only, grounded in the current
Spec, implementation, tests, docs and observed verification. The pre-plan mode
continues to examine open architectural alternatives. The mode distinction
explicitly resolves the old prohibition on reading tests.

Formal IDD technical review remains a separate workflow. Readiness, clean current
gap-check evidence, Boundaries, worker self-verification, recorder ownership and
human/QA lifecycle gates remain required. This portable change does not alter
the native Claude command, agents, hooks or character reference.

An independent reviewer found and helped resolve a circular gate: requiring a
completed Execution Report before the technical review that authorizes report
assembly. Technical review now covers the evidence and contracts for explicitly
pending orchestration outputs. All implementation/tests/docs and verification
must already be complete. The actual report and every Spec Deliverable must
exist and pass the lifecycle finish checks before advancing to review.

The eleven standard readiness criteria are now bundled in lifecycle guidance;
a separate personal IDD installation is not needed to learn them. An independent
check found them consistent with the IDD schema and no broader write scope.

All three manifests are incremented to **0.9.1**. The bundle contains 26 files.
The install probe reads the expected version from the manifest instead of a
hardcoded release number. New opt-in evaluation tooling retains ordinary root
session records, raw file snapshots and honest process receipts. It does not
decode protected worker payloads or label process exit zero as behavioral success.

The feature trial exposed an additional RED wording ambiguity: Python unittest
counts a promised function raising NotImplementedError as an error, while the
old test-author role rejected errors indiscriminately. Portable wording now
separates errors directly witnessing absent promised behavior from broken tests,
fixtures, unrelated dependencies and configuration. It preserves actual error,
failure and pass counts and does not allow reading implementation to guess.
Running the suite after authoring is explicitly distinguished from probing
implementation before tests are written.

## Verified observations

The following three observations used the earlier 0.9.0 bundle. Their execution
paths are unchanged by the feature-only closing-review update. A separate
reviewer recomputed hashes/modes, inspected actual dispatch calls/results and
checked artifact outcomes.

| Scenario | Actual evidence | Result and limits |
|---|---|---|
| Prototype | `spawn_agent` requests `prototype_builder`, `fork_turns: none`; returned `/root/prototype_builder`. | Two greeting assertions pass. All 27 baseline files unchanged; only `hello.py` and plan added. |
| Debug | `spawn_agent` requests `debug_investigator`, `fork_turns: none`; returned `/root/debug_investigator`. | Reproduced actual 6 versus expected 5, identified extra `+ 1`. All 28 baseline files unchanged; only plan added. |
| Missing gate | No spawn call; explicit refusal names missing content, human approval and gap-check evidence. | All 28 baseline files unchanged; zero additions, including no plan. |

Neither dispatch specified a model or reasoning override. These are actual
fresh-context dispatch requests and successful responses, stronger evidence than
the prior ephemeral run's parent assertion. Child prompt contents are protected
and full child records were not exposed; these observations do not establish
complete child read traces, write attribution, model identity or enforced isolation.

Retained evidence lives under:
`/private/var/folders/f0/_sscvrpd48s9srngb0d0l_mh0000gn/T/`

| Directory | Root record SHA-256 | Wall seconds / exit |
|---|---|---|
| `guildhall-prototype-0_wtvdcn` | `b3993f1f2d7671472eeeb7702e9587f0ce81cadb84242ffd6a89c422199b7ada` | 196.583 / 0 |
| `guildhall-debug-4c_n298y` | `e3b892bbd81ba25378e9ebb82cc3fc47649bbd2326aff7fe0c28ba31262fa78a` | 135.541 / 0 |
| `guildhall-missing-gate-9lyszasi` | `d84b7826d41dcb91d5f7ae9eff38c10f341f8644b3b136e80745fcc5be1ef710` | 36.117 / 0 |

Each directory includes `receipt.json`, baseline, stdout, final response, fixture
and copied root session record. Raw records remain local because they can contain
project content. Evidence paths are temporary and are not portable release assets.

## Additional 0.9.1 refusal observations

- **Unavailable delegation:** `guildhall-no-delegation-hbaodrm4`, 25.906 seconds,
  exit 0. The prompt explicitly made independent dispatch unavailable. The agent
  refused before writes rather than simulating workers. Independently recomputed
  all 36 baseline hashes/modes unchanged, zero additions and no spawn call.
  Root record SHA-256:
  `fa317a106745d892e67294331500e0d75a143c46ec4dbf69782c199d3fe01431`.
- **Conflicting execution owner:** `guildhall-owner-conflict-tg6wdzso`, 46.236
  seconds, exit 0. A labeled synthetic active-controller record had no authorized
  handoff. The agent refused before writes; all 37 baseline hashes/modes remain
  unchanged, zero additions and no spawn call. Root record SHA-256:
  `5ff5bbf7abb44e0a04123fd93efa5cd024dbbf4d7bd1d45117fac589013a54c7`.

These verify responses to supplied capability/ownership constraints, not absence
of delegation tools in a different app or integration with a real external lock.
Both explicitly preserved the distinction between mocked readiness and actual
human approval. All copied root record hashes match their receipts.

## Revised RED role observations

Two fresh role-only evaluations used the revised generated test-author contract;
these were not complete feature quests and performed no lifecycle transitions.

- `guildhall-red-runtime-2a6458j4`: 114.534 seconds, exit 0. Actual fresh-context
  `test_author` dispatch, two passes, zero assertion failures, three runtime
  errors from the promised greeting behavior. Correctly classified expected RED.
  Root record SHA-256:
  `250b82f3afe7e413429856d1ebc3e6e62b1cbd21cef4e70b21f4a22004da3bff`.
- `guildhall-red-setup-error-po_k_7_g`: 132.709 seconds, exit 0. Actual fresh-context
  `test_author` dispatch, zero passes, zero assertion failures, four errors. Three
  greeting errors were attributable to promised missing behavior; an unrelated
  missing dependency prevented baseline test discovery and correctly blocked
  verification. Root record SHA-256:
  `4fe9fff0c0f755d20f12a0d77d4f8ce1da17da30b644053a647e53a7a7c055aa`.

Both independently audited snapshots preserve all original files and modes and
add only `tests/test_greetings.py`. Root session hashes match receipts. Neither
dispatch overrides model/effort. The retained records still do not expose a full
child read trace; claims about instructional read restrictions remain limited.

## Feature trial provenance

Feature fixtures explicitly label both readiness and gap-check inputs as
synthetic. No person reviewed or approved the synthetic Spec. The invocation
mocks that prerequisite only; subsequent worker calls, files, tests and lifecycle
operations are real observations. Final human implementation review and QA must
remain pending. A successful synthetic run would not certify live approval checks.

- `guildhall-feature-ad_cy77g`: startup failed because the outer filesystem sandbox
  prevented Codex runtime state/app-server initialization. Exit 1, no fixture edits.
  Reran with the narrowly approved host execution permission; no client settings
  or credentials were changed.
- `guildhall-feature-0498ut4_`: deliberately stopped after the reviewer found the
  circular gate, before using the superseded contract for acceptance. Child exit
  -15, 136.199 seconds, receipt observed no fixture edits. This is interrupted
  evidence, not a pass. The original harness returned shell zero despite child
  failure; the checked-in helper now propagates failure as exit 1.

## Full feature observation and recovery

`guildhall-feature-dv1f02ek` used the corrected closing-review ordering, before
bundling the checklist and revising test-author RED wording. Its first bounded
invocation reached the 900-second deadline (900.223 seconds, child exit -15).
The first retained root record SHA-256 is
`60b3a3a4880558c6ee0105d2d747483260040b115b391d5cb67d3a091e51b95d`.

Before interruption, actual dispatch calls requested fresh contexts for recorder,
test-author, implementer, documentation, security, observability, technical review,
report assembly and PR drafting. Observed RED was two passes, zero assertion
failures and three NotImplementedError errors. The author initially rejected the
classification; the parent paused and obtained read-only clarification from the
same author, retaining the tests and numeric results. This is a run with an
internal classification clarification, not an unassisted test of the later wording.
The separate role probes above exercise that wording directly. The root also
looked up the eleven readiness criteria in a personal IDD installation; the final
bundle now includes them. This interrupted trial is not a clean standalone
execution of the final bundle.

GREEN was five passes, zero errors/failures, with accepted test bytes unchanged.
The parent recorded all selected reviews and a passing closing technical review.
At interruption, the only modified baseline files were the allowed source,
README and exact status-only Spec transition to `in-progress`; new files were
only the tests and quest plan. No report or final lifecycle pass was inferred.

An explicit recovery instruction resumed the same Codex session, requiring
inspection of existing workers, preservation of all evidence and no reset or
repetition of completed phases. Recovery artifacts live in `recovery-1/` inside
the fixture. The one-off recovery driver is `/tmp/guildhall-resume-observation.py`;
it is local evaluation scaffolding, not a shipped skill or automatic recovery
controller. The original deadline receipt remains unchanged. Recovery reported only the
parent active and no saved report/PR draft; it verified reviewed artifact hashes,
five passing tests, four documentation examples and protected files before
replacing only the interrupted output tasks.

The recovered report is
`docs/reviews/SPEC-f101-20260919T230936Z-execution.md`, SHA-256
`7a37e03b049e1d7326298b558c70f2141d868567181cca2c85c626e4d09d1a4e`.
Independent final artifact checks confirm status **review**, exact status-only
Spec bytes, all 33 protected original files unchanged and accepted test hash
`87888f908c9c96da7f4c04005166611ffa6b648b34bbec0052c2aa6c56328db9`.
The report truthfully retains its assembly-time in-progress state; the final
transition is recorded separately in the plan. Human approval/QA remain pending.

Recovery completed with exit **0**, **698.422 seconds**, no stop reason. Retained
full root-session SHA-256:
`072e9b97d9c8fd6da91a03bb71efe5f883d473af4c55c665426914cd05b52ef2`.
An independent reviewer confirmed the actual ownership check returned only the
parent, and fresh recovery-report, PR and final-recorder dispatches succeeded.
The final PR draft is saved in the plan. The only recovery changes were the plan,
status scalar and new report; product/test/docs hashes stayed fixed. Parent
mutation records are plan-only. This supports completed explicit recovery,
without upgrading the trial to clean/unassisted execution or child read isolation.

## Verification boundaries

Packaging/install evidence is distinct from execution evidence. Native Claude
source preservation does not certify native quest execution after adding the
portable entry. Skills installation does not certify another host's delegation,
browser or enforcement features. A clean full-feature run of the final bundle, missing-UI behavior, out-of-scope
writes, retry exhaustion, real ownership integration and additional interruption
points still need targeted observations before broad production certification.

## Mechanical and installation checks

All 16 unit tests pass, including four new evidence/fixture checks. Snapshot
auditing records symlink identity without reading link targets, so replacing a
protected regular file with a same-content symlink is detected. Native agent
validation reports 19 agents, zero errors and zero warnings. Generated drift,
manifest/version agreement, internal resources, Codex plugin schema and skill
schema checks pass. Native agents, commands, hooks and character reference remain
byte-for-byte identical to main `5286df9`; the Claude manifest changes only version.

Final bundle installation receipt: `guildhall-install-vd3eaghx/report.json` under
the temporary evidence parent above. Native Codex installed/enabled version 0.9.1;
standalone Codex and Claude Code copy routes also passed. Every installed byte
and mode matched, including after deleting each fixture source. Earlier 0.9.1
receipts `guildhall-install-uwdp6bew/report.json` and
`guildhall-install-hj0u3ux3/report.json` passed before final protocol edits.
These no-model probes used isolated credential-free home/client profiles.
