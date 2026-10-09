"""Meaningful publication-boundary tests using fictional data only."""
import copy
import importlib.util
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace as Args
import unittest

spec = importlib.util.spec_from_file_location('release_data', Path(__file__).resolve().parents[1] / 'scripts/release-data.py')
tool = importlib.util.module_from_spec(spec)
spec.loader.exec_module(tool)


def entry(rid='DEMO-001', status='approved'):
    e = {'public': {'id': rid, 'name': '虚构目录演示', 'sources': ['https://example.org/source'],
                    'verification': '待核对', 'materials': [], 'stories': []},
         'private': {'contact': 'PRIVATE-SENTINEL', 'receipt': 'PRIVATE-RECEIPT'},
         'media': [], 'review': {'status': status, 'scope': 'directory',
                                 'reviewer': 'fictional-reviewer', 'date': '2026-10-09'}}
    e['review']['content_sha256'] = tool.review_hash(e)
    return e


class PublicationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.base = Path(self.tmp.name)
        self.source = self.base / 'records.json'

    def tearDown(self):
        self.tmp.cleanup()

    def save(self, entries):
        self.source.write_bytes(tool.encoded({'format': 'jiewangyin-private-index-v1',
                                            'updated_at': 'PRIVATE-UPDATE', 'entries': entries}))

    def export(self, name='v1', previous=None):
        dest = self.base / name
        tool.export(Args(source=self.source, output=dest, version=name, previous=previous,
                         media_root=self.base / 'approved', volume_mb=1))
        return dest

    def test_private_and_unapproved_content_never_export(self):
        hidden = entry('DEMO-002', 'pending')
        hidden['public']['name'] = 'PENDING-SENTINEL'
        self.save([entry(), hidden])
        out = self.export()
        joined = b''.join(p.read_bytes() for p in out.rglob('*') if p.is_file())
        for secret in [b'PRIVATE-SENTINEL', b'PRIVATE-RECEIPT', b'PENDING-SENTINEL', b'PRIVATE-UPDATE', b'fictional-reviewer']:
            self.assertNotIn(secret, joined)
        tool.verify(Args(directory=out))
        self.assertEqual(len(tool.read_json(out / 'source-catalog.json')['institutions']), 1)

    def test_changed_approval_and_unknown_fields_fail_atomically(self):
        for mutate in [lambda e: e['public'].update(name='Changed'),
                       lambda e: e['public'].update(contact='PRIVATE-SENTINEL')]:
            e = entry(); mutate(e); self.save([e])
            with self.assertRaises(ValueError): self.export()
            self.assertFalse((self.base / 'v1').exists())
        e['review']['content_sha256'] = tool.review_hash(e); self.save([e])
        with self.assertRaises(ValueError): self.export()

    def test_reproducibility_withdrawal_and_full_snapshot(self):
        self.save([entry(), entry('DEMO-002')]); first = self.export()
        self.export('v2')
        tool.export(Args(source=self.source, output=self.base / 'same-version', version='v1', previous=None,
                         media_root=None, volume_mb=1))
        a = {p.relative_to(first): p.read_bytes() for p in first.rglob('*') if p.is_file()}
        b = {p.relative_to(self.base / 'same-version'): p.read_bytes() for p in (self.base / 'same-version').rglob('*') if p.is_file()}
        self.assertEqual(a, b)
        changed = entry(); changed['public']['summary'] = '更正后的摘要'
        changed['review']['content_sha256'] = tool.review_hash(changed)
        self.save([changed, entry('DEMO-002', 'withdrawn')])
        latest = self.export('v3', first)
        changes = tool.read_json(latest / 'changes.json')
        self.assertEqual(changes['changed'], ['DEMO-001'])
        self.assertEqual(changes['removed'], ['DEMO-002'])
        self.assertEqual(len(tool.read_json(latest / 'source-catalog.json')['institutions']), 1)

    def test_duplicate_ids_and_destination_overwrite_rejected(self):
        self.save([entry(), entry()])
        with self.assertRaises(ValueError): self.export()
        self.save([entry()]); out = self.export()
        with self.assertRaises(ValueError): self.export()
        self.assertTrue(out.is_dir())

    def test_seed_requires_explicit_public_acceptance_and_approve_binds_new_content(self):
        public = self.base / 'public.json'
        public.write_bytes(tool.encoded({'format': 'jiewangyin-source-catalog-v1',
                                        'institutions': [entry()['public']]}))
        args = Args(destination=self.base / 'seed', from_public=public,
                    accept_existing_public=False, date='2026-10-09')
        with self.assertRaises(ValueError): tool.init(args)
        self.assertFalse((self.base / 'seed').exists())
        args.accept_existing_public = True; tool.init(args)
        seeded = tool.read_json(self.base / 'seed' / 'records.json')
        self.assertEqual(seeded['entries'][0]['private'], {})
        e = entry(status='pending'); e['public']['name'] = '重新核对后的虚构内容'
        self.save([e])
        tool.approve(Args(source=self.source, id='DEMO-001', reviewer='human', date='2026-10-10'))
        self.export()

    def test_oversized_media_is_not_silently_byte_split(self):
        m = self.media()
        payload = b'X' * (1024 * 1024)
        (self.base / 'approved' / 'clip.mp4').write_bytes(payload)
        m.update(bytes=len(payload), sha256=tool.digest(payload))
        e = entry(); e['media'] = [m]; e['review']['content_sha256'] = tool.review_hash(e)
        self.save([e])
        with self.assertRaises(ValueError): self.export()
        self.assertFalse((self.base / 'v1').exists())

    def media(self):
        root = self.base / 'approved'; root.mkdir()
        payload = b'Fictional video bytes, not a real recording'
        (root / 'clip.mp4').write_bytes(payload)
        return {'id': 'DEMO-MEDIA-001', 'title': '虚构媒体流程测试',
                'source_url': 'https://example.org/source', 'rights': 'fictional test permission',
                'redistribution': 'allowed', 'privacy_reviewed': True, 'sha256': tool.digest(payload),
                'bytes': len(payload), 'storage_relative': 'clip.mp4', 'mirrors': []}

    def test_media_hash_permission_path_and_symlink_boundaries(self):
        m = self.media(); base = entry(); base['media'] = [m]
        base['review']['content_sha256'] = tool.review_hash(base)
        self.save([base]); out = self.export()
        manifest = tool.read_json(out / 'media-index.json')['media'][0]
        self.assertNotIn('storage_relative', manifest)
        self.assertTrue((out / manifest['package']).is_file())
        for bad in [{'sha256': '0' * 64}, {'redistribution': 'display-only'},
                    {'storage_relative': '../clip.mp4'}, {'privacy_reviewed': False},
                    {'mirrors': ['https://example.org/v?token=SECRET']}]:
            e = copy.deepcopy(base); e['media'][0].update(bad)
            e['review']['content_sha256'] = tool.review_hash(e); self.save([e])
            with self.assertRaises(ValueError): self.export('bad')
            self.assertFalse((self.base / 'bad').exists())
        (self.base / 'approved' / 'clip.mp4').unlink()
        (self.base / 'approved' / 'clip.mp4').symlink_to(out / manifest['path'])
        self.save([base])
        with self.assertRaises(ValueError): self.export('linked')

    def test_verifier_detects_tamper_extra_file_and_formula_safety(self):
        e = entry(); e['public']['name'] = '=HYPERLINK("https://example.org")'
        e['review']['content_sha256'] = tool.review_hash(e); self.save([e])
        out = self.export()
        self.assertIn("'=HYPERLINK", (out / 'source-catalog.csv').read_text(encoding='utf-8-sig'))
        extra = out / 'unexpected.txt'; extra.write_text('extra')
        with self.assertRaises(ValueError): tool.verify(Args(directory=out))
        extra.unlink()
        (out / 'source-catalog.json').write_text('{}')
        with self.assertRaises(ValueError): tool.verify(Args(directory=out))


if __name__ == '__main__':
    unittest.main()
