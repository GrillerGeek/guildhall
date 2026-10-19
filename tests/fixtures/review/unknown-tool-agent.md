---
name: unknown-tool-fixture
description: Synthetic validator fixture preserving unknown-tool diagnostics.
model: sonnet
tools: Read, UnrecognizedFixtureTool
---

This is an isolated packaging fixture, never a production agent.

<example>
Context: Packaging validation must identify an unknown synthetic tool.
user: "Validate this fixture."
assistant: "The validator should report the unknown tool."
</example>
