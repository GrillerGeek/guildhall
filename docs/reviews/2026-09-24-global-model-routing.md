# Global model routing implementation

- Date: 2026-09-24.
- Branch: `GlobalRouting`, fast-forwarded from `2e5ad08` to the locally available
  routing baseline `0abca43` before implementation. The original plan was retained.
  Before PR creation, refreshed to merged `main` at `1c25444` and reran both
  interpreter suites and repository validators, retaining the new Codex adapter.
- Package version: 0.15.0, unreleased; all three manifests agree.
- Scope: [global specialist-routing plan](../plans/2026-09-24-global-model-routing.md).

## Delivered behavior

The installed `routing_config.py` resolves session selection, a complete project
policy/opt-out, then the current host's global policy. Global configuration uses
absolute XDG_CONFIG_HOME or `~/.config/guildhall/`. Native Claude, standalone
Claude and Codex have separate entries. Projects without configuration inherit
without creating files. Policy v1–v4 remains compatible; overrides replace the
whole policy rather than merging candidate or qualification data.

The separate approval store binds source, scope, policy hash, host configuration
fingerprint and reviewed evidence references. Global approval survives sessions
and projects; project copies do not inherit it. Configuration changes, expiry,
missing reviewed host evidence and revocation invalidate reuse. Summary approval
remains transient and exact-text-specific. Configuration-ready status is not
adaptive qualification. The existing engine still performs task eligibility,
qualification, baseline, budget and failure-state checks.

Offline resolve/status/preview/prepare/activate/revoke operations ship in the
generated bundle. Writes use restrictive permissions, exclusive locks, revision
checks and atomic replacement. Preparation and migration never activate or delete
a project file. No secret value or quest counter is stored globally. Updated
native/portable instructions resolve settings at each worker boundary while
preserving Mordain's plan-only scope and the no-Python absent/off path.

The installed guide documents setup packets, migration, source precedence and
the changed deletion behavior: deleting a project policy restores inheritance;
an explicit off marker disables it.

## Validation evidence

| Check | Result |
|---|---|
| Full unit suite, Python 3.12.2 | 149 passed on refreshed main |
| Full unit suite, Python 3.14.5 | 149 passed on refreshed main |
| New configuration regression tests | 22 passed, including all host routes and all 18 specialist roles |
| Native plugin validator | 19 definitions; zero errors or warnings |
| Portable validator | Schemas, examples, generated resources, links and manifests passed |
| Generated bundle drift | 65 files, no drift on refreshed main |
| Isolated native Codex installation | Installed/enabled; exact bytes/modes; installed tools after source removal passed |
| Isolated native Claude installation | Project installation/enabled; exact bytes/modes; installed tools after source removal passed |
| Pinned skills installer 1.5.25 | Codex/Claude explicit bundle and repository-root discovery passed |
| Additional installed skills version 1.7.0 | Same installation checks passed; documented pin unchanged |
| Whitespace validation | Passed |

The copied native and standalone bundles exercise preview, preparation, explicit
synthetic approval, fresh-session inheritance in two projects, project opt-out
and revocation. Routing through the copied engine after revocation makes zero
transport calls and preserves the existing quest call count. Other regressions
cover stale previews, concurrent-write conflicts, corrupt/unsafe state, symlinks,
unknown hosts, duplicate/null JSON, unsupported runtime, semantic policy errors,
host drift, summary approval and unqualified adaptive fallback.

Installation receipts were retained in isolated temporary directories:

- Native Codex: `guildhall-install-g6hjrv4q`.
- Native Claude: `guildhall-install-w4z0dvs1`.
- Skills 1.5.25: `guildhall-install-_7l1kma7`.
- Skills 1.7.0: `guildhall-install-4iuvaigm`.

## Limits and remaining release work

Checks ran locally on macOS, with synthetic policies, fake transport and supplied
host evidence. They establish configuration, approval and packaging behavior;
they do not qualify a live model or certify actual served-model identity. No
paid Jev request or live worker study was run. No personal global installation,
approval, host setting, credential or external marketplace was changed.

The host adapter remains an instruction-based integration, as in existing
Guildhall routing. It must supply current truthful host evidence, preserve quest
state, record explicit user consent and honor off-path behavior. The helper
checks evidence references, not the truth of underlying records. The local
approval store is not protection against a compromised user account.

The implementation is prepared for PR review. PR creation does not merge or
publish a release, or enable routing in the user's installed plugin. After
release/install, restart the host and perform global setup once per host.
