# Conversational routing setup

- Version: 0.16.0, unreleased.
- Scope: add the user-requested guided setup workflow on top of global routing.
- Skill: `guildhall-routing-setup`; invoke explicitly or ask to set up Guildhall routing.

## Delivered

The skill identifies the current host and configuration, asks only for remaining
scope/objective/profile/mode choices, checks prerequisites, and presents a
plain-language proposal. It uses the existing offline preview/prepare/status/
activate/revoke operations. New setup recommends global scope, category facts and
shadow mode; established settings and explicit user choices take precedence.
Missing evidence or credentials cannot become activation merely by completing
the wizard. Save-off, cancellation, settings changes, diagnosis and disabling
are separate outcomes, with the actual effective source reported at completion.

`plugin/routing-setup/` owns the entry and detailed flow. The builder creates a
complete standalone `plugin/skills/guildhall-routing-setup/` bundle, including the
same canonical routing scripts, schemas, examples and linked guides used by
`guildhall-quest`. It has no sibling quest dependency or role dispatch. Native
plugins include both skills; standalone users can choose either or both.
Build validation checks both destinations before writing, preserving unknown
files and rejecting symlinks. Links cannot escape either installed bundle.

Setup can now target a global/project entry for resolve/status/activate. This
allows global activation while a project override is retained. Targeted calls
still bind the exact source, scope, host and policy; they reject contradictory
session selection. Worker dispatch omits the setup target and keeps ordinary
precedence, including project opt-out. No existing policy or approval schema
changed, and the helper makes no network request.

## Validation

| Check | Result |
|---|---|
| Skill creator quick validation | Passed for the generated setup skill |
| Full suite, Python 3.12.2 | 154 passed |
| Full suite, Python 3.14.5 | 154 passed |
| Native plugin validator | 19 definitions; zero errors/warnings |
| Portable validator | Both skill inventories, internal links, shared-resource drift, schemas and manifests passed |
| Generated bundles | 107 files, no drift |
| Native Codex and native Claude installation | Both skills included; exact bytes/modes and tools after source removal passed |
| Skills 1.5.25 and 1.7.0 | Both skills independently installed for Codex/Claude from explicit bundle paths and repository discovery |

The new standalone test runs setup operations from a copied bundle with isolated
user state and no source/quest dependency. It exercises a side-effect-free preview,
save-off, explicit synthetic shadow activation, revocation and project opt-out.
Other tests cover shared resource identity, rejecting unknown setup outputs
before writing either bundle, and global activation/revocation behind an unchanged
project opt-out. Installer probes require that only the selected skill is copied
in standalone cases, and execute the installed routing tools after source removal.

Retained installer receipts:

- Native hosts plus skills 1.5.25: `guildhall-install-9hw969cl`.
- Skills 1.7.0: `guildhall-install-zctdb5xd`.

## Limits

Validation ran locally on macOS with synthetic evidence and isolated user state.
The conversational instructions were reviewed for branching, authorization,
missing prerequisites, cancellation and masked configuration; no live end-to-end
conversation through a host's question UI was run. Automated tests exercise the
underlying workflow operations and installation, not an agent's future choices.
No paid probes, live model qualification, personal installation, credentials or
host settings were changed. Restart after installing the release to discover the
new skill; setup does not automatically execute during installation.
