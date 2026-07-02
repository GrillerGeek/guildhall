#!/usr/bin/env python3
"""Mechanical validator for the Guildhall plugin tree.

Implements plugin-validator's (Tabs') eight checks as CI-runnable code, so the
mirror-consistency guarantees hold on every push instead of only when Tabs is
dispatched. Stdlib only; exits 1 on any error-severity finding, 0 otherwise
(warnings are printed but do not fail the build).

Check list (mirrors plugin/agents/plugin-validator.md):
  1. Manifest well-formedness (plugin.json exists, valid JSON, name/version/
     description present, semver-ish version)
  2. Agent frontmatter completeness (name/description/model/tools; name
     matches filename)
  3. <example> blocks in agent descriptions indented exactly 2 spaces
  4. model: in alias form (sonnet/opus/haiku); full model IDs are warnings
  5. Tool names are known built-ins or mcp__-prefixed; unknown names warn
     (mcp__ names cannot be validated statically -- see ui-test-author history)
  6. Command frontmatter declares allowed-tools
  7. No obvious secrets in the plugin tree
  8. Cross-file tier consistency: agent frontmatter model: is canonical;
     quest.md roster table and plugin/README.md roster mismatches are errors;
     CHARACTERS.md Model rows, plugin.json description groups, and CLAUDE.md
     tier lists are warnings. A surface that does not mention an agent is not
     a finding.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
PLUGIN = REPO / "plugin"

TIER_ALIASES = {"sonnet", "opus", "haiku"}

KNOWN_TOOLS = {
    "Agent", "AskUserQuestion", "Bash", "BashOutput", "Edit", "ExitPlanMode",
    "Glob", "Grep", "KillShell", "LS", "NotebookEdit", "NotebookRead",
    "PowerShell", "Read", "Skill", "SlashCommand", "Task", "TodoWrite",
    "WebFetch", "WebSearch", "Write",
}

SECRET_PATTERNS = [
    re.compile(r"sk-ant-[A-Za-z0-9_\-]{20,}"),
    re.compile(r"ghp_[A-Za-z0-9]{30,}"),
    re.compile(r"github_pat_[A-Za-z0-9_]{20,}"),
    re.compile(r"AKIA[0-9A-Z]{16}"),
    re.compile(r"-----BEGIN (?:RSA|EC|OPENSSH|PGP) PRIVATE KEY-----"),
]

errors: list[str] = []
warnings: list[str] = []


def error(msg: str) -> None:
    errors.append(msg)


def warn(msg: str) -> None:
    warnings.append(msg)


def frontmatter(text: str) -> str | None:
    """Return the raw frontmatter block, or None if the file has none."""
    m = re.match(r"\A---\r?\n(.*?)\r?\n---\r?\n", text, re.DOTALL)
    return m.group(1) if m else None


def fm_field(block: str, field: str) -> str | None:
    """Return a top-level (column-0) frontmatter field's value, or None."""
    m = re.search(rf"^{field}:[ \t]*(.*)$", block, re.MULTILINE)
    return m.group(1).strip() if m else None


def check_1_manifest() -> dict:
    path = PLUGIN / ".claude-plugin" / "plugin.json"
    if not path.exists():
        error(f"check 1: {path.relative_to(REPO)} missing")
        return {}
    try:
        manifest = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        error(f"check 1: plugin.json is not valid JSON ({exc})")
        return {}
    for key in ("name", "version", "description"):
        if key not in manifest:
            error(f"check 1: plugin.json missing required key '{key}'")
    version = manifest.get("version", "")
    if version and not re.fullmatch(r"\d+\.\d+\.\d+", version):
        error(f"check 1: plugin.json version '{version}' is not semver-ish")
    return manifest


def agent_files() -> list[Path]:
    return sorted((PLUGIN / "agents").glob("*.md"))


def checks_2_to_5(agents: dict[str, str]) -> None:
    for path in agent_files():
        rel = path.relative_to(REPO)
        text = path.read_text(encoding="utf-8")
        block = frontmatter(text)
        if block is None:
            error(f"check 2: {rel} has no frontmatter")
            continue

        # Check 2 -- required fields, name matches filename
        for field in ("name", "description", "model", "tools"):
            if fm_field(block, field) is None:
                error(f"check 2: {rel} frontmatter missing '{field}:'")
        name = fm_field(block, "name")
        if name and name != path.stem:
            error(f"check 2: {rel} frontmatter name '{name}' != filename '{path.stem}'")

        # Check 3 -- example indentation exactly 2 spaces
        for line in block.splitlines():
            m = re.match(r"^([ \t]*)</?example>\s*$", line)
            if m and m.group(1) != "  ":
                error(f"check 3: {rel} example tag indented {len(m.group(1))} chars (want 2 spaces): {line.strip()}")

        # Check 4 -- model alias form
        model = fm_field(block, "model")
        if model:
            if model in TIER_ALIASES:
                agents[path.stem] = model
            elif re.match(r"claude-", model):
                warn(f"check 4: {rel} model '{model}' is a full model ID, not an alias")
                agents[path.stem] = model
            else:
                error(f"check 4: {rel} model '{model}' is not sonnet/opus/haiku")

        # Check 5 -- tool names
        tools_raw = fm_field(block, "tools")
        if tools_raw:
            if tools_raw.startswith("["):
                try:
                    tools = json.loads(tools_raw)
                except json.JSONDecodeError:
                    error(f"check 5: {rel} tools list is not parseable JSON")
                    tools = []
            else:
                tools = [t.strip() for t in tools_raw.split(",") if t.strip()]
            for tool in tools:
                if tool not in KNOWN_TOOLS and not tool.startswith("mcp__"):
                    warn(f"check 5: {rel} unknown tool '{tool}'")


def check_6_commands() -> None:
    for path in sorted((PLUGIN / "commands").glob("*.md")):
        rel = path.relative_to(REPO)
        block = frontmatter(path.read_text(encoding="utf-8"))
        if block is None or fm_field(block, "allowed-tools") is None:
            error(f"check 6: {rel} missing 'allowed-tools' frontmatter")


def check_7_secrets() -> None:
    for path in sorted(PLUGIN.rglob("*")):
        if not path.is_file() or path.suffix not in {".md", ".json"}:
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        for pattern in SECRET_PATTERNS:
            for m in pattern.finditer(text):
                error(f"check 7: {path.relative_to(REPO)} contains key-like string '{m.group(0)[:24]}...'")


def check_8_tiers(agents: dict[str, str], manifest: dict) -> None:
    def compare(surface: str, agent: str, found: str, severity) -> None:
        canonical = agents.get(agent)
        if canonical is None:
            severity(f"check 8: {surface} mentions unknown agent '{agent}'")
        elif found.lower() != canonical.lower():
            severity(f"check 8: {surface} says {agent} = {found}, frontmatter says {canonical}")

    # quest.md roster table (error severity)
    quest = (PLUGIN / "commands" / "quest.md").read_text(encoding="utf-8")
    for m in re.finditer(r"^\|[^|]+\|\s*`([a-z0-9-]+)`\s*\|\s*(sonnet|opus|haiku)\s*\|", quest, re.MULTILINE):
        compare("quest.md roster", m.group(1), m.group(2), error)

    # plugin/README.md roster table (error severity)
    readme = (PLUGIN / "README.md").read_text(encoding="utf-8")
    for m in re.finditer(r"^\|[^|]+\|\s*`([a-z0-9-]+)`\s*\|[^|]*\|\s*(Opus|Sonnet|Haiku)\s*\|\s*$", readme, re.MULTILINE):
        compare("plugin/README.md roster", m.group(1), m.group(2), error)

    # CHARACTERS.md sheets (warn severity): an **Agent** row binds the next **Model** row
    characters = (PLUGIN / "CHARACTERS.md").read_text(encoding="utf-8")
    current_agent = None
    for line in characters.splitlines():
        m = re.match(r"^\|\s*\*\*Agent\*\*\s*\|\s*`([a-z0-9-]+)`\s*\|", line)
        if m:
            current_agent = m.group(1)
            continue
        m = re.match(r"^\|\s*\*\*Model\*\*\s*\|\s*(\w+)\s*\|", line)
        if m and current_agent:
            compare("CHARACTERS.md", current_agent, m.group(1), warn)
            current_agent = None

    # plugin.json description tier groups (warn severity)
    description = manifest.get("description", "")
    for m in re.finditer(r"\b(Opus|Sonnet|Haiku)\s*\(([^)]+)\)", description):
        for agent in (a.strip() for a in m.group(2).split(",")):
            if agent in agents:
                compare("plugin.json description", agent, m.group(1), warn)

    # repo-root CLAUDE.md tier lists (warn severity)
    claude_md = REPO / "CLAUDE.md"
    if claude_md.exists():
        for m in re.finditer(r"^- \*\*(Opus|Sonnet|Haiku):\*\*(.*)$", claude_md.read_text(encoding="utf-8"), re.MULTILINE):
            for agent in re.findall(r"`([a-z0-9-]+)`", m.group(2)):
                if agent in agents:
                    compare("CLAUDE.md tier list", agent, m.group(1), warn)


def main() -> int:
    manifest = check_1_manifest()
    agents: dict[str, str] = {}
    checks_2_to_5(agents)
    check_6_commands()
    check_7_secrets()
    check_8_tiers(agents, manifest)

    for msg in errors:
        print(f"ERROR  {msg}")
    for msg in warnings:
        print(f"WARN   {msg}")
    print(f"\n{len(agents)} agents checked: {len(errors)} error(s), {len(warnings)} warning(s)")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
