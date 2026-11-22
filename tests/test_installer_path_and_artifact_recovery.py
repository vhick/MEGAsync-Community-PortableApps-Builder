"""Regression tests for verified v1.0.0 running-exe and GitHub artifact reuse."""
from pathlib import Path
from tempfile import TemporaryDirectory
import importlib.util
import hashlib
import json
import re
import subprocess
import sys
import unittest
import zipfile

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('verify_installer_input', ROOT / 'scripts' / 'validate_installer_input.py')
sys.path.insert(0, str(ROOT / 'scripts'))
mod = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(mod)


def fixture_pe(machine=0x8664):
    """Minimal PE header for tests only (never shipped as an app binary)."""
    binary = bytearray(256)
    binary[0:2] = b'MZ'
    binary[0x3c:0x40] = (0x80).to_bytes(4, 'little')
    binary[0x80:0x84] = b'PE\0\0'
    binary[0x84:0x86] = machine.to_bytes(2, 'little')
    return bytes(binary)


def create_stage(where, machine=0x8664):
    stage = Path(where) / 'MEGAsyncPortable'
    app = stage / 'App' / 'MEGAsync'
    app.mkdir(parents=True)
    (app / 'MEGAsync.exe').write_bytes(fixture_pe(machine))
    return stage


class SharedActionRunningExeTests(unittest.TestCase):
    def test_pinned_windows_relative_path_is_accepted(self):
        with TemporaryDirectory() as d:
            stage = create_stage(d)
            self.assertEqual(mod.validate(stage, r'App\MEGAsync\MEGAsync.exe'), stage / 'App' / 'MEGAsync' / 'MEGAsync.exe')

    def test_forward_slashes_rejected(self):
        with TemporaryDirectory() as d:
            with self.assertRaises(ValueError):
                mod.validate(create_stage(d), 'App/MEGAsync/MEGAsync.exe')

    def test_parent_traversal_or_absolute_rejected(self):
        with TemporaryDirectory() as d:
            stage = create_stage(d)
            for rel in (r'..\MEGAsync.exe', r'C:\App\MEGAsync\MEGAsync.exe', r'\App\MEGAsync\MEGAsync.exe'):
                with self.subTest(rel=rel), self.assertRaises(ValueError):
                    mod.validate(stage, rel)

    def test_installer_requires_real_package_exe(self):
        with TemporaryDirectory() as d:
            stage = Path(d) / 'MEGAsyncPortable'
            stage.mkdir()
            with self.assertRaises(FileNotFoundError):
                mod.validate(stage, r'App\MEGAsync\MEGAsync.exe')

    def test_must_be_x64(self):
        with TemporaryDirectory() as d:
            stage = create_stage(d, 0x014c)
            with self.assertRaisesRegex(ValueError, 'x64 PE'):
                mod.validate(stage, r'App\MEGAsync\MEGAsync.exe')

    def test_both_workflows_have_identical_shared_action_compatible_path(self):
        for name in ('build-portableapps.yml', 'packaging-only.yml'):
            with self.subTest(workflow=name):
                t = (ROOT / '.github' / 'workflows' / name).read_text(encoding='utf-8')
                self.assertIn("running-exe: 'App\\MEGAsync\\MEGAsync.exe'", t)
                self.assertNotIn('running-exe: App/MEGAsync/MEGAsync.exe', t)
                self.assertIn('scripts/validate_installer_input.py', t)
                self.assertLess(t.index('scripts/validate_installer_input.py'), t.index('uses: vhick/Portable-Package-Builder@v1.0.0'))

    def test_recovery_accepts_only_same_builder_run_or_release(self):
        t = (ROOT / '.github' / 'workflows' / 'packaging-only.yml').read_text(encoding='utf-8')
        for token in ('source_run_id:', "if ($hasTag -eq $hasRun)", 'gh run download',
                      "-n 'independently-validated-zip-installer-failed'", "'out/ZIP-SHA256.txt'",
                      'scripts/verify_source_run.py', 'actions/workflows/build-portableapps.yml',
                      'EXPECTED_SHA256', 'scripts/packaging_only.py', 'actions: read'):
            self.assertIn(token, t)
        self.assertIn('publish_release == true', t)
        self.assertIn('dry-run: \'true\'', t)

    def test_packaging_only_reuses_b1r9_zip_without_rewriting_source_identity(self):
        with TemporaryDirectory() as d:
            base = Path(d)
            srczip = base / 'MEGAsyncPortable_6.7.1.0_b1r9_x64.zip'
            appini = '[Version]\nPackageVersion=6.7.1.0\n'
            identity = json.dumps({'upstream_commit': 'a'*40, 'kit_revision': 'b1r9'})
            members = {
                'MEGAsyncPortable/MEGAsyncPortable.exe': fixture_pe(),
                'MEGAsyncPortable/App/MEGAsync/MEGAsync.exe': fixture_pe(),
                'MEGAsyncPortable/App/AppInfo/appinfo.ini': appini.encode(),
                'MEGAsyncPortable/App/AppInfo/appicon.ico': b'ico fixture',
                'MEGAsyncPortable/Other/Source/BUILD-IDENTITY.json': identity.encode(),
                'MEGAsyncPortable/Data/': b'',
            }
            with zipfile.ZipFile(srczip, 'w') as z:
                for name, raw in members.items():
                    z.writestr(name, raw)
            original = hashlib.sha256(srczip.read_bytes()).hexdigest()
            out = base / 'out'
            env = base / 'github_env.txt'
            run = subprocess.run([sys.executable, str(ROOT / 'scripts' / 'packaging_only.py'),
                                  '--zip', str(srczip), '--sha256', original,
                                  '--out', str(out), '--env', str(env)],
                                 capture_output=True, text=True)
            self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
            self.assertEqual((out / 'MEGAsyncPortable' / 'Other' / 'Source' / 'BUILD-IDENTITY.json').read_text(), identity)
            self.assertIn('UPSTREAM_SHA=' + 'a'*40, env.read_text())
            self.assertIn(original, (out / 'ZIP-SHA256.txt').read_text())
            self.assertEqual(hashlib.sha256(srczip.read_bytes()).hexdigest(), original)

    def test_packaging_only_rejects_wrong_sha_without_extracting(self):
        with TemporaryDirectory() as d:
            p = Path(d) / 'MEGAsyncPortable_6.7.1.0_b1r9_x64.zip'
            p.write_bytes(b'not a zip')
            out = Path(d) / 'out'
            run = subprocess.run([sys.executable, str(ROOT / 'scripts' / 'packaging_only.py'),
                                 '--zip', str(p), '--sha256', 'a'*64,
                                 '--out', str(out), '--env', str(Path(d)/'env')],
                                 capture_output=True, text=True)
            self.assertNotEqual(run.returncode, 0)
            self.assertFalse((out / 'MEGAsyncPortable').exists())


if __name__ == '__main__':
    unittest.main()
