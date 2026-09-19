# Contributing to Guildhall

Guildhall orchestrates independent specialists through a sequential TDD build,
independent post-green reviews and a final PR draft. Mordain stays in the main
conversation. Preserve the characters, contracts and explicit handoffs.

Read `docs/contributing-agents.md` for ownership and checks. `CLAUDE.md` adds
Claude-specific dispatch, model and hook guidance; its aliases and tool names
are not universal host requirements. Historical design notes are evidence of
past decisions, not instructions to override the current user.

Do not run a quest merely to maintain this repository. A user-requested quest
loads the quest workflow. Repository assessment, packaging and documentation
work can proceed directly within the user's requested scope.

- Keep test-author separate from implementation context; never parallelize the
  RED → GREEN → conditional refactor chain.
- Keep Mordain's edits limited to the quest plan during quest execution.
- Parallelize only independent reviewers with disjoint write scopes; capacity
  limits can require batches, but must not drop a required review.
- Preserve the existing Claude `/quest`, nineteen agent definitions, model
  aliases and hooks when adding another host. Do not claim hook equivalence.
- Treat model names as host configuration, not transferable quality tiers.
- Honor the consuming project's guidance and IDD lifecycle, when applicable.
- Do not publish, install globally or change external marketplaces merely to
  test packaging. Use isolated fixtures.
