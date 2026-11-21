"""Regression coverage for official WindowsApp.lib C++/WinRT link defect."""
from pathlib import Path
import sys
import json
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import patch_winrt_link as patcher
import ensure_winrt_link as verifier

SOURCE = '''if (WIN32)
    add_executable(MEGAsync WIN32)
elseif(APPLE)
    add_executable(MEGAsync MACOSX_BUNDLE)
endif()
target_link_libraries(MEGAsync
    PUBLIC
    MEGA::SDKlib
    Qt5::Core
)
'''
WINRT = '''#include "DesktopManager.h"
#include <winrt/Windows.Foundation.h>
#include <winrt/Windows.UI.Shell.h>
bool DesktopManager::IsDesktopAppPinningSupported() {
    return !!winrt::try_get_activation_factory<winrt::Windows::UI::Shell::TaskbarManager>();
}
'''


def fixture(root: Path, *, cmake: str = SOURCE, winrt: str = WINRT):
    target = root / patcher.TARGET
    desktop = root / patcher.DESKTOP
    target.parent.mkdir(parents=True, exist_ok=True)
    desktop.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(cmake, encoding='utf-8')
    desktop.write_text(winrt, encoding='utf-8')
    return target


class WinRTAdapterTests(unittest.TestCase):
    def test_real_winrt_source_gets_private_link(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d); target=fixture(root)
            self.assertEqual(patcher.patch(root), 'target-private-windowsapp')
            output=target.read_text()
            self.assertEqual(output.count('target_link_libraries(MEGAsync PRIVATE WindowsApp)'), 1)
            self.assertIn('if (MSVC)', output)
            self.assertIn('MEGA::SDKlib', output)

    def test_preserves_previous_stl4043_patch(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d); target=fixture(root)
            from patch_msvc_qt_compat import patch as stl_patch
            stl_patch(root)
            self.assertEqual(patcher.patch(root), 'target-private-windowsapp')
            output=target.read_text()
            self.assertEqual(output.count('_SILENCE_STDEXT_ARR_ITERS_DEPRECATION_WARNING'), 1)
            self.assertEqual(output.count('target_link_libraries(MEGAsync PRIVATE WindowsApp)'), 1)

    def test_skips_when_upstream_already_links_windowsapp(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d); target=fixture(root,cmake=SOURCE+'\ntarget_link_libraries(MEGAsync PRIVATE WindowsApp)\n')
            before=target.read_bytes()
            self.assertEqual(patcher.patch(root), 'already-upstream')
            self.assertEqual(before, target.read_bytes())

    def test_skips_when_winrt_was_removed(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d); target=fixture(root,winrt='// No WinRT APIs\n')
            before=target.read_bytes()
            self.assertEqual(patcher.patch(root), 'not-needed')
            self.assertEqual(before,target.read_bytes())

    def test_rejects_changed_winrt_api_evidence(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);target=fixture(root,winrt='#include <winrt/Windows.Foundation.h>\n// No expected API calls\n')
            before=target.read_bytes()
            with self.assertRaisesRegex(RuntimeError,'evidence changed'):patcher.patch(root)
            self.assertEqual(before,target.read_bytes())

    def test_rejects_missing_win_target_without_modifications(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);target=fixture(root,cmake=SOURCE.replace('add_executable(MEGAsync WIN32)','add_executable(MEGAsync)'))
            before=target.read_bytes()
            with self.assertRaisesRegex(RuntimeError,'anchor changed'):patcher.patch(root)
            self.assertEqual(before,target.read_bytes())

    def test_rejects_duplicate_win_target_without_modifications(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);target=fixture(root,cmake=SOURCE+'\nif(WIN32)\n  add_executable(MEGAsync WIN32)\nendif()\n')
            before=target.read_bytes()
            with self.assertRaisesRegex(RuntimeError,'anchor changed'):patcher.patch(root)
            self.assertEqual(before,target.read_bytes())

    def test_failed_link_preflight_preserves_source_and_reports_failure(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);target=fixture(root)
            before=target.read_bytes()
            project=root/'probe';project.mkdir();(project/'CMakeLists.txt').write_text('cmake_minimum_required(VERSION 3.21)')
            (project/'probe.cpp').write_text('int main(){return 0;}')
            def fail_on_build(command):
                return (0,'configure OK') if '-S' in command else (1,'LNK1104 cannot open file WindowsApp.lib')
            report=root/'report.json'
            with self.assertRaisesRegex(RuntimeError,'build preflight failed'):
                verifier.verify(project,root,root/'logs',report,executor=fail_on_build)
            self.assertEqual(before,target.read_bytes())
            data=json.loads(report.read_text())
            self.assertEqual(data['status'],'FAILED/BLOCKED')
            self.assertEqual(data['build'],'failed:1')
            self.assertTrue((root/'logs/cmake-build.log').is_file())

    def test_successful_real_procedure_flow_fixture(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);target=fixture(root)
            project=root/'probe';project.mkdir();(project/'CMakeLists.txt').write_text('cmake_minimum_required(VERSION 3.21)')
            (project/'probe.cpp').write_text('int main(){return 0;}')
            calls=[]
            def ok(command):
                calls.append(command)
                return 0,'Microsoft Visual Studio compile and link fixture succeeded'
            report=root/'report.json'
            data=verifier.verify(project,root,root/'logs',report,executor=ok)
            self.assertEqual(data['status'],'WINDOWS-COMPILED-LINK-PROBE')
            self.assertEqual(data['mode'],'target-private-windowsapp')
            self.assertEqual(len(calls),2)
            self.assertIn('WindowsApp',target.read_text())
            self.assertEqual(data,json.loads(report.read_text()))

    def test_winrt_probe_project_explicitly_uses_windowsapp(self):
        cmake=(ROOT/'scripts/winrt_link_probe/CMakeLists.txt').read_text()
        code=(ROOT/'scripts/winrt_link_probe/probe.cpp').read_text()
        self.assertIn('WindowsApp',cmake)
        self.assertIn('MSVC',cmake)
        self.assertIn('try_get_activation_factory',code)
        self.assertIn('check_hresult',code)

    def test_winrt_probe_declares_hresult_from_sdk_before_e_fail_use(self):
        """Regression: real b1r8 C2065 in probe.cpp(13,32) on Windows."""
        code=(ROOT/'scripts/winrt_link_probe/probe.cpp').read_text(encoding='utf-8')
        self.assertIn('#include <winerror.h>', code)
        self.assertLess(code.index('#include <winerror.h>'),code.index('check_hresult(E_FAIL)'))
        self.assertNotIn('#define E_FAIL', code)
        self.assertIn('#include <winrt/Windows.Foundation.h>', code)
        self.assertIn('#include <winrt/Windows.UI.Shell.h>', code)

    def test_link_probe_covers_both_previous_linker_references(self):
        code=(ROOT/'scripts/winrt_link_probe/probe.cpp').read_text(encoding='utf-8')
        cmake=(ROOT/'scripts/winrt_link_probe/CMakeLists.txt').read_text(encoding='utf-8')
        self.assertIn('try_get_activation_factory',code)
        self.assertIn('check_hresult(E_FAIL)',code)
        self.assertIn('catch (winrt::hresult_error const&)',code)
        self.assertIn('target_link_libraries(MEGAWinRTLinkProbe PRIVATE WindowsApp)',cmake)
        self.assertNotIn('add_library(MEGAWinRTLinkProbe',cmake)

    def test_workflow_orders_preflight_before_full_vcpkg_build(self):
        wf=(ROOT/'.github/workflows/build-portableapps.yml').read_text()
        self.assertLess(wf.index('Detect Qt/MSVC compatibility using real C++ compile probes'),
                        wf.index('Verify WindowsApp C++/WinRT linkage and source adapter'))
        self.assertLess(wf.index('Verify WindowsApp C++/WinRT linkage and source adapter'),
                        wf.index('Resolve and record vcpkg dependency manager identity'))
        self.assertIn('out/winrt-link-compatibility.json',wf)
        self.assertIn('winrt-link-compatibility-diagnostics',wf)
        self.assertIn('--winrt-report',wf)
        stage=(ROOT/'scripts/stage.py').read_text()
        self.assertIn('WINRT-LINK-COMPATIBILITY.json',stage)
        self.assertIn('WINDOWS-COMPILED-LINK-PROBE',stage)


if __name__=='__main__':unittest.main()
