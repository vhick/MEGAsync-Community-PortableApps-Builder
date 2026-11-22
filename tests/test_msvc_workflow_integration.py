"""Ensure compiler feature probing precedes expensive vcpkg dependency compilation."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / '.github/workflows/build-portableapps.yml'


class CompilerAdapterWorkflowTests(unittest.TestCase):
    def test_real_probe_runs_after_qt_before_vcpkg(self):
        data = WORKFLOW.read_text(encoding='utf-8')
        source_patch = data.index('      - name: Patch MEGA configuration directory at source (fail closed)')
        qt_install = data.index('      - name: Install verified-route Qt 5.15.2 and build helpers')
        adaptive = data.index('      - name: Detect Qt/MSVC compatibility using real C++ compile probes')
        vcpkg = data.index('      - name: Resolve and record vcpkg dependency manager identity')
        actual_build = data.index('      - name: Build actual MEGA Desktop application from pinned source')
        self.assertLess(source_patch, qt_install)
        self.assertLess(qt_install, adaptive)
        self.assertLess(adaptive, vcpkg)
        self.assertLess(vcpkg, actual_build)
        self.assertEqual(data.count('python scripts/detect_msvc_qt_compat.py'), 1)
        self.assertNotIn('python scripts/patch_msvc_qt_compat.py "$env:SOURCE_ROOT"', data)
        self.assertNotIn('-DCMAKE_COMPILE_WARNING_AS_ERROR=OFF', data)
        self.assertNotIn('/WX-', data)

    def test_build_identity_contains_preflight_report(self):
        data = WORKFLOW.read_text(encoding='utf-8')
        self.assertIn('--compat-report "$env:MEGA_COMPAT_REPORT"', data)
        self.assertIn('out/compiler-compatibility.json', data)
        stage = (ROOT / 'scripts/stage.py').read_text(encoding='utf-8')
        self.assertIn('COMPILER-COMPATIBILITY.json', stage)
        self.assertIn("REV='b1r10'", stage)


if __name__ == '__main__':
    unittest.main()
