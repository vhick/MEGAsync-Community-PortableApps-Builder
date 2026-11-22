"""Regression fixtures for b1r10's invalid leading slash GitHub run.path guard."""
import copy
import importlib.util
import json
import subprocess
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

ROOT=Path(__file__).resolve().parents[1]
SPEC=importlib.util.spec_from_file_location('source_run', ROOT/'scripts/verify_source_run.py')
mod=importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(mod)
REPO='vhick/MEGAsync-Community-PortableApps-Builder'
RUN_ID=44918203381
WF_ID=123456789


def responses(path='.github/workflows/build-portableapps.yml@main'):
    run={'id':RUN_ID,'repository':{'full_name':REPO},'event':'workflow_dispatch',
         'status':'completed','conclusion':'failure','path':path,'workflow_id':WF_ID}
    workflow={'id':WF_ID,'path':'.github/workflows/build-portableapps.yml'}
    return run,workflow

class SourceRunProvenance(unittest.TestCase):
    def test_github_documented_relative_at_branch_path(self):
        r,w=responses()
        self.assertIn('Trusted completed', mod.check_source_run(r,w,REPO,str(RUN_ID)))

    def test_relative_path_without_branch(self):
        r,w=responses('.github/workflows/build-portableapps.yml')
        self.assertIn('workflow_id=',mod.check_source_run(r,w,REPO,str(RUN_ID)))

    def test_prior_optional_leading_slash_path(self):
        r,w=responses('/.github/workflows/build-portableapps.yml@refs/heads/main')
        self.assertIn('Trusted completed',mod.check_source_run(r,w,REPO,str(RUN_ID)))

    def test_invalid_paths_are_rejected(self):
        for path in ('x/.github/workflows/build-portableapps.yml@main',
                     '.github/workflows/packaging-only.yml@main',
                     '.github/workflows/build-portableapps.yml.bad@main',
                     '.github/workflows/build-portableapps.yml@main\nOTHER',
                     '', None):
            with self.subTest(path=path):
                r,w=responses(path)
                with self.assertRaises(ValueError): mod.check_source_run(r,w,REPO,str(RUN_ID))

    def test_different_repository_rejected(self):
        r,w=responses();r['repository']['full_name']='other/MEGAsync-Community-PortableApps-Builder'
        with self.assertRaisesRegex(ValueError,'repository mismatch'):mod.check_source_run(r,w,REPO,str(RUN_ID))

    def test_different_workflow_id_rejected(self):
        r,w=responses();r['workflow_id']=987654321
        with self.assertRaisesRegex(ValueError,'workflow ID mismatch'):mod.check_source_run(r,w,REPO,str(RUN_ID))

    def test_wrong_canonical_workflow_path_rejected(self):
        r,w=responses();w['path']='.github/workflows/packaging-only.yml'
        with self.assertRaisesRegex(ValueError,'Canonical workflow'):mod.check_source_run(r,w,REPO,str(RUN_ID))

    def test_wrong_run_id_rejected(self):
        r,w=responses();r['id']=RUN_ID-1
        with self.assertRaisesRegex(ValueError,'run ID mismatch'):mod.check_source_run(r,w,REPO,str(RUN_ID))

    def test_nonmanual_or_incomplete_run_rejected(self):
        for key,val in [('event','push'),('status','in_progress')]:
            with self.subTest(key=key):
                r,w=responses();r[key]=val
                with self.assertRaises(ValueError):mod.check_source_run(r,w,REPO,str(RUN_ID))

    def test_missing_api_fields_rejected(self):
        r,w=responses();del r['repository']
        with self.assertRaises(ValueError):mod.check_source_run(r,w,REPO,str(RUN_ID))

    def test_cli_fixture_accepts_b1r9_run_metadata(self):
        r,w=responses()
        with TemporaryDirectory() as d:
            base=Path(d)
            (base/'run.json').write_text(json.dumps(r),encoding='utf-8')
            (base/'workflow.json').write_text(json.dumps(w),encoding='utf-8')
            cmd=[sys.executable,str(ROOT/'scripts/verify_source_run.py'),
                 '--run-json',str(base/'run.json'),'--workflow-json',str(base/'workflow.json'),
                 '--repository',REPO,'--run-id',str(RUN_ID)]
            result=subprocess.run(cmd,capture_output=True,text=True)
            self.assertEqual(result.returncode,0,result.stderr)
            self.assertIn('Trusted completed source-build run',result.stdout)

    def test_packaging_workflow_uses_verified_identity_before_download(self):
        text=(ROOT/'.github/workflows/packaging-only.yml').read_text(encoding='utf-8')
        self.assertIn('gh api "repos/$env:GITHUB_REPOSITORY/actions/workflows/build-portableapps.yml"',text)
        self.assertIn('scripts/verify_source_run.py',text)
        self.assertLess(text.index('scripts/verify_source_run.py'),text.index('gh run download'))
        self.assertNotIn(r"$run.path -notmatch '/\.github/workflows/build-portableapps\.yml@'",text)
        self.assertIn("-n 'independently-validated-zip-installer-failed'",text)
        self.assertIn('EXPECTED_SHA256',text)

if __name__=='__main__':unittest.main()
