# Changelog

## 0.11.0 — Unreleased

- Add offline, scoped subscription-usage normalization with replay and retry accounting.
- Add explicit routing schema v2 for role/category measurement facts; retain v1.
- Ship subscription setup and unknown-cost examples without fabricated billing.

## 0.10.1 — Unreleased

- Bundle the routing guide and evaluator for standalone installations.
- Enforce Python 3.12 before routing requests, preserving trusted quest state.
- Replace policy candidate IDs with opaque transport labels.
- Verify installed tools and links after source removal.

## 0.10.0 — Unreleased

- Add optional Jev-assisted specialist model routing through one bundled helper
  shared by native Claude and portable Claude/Codex. Off is the default; shadow
  retains baseline dispatch and adaptive is limited to evaluated docs/PR roles.
- Add strict policy/request schemas, off-mode examples, explicit activation,
  host/profile evidence checks, bounded requests, per-quest failure state and
  decision receipts. User selections retain precedence within host constraints.
- Add an offline evaluator comparing static, deterministic and Jev records per
  role/category. Synthetic results never qualify profiles or enable routing.
- Correct model-echo guidance: self-report is a diagnostic hint, not proof of
  executed model, routing precedence or cost. Frontmatter tiers remain defaults.
- Document setup, data sharing, fallback and disabling. Enabled routing requires
  Python 3.12+ and external calls need the host's `TYPESAFE_API_KEY`; ordinary
  off-mode dispatch remains independent of Jev and the routing runtime.

No live-qualified profile, measured savings or live Jev/host qualification ships
with this release. See the [verification report](docs/reviews/2026-09-21-jev-routing.md)
for offline tests, installation evidence and remaining limits. This candidate
becomes available through the repository's `main` installation routes after merge;
the separate external marketplace is not updated here.
