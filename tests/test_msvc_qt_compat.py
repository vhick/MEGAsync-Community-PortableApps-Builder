"""Regression fixtures for the b1r4 MSVC C2220/STL4043 build failure."""
import importlib.util
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('patch_msvc', ROOT / 'scripts' / 'patch_msvc_qt_compat.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

SAMPLE = '''# MEGA Desktop target
if (WIN32)
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


class MsvcQtCompatPatchTests(unittest.TestCase):
    def make_file(self, root, source=SAMPLE):
        target = root / module.TARGET
        target.parent.mkdir(parents=True)
        target.write_text(source, encoding='utf-8')
        return target

    def test_inserts_target_only_msvc_macro_and_preserves_warning_errors(self):
        with TemporaryDirectory() as temp:
            root = Path(temp)
            target = self.make_file(root)
            module.patch(root)
            data = target.read_text(encoding='utf-8')
            self.assertEqual(data.count(module.DEFINITION), 1)
            self.assertIn('if (MSVC)\n        target_compile_definitions(MEGAsync PRIVATE', data)
            self.assertIn('target_compile_definitions(MEGAsync\n    PUBLIC', data)
            self.assertNotIn('/WX-', data)
            self.assertNotIn('/wd4996', data)
            self.assertNotIn('_SILENCE_ALL_MS_EXT_DEPRECATION_WARNINGS', data)
            self.assertNotIn('CMAKE_CXX_FLAGS', data)

    def test_double_patch_rejected(self):
        with TemporaryDirectory() as temp:
            root = Path(temp)
            self.make_file(root)
            module.patch(root)
            with self.assertRaisesRegex(RuntimeError, 'already exists'):
                module.patch(root)

    def test_changed_upstream_anchor_rejected_without_editing(self):
        with TemporaryDirectory() as temp:
            root = Path(temp)
            target = self.make_file(root, SAMPLE.replace('add_executable(MEGAsync WIN32)', 'add_executable(MEGAsync)'))
            before = target.read_bytes()
            with self.assertRaisesRegex(RuntimeError, 'declaration changed'):
                module.patch(root)
            self.assertEqual(before, target.read_bytes())

    def test_changed_upstream_definitions_rejected(self):
        with TemporaryDirectory() as temp:
            root = Path(temp)
            target = self.make_file(root, SAMPLE.replace('target_compile_definitions(MEGAsync', '# target_compile_definitions absent'))
            before = target.read_bytes()
            with self.assertRaisesRegex(RuntimeError, 'compile-definition structure changed'):
                module.patch(root)
            self.assertEqual(before, target.read_bytes())


if __name__ == '__main__':
    unittest.main()
