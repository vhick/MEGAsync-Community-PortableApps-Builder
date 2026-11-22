"""Tests that catch the b1r12 Windows CI environment failures before dispatch."""
from pathlib import Path
from tempfile import TemporaryDirectory
import importlib.util
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]

class WindowsBootstrapTests(unittest.TestCase):
    def test_python_dependencies_installed_before_all_tests(self):
        workflow = (ROOT / '.github/workflows/build-portableapps.yml').read_text(encoding='utf-8')
        install = workflow.index('- name: Install pinned Python test and build dependencies')
        pip = workflow.index('python -m pip install -r requirements-build.txt')
        tests = workflow.index('- name: Test resolver and fail-closed source patch fixture')
        self.assertLess(install, pip)
        self.assertLess(pip, tests)
        self.assertEqual(workflow.count('python -m pip install -r requirements-build.txt'), 1)

    def test_pinned_pillow_is_declared_for_launcher_icon_test(self):
        requirements = (ROOT / 'requirements-build.txt').read_text(encoding='utf-8')
        self.assertRegex(requirements, r'(?m)^Pillow==[0-9]+\.[0-9]+\.[0-9]+$')
        workflow = (ROOT / '.github/workflows/build-portableapps.yml').read_text(encoding='utf-8')
        self.assertIn('python -c "import PIL; import aqt;', workflow)

    def test_windows_alias_sensitive_test_uses_file_identity(self):
        source = (ROOT / 'tests/test_installer_path_and_artifact_recovery.py').read_text(encoding='utf-8')
        self.assertIn('actual.samefile(expected)', source)
        self.assertNotIn("self.assertEqual(mod.validate(stage, r'App", source)

    def test_shared_installer_validator_keeps_realpath_safety(self):
        source = (ROOT / 'scripts/validate_installer_input.py').read_text(encoding='utf-8')
        self.assertIn('source.resolve(strict=True)', source)
        self.assertIn('target.is_relative_to(root)', source)
        self.assertIn('pe_kind(target)', source)

    def test_revisions_align(self):
        main=(ROOT/'.github/workflows/build-portableapps.yml').read_text(encoding='utf-8')
        package=(ROOT/'.github/workflows/packaging-only.yml').read_text(encoding='utf-8')
        self.assertIn('package-revision: b1r15', main)
        self.assertIn('default: b1r15',package)
        self.assertIn('tag: mega-portable-v${{ env.APP_VERSION }}-b1r15-',main)

if __name__=='__main__':
    unittest.main()
