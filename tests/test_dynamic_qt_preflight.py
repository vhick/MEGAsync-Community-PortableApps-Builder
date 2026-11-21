"""Deterministic decision tests; NOT Windows compiler or portability tests."""
import sys
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import detect_msvc_qt_compat as detector

CMAKE_SOURCE = '''if (WIN32)
    add_executable(MEGAsync WIN32)
elseif (APPLE)
    add_executable(MEGAsync MACOSX_BUNDLE)
else()
    add_executable(MEGAsync)
endif()
target_compile_definitions(MEGAsync
    PUBLIC
    QT_NO_CAST_FROM_ASCII QT_NO_CAST_TO_ASCII
)
'''
STL4043 = """xutility(1341): error C2220: warning treated as error
xutility(1341): warning C4996: stdext::checked_array_iterator: warning STL4043: removed in future"""
MISSING_API = """qlist.h(915): error C2039: 'make_checked_array_iterator' is not a member of 'stdext'"""


class QtMsvcDetectorTests(unittest.TestCase):
    def setUp(self):
        self.tmp = TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.qt = self.root / 'qt'
        (self.qt / 'bin').mkdir(parents=True)
        (self.qt / 'bin' / 'windeployqt.exe').write_text('fixture')
        self.source = self.root / 'upstream'
        self.target = self.source / 'src/MEGASync/CMakeLists.txt'
        self.target.parent.mkdir(parents=True)
        self.target.write_text(CMAKE_SOURCE, encoding='utf-8')
        self.work = self.root / 'work'
        self.report = self.root / 'report.json'
        self.project = ROOT / 'scripts/qt_msvc_probe'

    def fake_executor(self, baseline_build=(0, 'Compiled successfully'), targeted_build=(0, 'Compiled successfully')):
        commands = []

        def fake(args):
            commands.append(args)
            if '-S' in args:
                loc = Path(args[args.index('-B') + 1])
                loc.mkdir(parents=True, exist_ok=True)
                (loc / 'probe-environment.txt').write_text(
                    'compiler=fixture-cl\ncompiler_version=19.44\nqt_version=5.15.2\ngenerator=Visual Studio 17 2022\n',
                    encoding='utf-8',
                )
                return (0, 'Configured')
            if 'baseline' in args[2]:
                return baseline_build
            return targeted_build
        return fake, commands

    def test_unmodified_on_baseline_success(self):
        fake, commands = self.fake_executor()
        before = self.target.read_bytes()
        result = detector.detect(self.qt, self.source, self.work, self.report, self.project, fake)
        self.assertEqual(result['mode'], 'unchanged')
        self.assertEqual(result['targeted'], 'not-run')
        self.assertEqual(self.target.read_bytes(), before)
        self.assertEqual(len(commands), 2)
        self.assertEqual(result['toolchain']['compiler_version'], '19.44')

    def test_real_stl4043_failure_triggers_only_verified_target_patch(self):
        fake, commands = self.fake_executor((1, STL4043))
        result = detector.detect(self.qt, self.source, self.work, self.report, self.project, fake)
        self.assertEqual(result['mode'], 'target-only-stl4043')
        self.assertEqual(result['targeted'], 'passed')
        self.assertEqual(len(commands), 4)
        self.assertEqual(self.target.read_text().count('_SILENCE_STDEXT_ARR_ITERS_DEPRECATION_WARNING'), 1)
        self.assertNotIn('/WX-', self.target.read_text())

    def test_actual_two_compile_definitions_probed_and_patched(self):
        self.target.write_text(CMAKE_SOURCE + '''
if(USE_BREAKPAD)
    target_compile_definitions(MEGAsync PRIVATE CRASH_BACKEND_URL="${CRASH_BACKEND_URL}")
endif()
''', encoding='utf-8')
        fake, cmds = self.fake_executor((1, STL4043))
        result = detector.detect(self.qt, self.source, self.work, self.report, self.project, fake)
        self.assertEqual(result['mode'], 'target-only-stl4043')
        self.assertEqual(result['targeted'], 'passed')
        self.assertEqual(self.target.read_text().count('target_compile_definitions(MEGAsync'), 3)
        self.assertEqual(len(cmds), 4)

    def test_unsupported_removed_stl_api_fails_without_patch(self):
        fake, commands = self.fake_executor((1, MISSING_API))
        before = self.target.read_bytes()
        with self.assertRaisesRegex(RuntimeError, 'removed API'):
            detector.detect(self.qt, self.source, self.work, self.report, self.project, fake)
        self.assertEqual(self.target.read_bytes(), before)
        self.assertEqual(len(commands), 2)
        self.assertTrue(self.report.exists())

    def test_unknown_error_fails_without_retry(self):
        fake, commands = self.fake_executor((1, 'fatal error C1083: cannot open Qt core header'))
        before = self.target.read_bytes()
        with self.assertRaisesRegex(RuntimeError, 'Unknown'):
            detector.detect(self.qt, self.source, self.work, self.report, self.project, fake)
        self.assertEqual(len(commands), 2)
        self.assertEqual(self.target.read_bytes(), before)

    def test_targeted_failure_fails_no_patch(self):
        fake, commands = self.fake_executor((1, STL4043), (1, 'fatal C2065: symbol missing'))
        before = self.target.read_bytes()
        with self.assertRaisesRegex(RuntimeError, 'also failed'):
            detector.detect(self.qt, self.source, self.work, self.report, self.project, fake)
        self.assertEqual(len(commands), 4)
        self.assertEqual(self.target.read_bytes(), before)

    def test_source_drift_fails_closed(self):
        self.target.write_text(CMAKE_SOURCE.replace('add_executable(MEGAsync WIN32)', 'add_executable(MEGAsync)'), encoding='utf-8')
        before = self.target.read_bytes()
        fake, commands = self.fake_executor((1, STL4043))
        with self.assertRaisesRegex(RuntimeError, 'declaration changed'):
            detector.detect(self.qt, self.source, self.work, self.report, self.project, fake)
        self.assertEqual(self.target.read_bytes(), before)

    def test_classifier_requires_specific_error_not_just_warning_as_error(self):
        self.assertEqual(detector.classify_failure('error C2220: warning as error'), 'unknown')
        self.assertEqual(detector.classify_failure(STL4043), 'stl4043')
        self.assertEqual(detector.classify_failure(MISSING_API), 'removed_api')

    def test_generated_command_is_real_cmake_build(self):
        config, build = detector.commands(self.project, self.work/'baseline', self.qt, 'baseline')
        self.assertEqual(config[:3], ['cmake','-G','Visual Studio 17 2022'])
        self.assertIn('-A', config)
        self.assertIn('-DMEGA_COMPAT_MODE:STRING=baseline', config)
        self.assertEqual(build[0:2], ['cmake','--build'])
        cmake_source = (self.project/'CMakeLists.txt').read_text()
        self.assertIn('/WX', cmake_source)
        self.assertIn('Qt5::Core', cmake_source)
        self.assertNotIn('/WX-', cmake_source)
        self.assertIn('return a == b', (self.project/'probe.cpp').read_text())


if __name__ == '__main__':
    unittest.main()
