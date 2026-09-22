# Jev routing verification — 2026-09-21

Version 0.10.0 is a release candidate. This report records evidence supplied by
the implementation coordinator against clean baseline `c73a887`, including
untracked routing resources and tests. The [quest plan](../guildhall/plans/2026-09-21-jev-routing.md)
contains the accepted test hashes and complete initial GREEN file snapshot.
The [approved prose specification](../plans/2026-09-21-jev-assisted-routing.md)
is the non-IDD input; no IDD approval or lifecycle state is asserted.

## Independent tests and initial GREEN

The independent test author wrote 54 new acceptance cases before implementation,
without implementation reads. The coordinator witnessed initial RED: 70 tests,
16 baseline passes and 54 errors caused by the missing promised routing/evaluator
modules and generated helper. These were missing-deliverable import errors, not
assertion failures mislabeled as expected behavior.

A subsequent independent supplement added three numerical-overflow tests.
Their RED run had four assertion failures across subtests and zero errors:
nonfinite aggregate results were accepted, and the CLI failed to sanitize its
error exit. The implementer preserved the accepted tests.

The coordinator's initial GREEN run passed **73 tests**, zero failures/errors,
with all five accepted test-file hashes intact. The portable builder checked
32 files with zero drift. Native validation checked 19 agents with zero
errors/warnings. Portable validation and whitespace checks passed. These are
offline code/package checks; they do not prove live host model control.

## Corrected runtime and final verification

Independent review identified request rejection resetting prior quest state.
The corrected helper preserves independently valid incoming state on rejection;
missing or invalid state produces a hold with provider failure and adaptive
suspension set, while the adapter retains its last trusted state. Four additional
regression tests bring the suite to **77 passing tests**, zero failures/errors,
independently verified by the coordinator in 1.845 seconds.

All validators passed again, and the generated bundle remained **32 files with
zero drift**. Documentation also clarifies the timeout boundary: the parent
watchdog bounds the HTTP child's attempt, but OS process creation and final
reaping can exceed that budget. It is not an absolute wall-clock return guarantee.

Security, reliability, observability and performance reviews reported zero
findings on the reviewed result. Operations review reported no blocker. Closing
technical and plugin-validator review outcomes are recorded in the quest plan.

## Synthetic evaluation

The coordinator independently checked `scripts/evaluate_routing.py --demo`:
32 synthetic fixtures × two repeats × three strategies produced 48 development
and 144 holdout records across docs and PR scopes. The strategies are static,
deterministic and Jev-labeled arithmetic inputs. Output retains
`synthetic: true` and `qualification: false`.

These are invented demonstration measurements, not observed Jev responses,
completed model tasks, savings or quality results. Held-out comparisons and the
10% objective gate exercise the analyzer only. No profile is qualified by them.

## Isolated installation

The coordinator's initial installation checks passed all ten cases: native
Codex and Claude, plus explicit-bundle and repository-root skill copies for both
hosts at installer 1.5.25 and 1.7.0. The latter was checked against the npm latest
version at test time. Installed bytes/modes matched, including after source
removal. No models were run and no personal installation was changed.

Initial local receipts:

- `/private/var/folders/f0/_sscvrpd48s9srngb0d0l_mh0000gn/T/guildhall-install-x0enlquo/report.json`
- `/private/var/folders/f0/_sscvrpd48s9srngb0d0l_mh0000gn/T/guildhall-install-q6__65a8/report.json`

These receipts describe the initial snapshot. The coordinator then repeated all
ten installation cases against the corrected runtime; all passed with exact
installed bytes/modes and source-removal verification. Final local receipts:

- Native Codex, native Claude and four standalone copy routes with skills 1.5.25:
  `/private/var/folders/f0/_sscvrpd48s9srngb0d0l_mh0000gn/T/guildhall-install-07f2eb3o/report.json`
- Four standalone copy routes with skills 1.7.0:
  `/private/var/folders/f0/_sscvrpd48s9srngb0d0l_mh0000gn/T/guildhall-install-wa7c8035/report.json`

Both final reports were readable when this report was updated. These are local
fixture receipts, not published GitHub installation evidence for 0.10.0.

## Documented smoke check

The coordinator ran the exact [documented off-mode smoke command](../model-routing.md#safe-offline-smoke-check)
against the native Codex installed 0.10.0 skill under the first final receipt's
temporary tree, using Python 3.12.2. It exited 0 with `status: "dispatch"`,
`reason: "router_disabled"`, null model/effort dispatch arguments, `calls_used: 0`
and observed model/effort `unknown`. No external call or worker dispatch occurred.
This establishes the installed helper's off path, not live host model control.
The coordinator also checked local file links across all nine changed
documentation surfaces; all passed.

## Remaining limits

No `TYPESAFE_API_KEY` was used; live Jev requests and live host/model
qualification were not run. The release ships no approved model catalog or
qualified profiles. Router selector/version support, confidence calibration,
real task quality and measured total cost/latency remain to be evaluated.
Requested model settings and model-echo self-reports do not prove execution
identity. Unknown host observation and billing remain unknown.

Closing technical and plugin-validator review outcomes are recorded in the quest
plan. The corrected runtime tests and installation reverification above are complete.
No release, tag, marketplace update or personal installation is implied by this
report. Ordinary Guildhall remains available with routing off.
