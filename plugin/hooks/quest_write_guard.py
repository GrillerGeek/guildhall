#!/usr/bin/env python3
"""PreToolUse hook (matcher: Write): enforce Mordain's plan-file-only Write.

quest.md states the forcing function in prose — Mordain MUST NOT Write anything
but the quest plan file at docs/guildhall/plans/*.md. Prose rules are
probabilistic on long turns; this hook is the deterministic backstop.

Scope, deliberately narrow:
- Fires only while a /quest turn is in flight (flag file set by quest_flag.py).
  Outside quests the hook abstains and normal sessions are untouched.
- Fires only for the MAIN agent. A tool call inside a subagent carries
  `agent_id` in the hook input (per the hooks docs); adventurers' Writes are
  governed by their own tool lists, not by this guard.
- Guards `Write` only. Mordain's Bash access stays a prose rule — quest.md
  already forbids `cat >` workarounds in its non-goals.

On violation, emits a PreToolUse deny decision naming the rule, so Mordain is
steered back to dispatching an adventurer instead of writing the file himself.
Fails open (exit 0) on malformed input — the prose rule remains the fallback.
"""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path, PurePosixPath

PLAN_DIR_PARTS = ("docs", "guildhall", "plans")


def flag_path(session_id: str) -> Path:
    return Path(tempfile.gettempdir()) / f"guildhall-quest-{session_id}"


def is_plan_file(file_path: str) -> bool:
    parts = PurePosixPath(file_path.replace("\\", "/")).parts
    for i in range(len(parts) - len(PLAN_DIR_PARTS)):
        if parts[i : i + len(PLAN_DIR_PARTS)] == PLAN_DIR_PARTS:
            return parts[-1].endswith(".md")
    return False


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, UnicodeDecodeError):
        return 0
    if payload.get("agent_id"):
        return 0  # subagent (an adventurer) — not Mordain's rule
    if not flag_path(payload.get("session_id") or "unknown").exists():
        return 0  # no quest in flight — ordinary session, abstain
    file_path = (payload.get("tool_input") or {}).get("file_path") or ""
    if not file_path or is_plan_file(file_path):
        return 0
    print(
        json.dumps(
            {
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": "deny",
                    "permissionDecisionReason": (
                        "Guildhall write guard: during a /quest, Mordain's Write is "
                        "scoped to the plan file (docs/guildhall/plans/*.md). "
                        f"'{file_path}' is outside that scope — dispatch the right "
                        "adventurer to write it instead."
                    ),
                }
            }
        )
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
