"""Regression tests for published-release ZIP recovery; deliberately offline."""
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'scripts'))
from verify_release_source import choose_release, verify_downloaded

REPO = 'vhick/MEGAsync-Community-PortableApps-Builder'
SHA = '650c9a2df326d7bf28d64e9f6e1588998757a862'
RUN_ID = '44997000086'
TAG = f'mega-portable-v6.7.1.0-b1r14-{SHA}'
ZIP_NAME = 'MEGAsyncPortable_6.7.1.0_b1r14_x64.zip'


def metadata(digest=None):
    return {
        'tag_name':TAG, 'draft':False, 'prerelease':False,
        'html_url': f'https://github.com/{REPO}/releases/tag/{TAG}',
        'body': f'Builder run: https://github.com/{REPO}/actions/runs/{RUN_ID}',
        'assets': [
            {'name':ZIP_NAME,'id':321,'state':'uploaded','size':123450,
             'digest':digest},
            {'name':'SHA256SUMS.txt','id':322,'state':'uploaded','size':120},
        ]
    }

class ReleaseReuseTests(unittest.TestCase):
    def test_selects_release_only_with_same_repo_success_run_and_sha(self):
        data=metadata()
        c=choose_release([data],REPO,'a'*64,RUN_ID,'')
        self.assertEqual(c['tag'],TAG)
        self.assertEqual(c['zip_filename'],ZIP_NAME)
        self.assertEqual(c['source_kind'],'verified-published-release')
    def test_specific_tag_without_run_id(self):
        c=choose_release(metadata(),REPO,'a'*64,'',TAG)
        self.assertEqual(c['commit'],SHA)
    def test_wrong_run_or_repo_rejected(self):
        for run,repo in [('44997000087',REPO),(RUN_ID,'notuser/otherrepo')]:
            with self.subTest(run=run,repo=repo),self.assertRaises(ValueError):
                choose_release([metadata()],repo,'a'*64,run)
    def test_rejects_ambiguous_releases(self):
        with self.assertRaisesRegex(ValueError,'found 2'):
            choose_release([metadata(),metadata()],REPO,'a'*64,RUN_ID)
    def test_draft_prerelease_and_bad_link_rejected(self):
        for change in ({'draft':True},{'prerelease':True},{'html_url':'https://example.com'}):
            with self.subTest(change=change),self.assertRaises(ValueError):
                choose_release([{**metadata(),**change}],REPO,'a'*64,RUN_ID)
    def test_wrong_digest_rejected_even_before_download(self):
        with self.assertRaises(ValueError):
            choose_release(metadata('sha256:'+'c'*64),REPO,'a'*64,RUN_ID)
    def test_digests_match_as_optional_source_evidence(self):
        self.assertTrue(choose_release(metadata('sha256:'+'a'*64),REPO,'a'*64,RUN_ID))
    def test_wrong_asset_name_or_checksum_asset_missing(self):
        for mode in ('rename','no-sums'):
            data=metadata()
            if mode=='rename':data['assets'][0]['name']='MEGAsyncPortable_6.7.1.0_b1r13_x64.zip'
            else: data['assets'].pop()
            with self.subTest(mode=mode),self.assertRaises(ValueError):
                choose_release(data,REPO,'a'*64,RUN_ID)
    def test_requires_run_id_or_tag(self):
        with self.assertRaises(ValueError):choose_release(metadata(),REPO,'a'*64)
    def test_verify_downloaded_checks_hash_manifest_and_embedded_identity(self):
        with tempfile.TemporaryDirectory() as tmp:
            d=Path(tmp)
            with zipfile.ZipFile(d/ZIP_NAME,'w') as f:
                f.writestr('MEGAsyncPortable/Other/Source/BUILD-IDENTITY.json',json.dumps({'upstream_commit':SHA,'kit_revision':'b1r14'}))
                f.writestr('MEGAsyncPortable/App/AppInfo/appinfo.ini','[Version]\nPackageVersion=6.7.1.0\n')
            checksum=hashlib.sha256((d/ZIP_NAME).read_bytes()).hexdigest()
            (d/'SHA256SUMS.txt').write_text(f'{checksum}  {ZIP_NAME}\n')
            plan=choose_release(metadata(),REPO,checksum,RUN_ID)
            verify_downloaded(plan,d)
            (d/'SHA256SUMS.txt').write_text('b'*64+'  '+ZIP_NAME+'\n')
            with self.assertRaisesRegex(ValueError,'SHA256SUMS'):
                verify_downloaded(plan,d)
            (d/'SHA256SUMS.txt').write_text(f'{checksum}  {ZIP_NAME}\n')
            plan['commit']='f'*40
            with self.assertRaisesRegex(ValueError,'upstream commit'):
                verify_downloaded(plan,d)
    def test_reject_zip_hash_mismatch(self):
        with tempfile.TemporaryDirectory() as tmp:
            d=Path(tmp); (d/ZIP_NAME).write_bytes(b'bad zip'); (d/'SHA256SUMS.txt').write_text('a'*64+'  '+ZIP_NAME+'\n')
            with self.assertRaisesRegex(ValueError,'user-supplied SHA256'):
                verify_downloaded({'zip_filename':ZIP_NAME,'sha256':'a'*64,'commit':SHA,'version':'6.7.1.0'},d)
    def test_workflow_contains_verified_release_fallback_before_repackage(self):
        y=(ROOT/'.github/workflows/refresh-icons-only.yml').read_text()
        for phrase in ('source_release_tag', 'No unexpired unpublished artifact',
                       'scripts/verify_release_source.py select',
                       'gh release download',"--pattern 'SHA256SUMS.txt'",
                       'scripts/verify_release_source.py verify',
                       'scripts/packaging_only.py','scripts/refresh_icons_only.py'):
            self.assertIn(phrase,y)
        self.assertLess(y.index('scripts/verify_release_source.py verify'), y.index('scripts/packaging_only.py'))
        self.assertLess(y.index('scripts/packaging_only.py'), y.index('scripts/refresh_icons_only.py'))
        self.assertNotIn('throw "Expected exactly one unexpired validated unpublished source ZIP artifact; found',y)
if __name__ == '__main__': unittest.main()
