"""Packaging invariants; these do not certify live model behavior."""
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0,str(ROOT/'scripts'))
from build_portable import build, outputs, DEST
from validate_portable import validate


class PortableTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix='guildhall bundle ')
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        for p in ['plugin','.agents','.claude-plugin']:
            shutil.copytree(ROOT/p,self.root/p)
        shutil.copy2(ROOT/'LICENSE',self.root/'LICENSE')

    def test_rebuild_is_idempotent_and_complete(self):
        self.assertEqual(build(self.root),0)
        validate(self.root)
        self.assertEqual(len(list((self.root/DEST/'references/roles').glob('*.md'))),19)

    def test_copied_bundle_has_no_source_dependency(self):
        bundle = self.root/DEST
        saved = {p.relative_to(bundle):p.read_bytes() for p in bundle.rglob('*') if p.is_file()}
        target = self.root/'installed'
        shutil.copytree(bundle,target)
        shutil.rmtree(self.root/'plugin')
        self.assertEqual(saved,{p.relative_to(target):p.read_bytes() for p in target.rglob('*') if p.is_file()})
        self.assertTrue((target/'references/roles/test-author.md').is_file())

    def test_source_change_requires_rebuild(self):
        p = self.root/'plugin/agents/test-author.md'
        p.write_text(p.read_text()+'\nA changed role contract.\n')
        with self.assertRaisesRegex(ValueError,'Generated drift'):
            build(self.root,check=True)
        self.assertGreater(build(self.root),0)
        validate(self.root)

    def test_unknown_file_refuses_before_any_write(self):
        p = self.root/DEST/'personal-notes.md';p.write_text('keep this')
        source = self.root/'plugin/portable/SKILL.md';source.write_text(source.read_text()+'\nchanged\n')
        before = (self.root/DEST/'SKILL.md').read_bytes()
        with self.assertRaisesRegex(ValueError,'unknown output'):
            build(self.root)
        self.assertEqual((self.root/DEST/'SKILL.md').read_bytes(),before)
        self.assertEqual(p.read_text(),'keep this')

    def test_output_symlink_refuses(self):
        p = self.root/DEST/'SKILL.md';p.unlink();p.symlink_to(self.root/'LICENSE')
        with self.assertRaisesRegex(ValueError,'symlink'):
            build(self.root)

    def test_output_parent_symlink_refuses(self):
        skills = self.root/'plugin/skills';skills.rename(self.root/'saved-skills');skills.symlink_to(self.root/'saved-skills',target_is_directory=True)
        with self.assertRaisesRegex(ValueError,'symlink'):
            build(self.root)

    def test_each_manifest_version_mismatch_refuses(self):
        for rel in ['plugin/plugin.json','plugin/.codex-plugin/plugin.json','plugin/.claude-plugin/plugin.json']:
            p=self.root/rel; original=p.read_text();m=json.loads(original);m['version']='9.9.9';p.write_text(json.dumps(m))
            with self.assertRaisesRegex(ValueError,'disagreement: version'):
                validate(self.root)
            p.write_text(original)

    def test_escaping_catalog_refuses(self):
        p=self.root/'.agents/plugins/marketplace.json';m=json.loads(p.read_text());m['plugins'][0]['source']['path']='../outside';p.write_text(json.dumps(m))
        with self.assertRaisesRegex(ValueError,'repository-owned'):
            validate(self.root)

    def test_broken_reference_is_detected_after_build(self):
        p=self.root/'plugin/portable/SKILL.md';p.write_text(p.read_text()+'\n[missing](references/missing.md)\n');build(self.root)
        with self.assertRaisesRegex(ValueError,'missing/escaped'):
            validate(self.root)

    def test_source_directory_symlink_refuses(self):
        source=self.root/'plugin/portable';source.rename(self.root/'saved-portable');source.symlink_to(self.root/'saved-portable',target_is_directory=True)
        with self.assertRaisesRegex(ValueError,'source directory'):
            build(self.root)

    def test_escaped_resource_reference_refuses(self):
        p=self.root/'plugin/portable/SKILL.md';p.write_text(p.read_text()+'\n[escape](../../../CHARACTERS.md)\n');build(self.root)
        with self.assertRaisesRegex(ValueError,'missing/escaped'):
            validate(self.root)

    def test_agent_inventory_change_requires_review(self):
        (self.root/'plugin/agents/refactorer.md').unlink()
        with self.assertRaisesRegex(ValueError,'inventory'):
            build(self.root)


if __name__ == '__main__':
    unittest.main()
