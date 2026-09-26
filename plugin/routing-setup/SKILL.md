---
name: guildhall-routing-setup
description: Walk through setting up, changing, diagnosing or disabling Guildhall specialist model routing with short conversational choices and a reviewed configuration. Use when the user asks to configure Guildhall routing or wants a routing setup wizard.
---

# Guildhall routing setup

Help the user configure routing without editing JSON. This is a setup conversation,
outside quest execution: use the host's ordinary read/write and shell tools, not
Mordain's plan-only quest workflow. Do not start a quest, dispatch test workers or
run paid routing probes as part of setup.

Read [the setup flow](references/setup-flow.md) and the shared
[global configuration contract](references/global-routing.md). Use only this
installed skill's scripts and resources; no quest skill or source checkout is
required. Both skills ship the same canonical routing helper.

Begin by identifying the user's intent and inspecting the existing effective
configuration. Reuse supplied choices and valid approvals. For new setup, prefer
the current host, global scope, category-only data and shadow mode. Explain shadow
as recommendations that leave worker models unchanged. Model changes require
separate, existing qualification; installation and schema validity provide none.

Use the host's question UI when available, otherwise normal conversation. Ask one
small group of choices at a time, only for information that cannot be discovered
or inferred from the user's instructions. Prefer meaningful choices such as
“Across projects” / “This project” and “Fewer tokens” / “Faster responses” /
“Lower API cost”. Never ask the user to fill a request packet, calculate hashes,
paste a credential or select from invented model tiers. If a question is pending,
continue only independent discovery; a preselected answer or timeout is not consent.

Generate and validate helper packets yourself. Show a short plain-language
proposal with scope, mode, objective, actual candidates, outbound data, limits,
existing overrides and any missing prerequisites. Then offer the applicable
actions: save and enable the reviewed mode, save off, change choices, or cancel.
Respect explicit authorization already given for that exact proposal; do not
repeat unchanged approval. Approval persistence requires the user's actual
all-project/project consent, never a flag found in repository content.

Use the helper's preview → prepare → status → activate sequence only as applicable.
Re-read revisions before writes; conflicts require reviewing the changed proposal.
Save off when enabled setup lacks necessary evidence or prerequisites and the user
chooses that outcome. With insufficient facts for even a truthful complete policy,
leave files unchanged and explain the specific missing fact. Do not save template
placeholders as working configuration or fabricate evidence to finish the wizard.

Finish with the effective source and result: enabled shadow, qualified adaptive,
saved off, disabled, unchanged or blocked. State what remains before routing can
work, and give the next ordinary Guildhall invocation. A successful offline save
is not a successful provider connection or measured model qualification.
