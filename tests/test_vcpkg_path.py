"""Regression of libsodium MSBuild long relative path from b1r2 log."""
import importlib.util
from pathlib import Path
import unittest

MODULE = Path(__file__).resolve().parents[1] / 'scripts' / 'verify_vcpkg_path.py'
spec = importlib.util.spec_from_file_location('verify_vcpkg_path', MODULE)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

class VcpkgLongPathTests(unittest.TestCase):
    def test_actual_failed_repo_length_is_264_chars(self):
        old = r'D:\a\MEGAsync-Community-PortableApps-Builder\MEGAsync-Community-PortableApps-Builder\vcpkg'
        self.assertEqual(mod.max_uncollapsed_path(old)[0], 264)
        with self.assertRaisesRegex(RuntimeError, 'MAX_PATH'):
            mod.validate(old)

    def test_runner_temp_is_short_enough(self):
        new = r'D:\a\_temp\vcpkg'
        self.assertEqual(mod.max_uncollapsed_path(new)[0], 190)
        self.assertEqual(mod.validate(new), 190)

    def test_relative_path_rejected(self):
        with self.assertRaisesRegex(ValueError, 'absolute Windows'):
            mod.validate('vcpkg')

if __name__ == '__main__': unittest.main()
