#!/usr/bin/env python3
"""PostToolUse hook: run validate_plugin.py after any edit under plugin/.

Claude Code invokes this after Write/Edit tool calls (see .claude/settings.json),
piping the hook payload as JSON on stdin. Edits outside plugin/ exit 0 silently.
An edit under plugin/ runs the nine-check validator; on failure this exits 2
with the findings on stderr, which Claude Code feeds back to the model — so a
broken block scalar or roster-table drift surfaces at edit time, not CI time.

Never blocks on its own malfunction: malformed input or unresolvable paths
exit 0 rather than vetoing the edit.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, UnicodeDecodeError):
        return 0
    tool_input = payload.get("tool_input") or {}
    file_path = tool_input.get("file_path") or ""
    if not file_path:
        return 0
    try:
        rel = Path(file_path).resolve().relative_to(REPO)
    except (ValueError, OSError):
        return 0
    if rel.parts[:1] != ("plugin",):
        return 0

    proc = subprocess.run(
        [sys.executable, str(REPO / "scripts" / "validate_plugin.py")],
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        sys.stderr.write(f"plugin validator failed after edit to {rel}:\n")
        sys.stderr.write(proc.stdout)
        sys.stderr.write(proc.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
