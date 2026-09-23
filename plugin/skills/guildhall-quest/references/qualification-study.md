# Run a bounded routing study

Guildhall supplies a development headroom analyzer and a study controller. They
run no models themselves. The controller prepares isolated Git worktrees and
explicit dispatch packets for the actual host, then imports measured outcomes
and independent grading. This avoids substituting CLI workers for a desktop
host merely because its worker tool is unavailable to a Python process.

Start with [host preflight](host-evidence.md). A study needs an explicitly approved
host/candidate scope and usage/time budget. No helper grants that approval. The
[example manifest](../resources/examples/study-manifest.json) is synthetic and
cannot qualify profiles. Replace fixture prompts, rubrics, allowed files, host
requirements, candidate settings and baselines with reviewed project fixtures.
Retain the original role contracts and fresh-context restrictions when dispatching.

## Freeze the study before running it

The manifest fixes the objective, development/holdout split, candidates, static
baseline, per-fixture deterministic baseline, repeats, host/evidence requirements,
router overhead, noise tolerance and budgets. Its hash binds subsequent phases.
Changing objectives or fixtures requires a new study; do not tune on holdout.
At least three development fixtures per role/category and two repeats are needed
for a headroom conclusion. This is a minimum diagnostic coverage rule, not a
statistical guarantee of generalization.

`max_runs` covers the entire planned development matrix plus three holdout
strategies. The host-token budget carries development consumption into holdout;
unknown consumption stops subsequent claims. Timeout is per assignment. The host
must enforce packet budgets: the controller cannot kill a native worker or
prevent a tool call after a host timeout. It records budget overruns as violations.
The two token meters remain separate; host-usage router overhead is 0 or unknown,
not Jev tokens relabeled as subscription consumption. Router latency/cost overhead
must be supplied for those objectives, or headroom is inconclusive.

## Prepare development runs

Use a clean committed fixture repository and a new directory outside it. The
controller creates one detached worktree per candidate/fixture/repeat and shuffles
run order using the frozen seed. Runs are claimed sequentially, avoiding accidental
concurrency interference; this does not eliminate caching or timing noise.

```sh
python3 "$GUILDHALL_SKILL_ROOT/scripts/study_runner.py" prepare \
  --manifest study-manifest.json --repo /absolute/fixture-repo \
  --directory /absolute/new-development-study
```

The controller may read `study.json` to select pending run IDs. Do not give that
file, candidate settings or strategy metadata to the independent grader. A partial
preparation is retained for explicit recovery; there is no automatic cleanup.

```sh
python3 "$GUILDHALL_SKILL_ROOT/scripts/study_runner.py" claim \
  --directory /absolute/development-study --run RUN_ID
```

A claim is persisted before the dispatch packet is returned. Dispatch once through
the approved actual worker tool, preserving the full role contract and permitted
handoff. A running claim is never returned a second time: a lost response or
interruption needs an explicit recovery decision, not automatic model replay.
Resume means continuing known pending work or recording the existing worker's
actual result. No extra retries are authorized by the controller.

## Record results and grade independently

Save a reviewed outcome object with exactly these fields:

- `worker_id`, `evidence` references and `output` text;
- measured `elapsed_ms`, `usage_tokens`, `cost_usd` (unknown values are null);
- `status`: completed/interrupted/failed and actual `retries`;
- `host_report`: the capture helper report, or null for a synthetic test.

Live records with missing/mismatched host evidence receive a violation. The report
must match the worker, role/category, requested settings, host revision/build and
required evidence level. Evidence hashes still require independent review; they
are not authentication. Use fully correlated records, not the final response's
usage or a worker's claim about its model. Do not count first-to-last assistant
message time as whole-assignment elapsed time when it omits the initial request.

```sh
python3 "$GUILDHALL_SKILL_ROOT/scripts/study_runner.py" record \
  --directory /absolute/development-study --run RUN_ID --input outcome.json
python3 "$GUILDHALL_SKILL_ROOT/scripts/study_runner.py" blind \
  --directory /absolute/development-study > grading-packets.json
```

The controller records actual changed paths, including ignored files, modes and
content hashes. It checks allowed-file boundaries, baseline HEAD and worktree Git
metadata. This is change detection inside the worktree, not an OS sandbox or proof
that a worker touched nothing elsewhere; use the host's existing permissions.
It refuses parent-symlink escapes and caps artifact data. Text artifacts are
included in grading packets; unsupported binary artifacts need a separate review
procedure and cannot be silently graded through this text-only pilot.

Blind packets contain a random ID, fixture task/rubric, actual changed artifacts
and output. Explicit model selectors in this material cause refusal instead of
silent rewriting. Author identity-neutral fixtures; stylistic clues cannot be
eliminated completely. An independent grader must not inspect controller metadata.
Grade with `{blind_id, accepted, critical_misses, reason}` entries in a JSON array:

```sh
python3 "$GUILDHALL_SKILL_ROOT/scripts/study_runner.py" grade \
  --directory /absolute/development-study --input grades.json
python3 "$GUILDHALL_SKILL_ROOT/scripts/study_runner.py" export \
  --directory /absolute/development-study > development-records.json
```

Grades are write-once. Changes to recorded artifacts invalidate the snapshot.
Controller restrictions are workflow checks, not separate per-grader OS permissions.
All expected runs and grades are required before export. Failed/interrupted work
stays visible; it is not dropped to improve the score.

## Check headroom before holdout

The analyzer consumes `{manifest, observations}`; exported development records
provide `observations`. The [synthetic packet](../resources/examples/headroom-packet.json)
shows the full input and can be run offline:

```sh
python3 "$GUILDHALL_SKILL_ROOT/scripts/routing_study.py" < headroom-packet.json
```

It requires the development candidate matrix, rather than inferring untried model
performance from three strategy records. Results distinguish insufficient or noisy
measurements, no measured headroom, and observed headroom. Baseline quality failures
are inconclusive. Analysis compares acceptable per-fixture choices plus overhead
against both baselines, so conditional routing can show opportunity even if no
single candidate wins everywhere. The best fixed candidate is also reported.

`no_measured_headroom` stops this study before holdout. It means no prespecified
improvement was measured in the tested scopes/candidates, not that Jev failed or
the baseline is globally optimal. A promising development result also does not
qualify anything; holdout and independent review remain necessary.

## Prepare held-out runs

```sh
python3 "$GUILDHALL_SKILL_ROOT/scripts/study_runner.py" prepare \
  --manifest study-manifest.json --repo /absolute/fixture-repo \
  --directory /absolute/new-holdout-study --phase holdout \
  --input development-records.json
```

Every held-out role/category must have measured development headroom under the
same manifest hash. The controller prepares static, deterministic and Jev runs.
For first-time qualification, use an approved **shadow** policy with candidate IDs
matching the manifest. Take its successful Jev recommendation, then explicitly
select that candidate through the helper's `selection.user_candidate` override
under the same request/policy. Study approval must authorize this bounded selection;
ordinary shadow quests still dispatch their baseline. Save the override decision
with an added `study_recommendation` field containing the original shadow envelope.
The controller checks matching recommendation, policy, task and host. No fabricated
qualification is needed. For already qualified adaptive policies, save the normal
`source: jev` dispatch envelope instead.

Before claiming a Jev run, save this actual decision envelope. Its dispatched settings must match one
of the study candidates; a recommendation in shadow is not the dispatched model.

```sh
python3 "$GUILDHALL_SKILL_ROOT/scripts/study_runner.py" select \
  --directory /absolute/holdout-study --run RUN_ID --input routing-decision.json
```

The controller records the decision hash; it does not itself authenticate policy
activation. Use the router's usual consent, scope, budget and fallback checks. Record elapsed
time across routing plus worker execution and separately retain router meter
evidence; monetary totals include known router charges, while host tokens exclude
Jev tokens. Missing overhead measurements stay unknown.
Then claim, dispatch, record, blind-grade and export as above. Complete holdout
exports are evaluator-format records. Missing elapsed measurements remain an
explicit incomplete export; never fill gaps with zero.

```sh
python3 "$GUILDHALL_SKILL_ROOT/scripts/evaluate_routing.py" < holdout-records.json
```

Held-out reports retain quality and 10% improvement gates, now with explicit
quality/missing-measurement/efficiency reason codes. They always retain
`qualification: false`. Independently review results before creating qualification
and renewing policy activation. All study files/worktrees remain owned evidence;
cleanup and any ambiguous recovery are deliberate operator actions.
