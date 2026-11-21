"""Regression coverage for b1r1 partial-vcpkg history failure and package identity."""
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]


class WorkflowContracts(unittest.TestCase):
    def test_vcpkg_must_use_full_checkout_and_preflight(self):
        workflow = (ROOT / '.github' / 'workflows' / 'build-portableapps.yml').read_text(encoding='utf-8')
        start = workflow.index('      - name: Resolve and record vcpkg dependency manager identity')
        end = workflow.index('      - name: Build actual MEGA Desktop application from pinned source')
        section = workflow[start:end]
        self.assertRegex(section, r'git clone --no-single-branch https://github.com/microsoft/vcpkg\.git')
        self.assertNotRegex(section, r'(?m)^\s*git clone .*--filter=')
        self.assertNotRegex(section, r'(?m)^\s*git -C .* fetch .*--depth')
        self.assertIn('scripts/verify_vcpkg_checkout.py', section)
        self.assertLess(section.index('scripts/verify_vcpkg_checkout.py'), section.index('bootstrap-vcpkg.bat'))
        self.assertIn('VCPKG_SHA=$sha', section)
        self.assertIn("Join-Path $env:RUNNER_TEMP 'vcpkg'", section)
        self.assertIn('scripts/verify_vcpkg_path.py --root', section)
        self.assertIn('PORTABLE_VCPKG_ROOT=$vcpkg', section)
        self.assertIn('-DVCPKG_ROOT="$env:PORTABLE_VCPKG_ROOT"', workflow)
        self.assertNotIn('-DVCPKG_ROOT="$env:KIT_ROOT/vcpkg"', workflow)
        self.assertIn("SOURCE_ROOT = (Join-Path $root 'mega-src')", workflow)
        self.assertIn("BUILD_ROOT = (Join-Path $root 'mega-build')", workflow)
        self.assertIn("QT_ROOT = (Join-Path $root 'mega-qt')", workflow)

    def test_packaging_only_accepts_future_revisions(self):
        workflow = (ROOT / '.github' / 'workflows' / 'packaging-only.yml').read_text(encoding='utf-8')
        self.assertIn('MEGAsyncPortable_*_b1r*_x64.zip', workflow)
        self.assertNotIn('MEGAsyncPortable_*_b1r1_x64.zip', workflow)

    def test_package_revision_in_source_workflow_matches_stage(self):
        source = (ROOT / '.github' / 'workflows' / 'build-portableapps.yml').read_text(encoding='utf-8')
        stage = (ROOT / 'scripts' / 'stage.py').read_text(encoding='utf-8')
        match = re.search(r"REV='(b1r\d+)'", stage)
        self.assertIsNotNone(match)
        self.assertIn('package-revision: ' + match.group(1), source)
        self.assertIn('b1r4', match.group(1))
        self.assertNotIn('b1r1', source)


if __name__ == '__main__':
    unittest.main()
