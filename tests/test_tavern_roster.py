"""The tavern mod keeps its own roster; these keep it in step with plugin/agents/."""
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parent.parent
ROSTER = ROOT/'mods/guildhall-tavern/hooks/roster.ts'


def roster_entries():
    source = ROSTER.read_text()
    block = source.split('export const ROSTER', 1)[1].split('\n}\n', 1)[0]
    return dict(re.findall(r"^  '?([a-z][a-z-]*)'?: \{\n\s+name: '([^']+)'", block, re.M))


def character_names():
    names = {}
    for section in (ROOT/'plugin/CHARACTERS.md').read_text().split('\n## ')[1:]:
        agent = re.search(r'^\| \*\*Agent\*\* \| `([a-z-]+)` \|', section, re.M)
        if agent:
            names[agent.group(1)] = section.split()[0]
    return names


class TavernRosterTests(unittest.TestCase):
    def test_every_agent_has_a_seat_in_the_tavern(self):
        agents = {p.stem for p in (ROOT/'plugin/agents').glob('*.md')}
        roster = set(roster_entries())
        self.assertEqual(sorted(agents - roster), [],
                         'agents missing from mods/guildhall-tavern/hooks/roster.ts (they would show as hirelings)')
        self.assertEqual(sorted(roster - agents), [],
                         'roster rows for agents that no longer exist in plugin/agents/')

    def test_roster_names_match_the_character_sheets(self):
        roster = roster_entries()
        for agent, name in character_names().items():
            with self.subTest(agent=agent):
                self.assertEqual(roster.get(agent), name)


if __name__ == '__main__':
    unittest.main()
