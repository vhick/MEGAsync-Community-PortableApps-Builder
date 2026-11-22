"""Static launcher and workflow regressions for Qt-owned host caches.

These are not substitutes for a real Windows runtime + ProcMon test.
"""
import pathlib
import re
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]


class PortableQtCachePolicyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.launcher = (ROOT/'launcher/main.cpp').read_text(encoding='utf-8')
        cls.main = (ROOT/'.github/workflows/build-portableapps.yml').read_text(encoding='utf-8')
        cls.refresh = (ROOT/'.github/workflows/refresh-icons-only.yml').read_text(encoding='utf-8')

    def test_qml_uses_documented_cache_path_under_portable_data(self):
        self.assertIn(r'L"\\Cache\\QML"', self.launcher)
        self.assertIn('SetEnvironmentVariableW(L"QML_DISK_CACHE_PATH", qmlCache.c_str())', self.launcher)
        self.assertIn('Mkdir(qmlCache)', self.launcher)

    def test_shader_cache_disabled_only_for_portable_child(self):
        for key in ('QT_DISABLE_SHADER_DISK_CACHE', 'QSG_RHI_DISABLE_SHADER_DISK_CACHE'):
            self.assertIn(f'SetEnvironmentVariableW(L"{key}", L"1")', self.launcher)
        self.assertNotIn('SetEnvironmentVariableW(L"LOCALAPPDATA"', self.launcher)
        self.assertNotIn('SetEnvironmentVariableW(L"APPDATA"', self.launcher)
        self.assertNotIn('SetEnvironmentVariableW(L"TEMP"', self.launcher)

    def test_cache_set_before_createprocess(self):
        self.assertLess(self.launcher.index('SetPortableQtCaches(data))'), self.launcher.index('CreateProcessW(exe.c_str()'))
        self.assertLess(self.launcher.index('MEGA_PORTABLE_DATA_DIR",profile.c_str()'), self.launcher.index('CreateProcessW(exe.c_str()'))
        self.assertIn('!IsRealDirectory(qmlCache)', self.launcher)

    def test_unicode_qt5_fallback_avoids_host_and_lossy_conversion(self):
        self.assertIn('!IsAsciiPath(qmlCache)', self.launcher)
        self.assertIn('UnsetEnv(L"QML_FORCE_DISK_CACHE")', self.launcher)
        self.assertIn('UnsetEnv(L"QML_DISK_CACHE_PATH")', self.launcher)
        self.assertIn('SetEnvironmentVariableW(L"QML_DISABLE_DISK_CACHE", L"1")', self.launcher)

    def test_no_global_env_or_destructive_host_cleanup(self):
        for bad in ('RegDelete', 'RemoveDirectoryW(', 'SHFileOperation', 'rmdir /s', 'TerminateProcessByName'):
            self.assertNotIn(bad, self.launcher)
        self.assertIn('OtherMegaRunning()', self.launcher)

    def test_full_build_and_launcher_refresh_compile_real_launcher(self):
        for contents in (self.main, self.refresh):
            self.assertIn('cmake --build launcher-build --config Release', contents)
            self.assertIn('scripts/verify_launcher_icon.py', contents)
            self.assertIn('scripts/verify_launcher_cache_policy.py', contents)
            self.assertIn('b1r15', contents)

    def test_launcher_refresh_preserves_app_subtree(self):
        src=(ROOT/'scripts/refresh_icons_only.py').read_text(encoding='utf-8')
        self.assertIn('if before != after:', src)
        self.assertIn('launcher_only_repackage', src)
        self.assertIn('original_zip_sha256', src)
        self.assertNotIn('shutil.rmtree', src)

if __name__ == '__main__':
    unittest.main()
