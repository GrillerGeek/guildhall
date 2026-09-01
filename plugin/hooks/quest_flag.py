#!/usr/bin/env python3
"""UserPromptSubmit hook: track whether a /quest turn is in flight.

The write-guard hook (quest_write_guard.py) must only constrain Mordain while
a quest is actually running — plugin hooks are live in every session where
Guildhall is enabled, and blocking ordinary Writes outside quests would break
normal use. This hook maintains that "quest in flight" signal:

- A prompt that invokes /quest (bare or plugin-namespaced) creates a flag file
  keyed by session id.
- Any other prompt removes it, so enforcement covers exactly the autonomous
  /quest turn and lapses on the user's next message (back to the prose rule).

Never blocks: always exits 0, even on malformed input.
"""

from __future__ import annotations

import json
import re
import sys

from quest_write_guard import flag_path

QUEST_INVOCATION = re.compile(r"^\s*/(?:guildhall:)?quest\b")


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, UnicodeDecodeError):
        return 0
    prompt = payload.get("prompt") or payload.get("user_prompt") or ""
    flag = flag_path(payload.get("session_id") or "unknown")
    try:
        if QUEST_INVOCATION.match(prompt):
            flag.touch()
        else:
            flag.unlink(missing_ok=True)
    except OSError:
        pass
    return 0


if __name__ == "__main__":
    sys.exit(main())
