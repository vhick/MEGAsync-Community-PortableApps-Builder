"""Stage uses MEGA's actual x64-windows-mega target, never host tools."""
import importlib.util
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / 'scripts' / 'stage.py'
spec=importlib.util.spec_from_file_location('stage', SCRIPT)
mod=importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

class VcpkgTargetTests(unittest.TestCase):
    def test_selects_mega_triplet(self):
        with TemporaryDirectory() as d:
            build=Path(d)/'build'; source=Path(d)/'source'
            (build/'vcpkg_installed'/'x64-windows'/'bin').mkdir(parents=True)
            target=source/'vcpkg_installed'/'x64-windows-mega'/'bin'
            target.mkdir(parents=True)
            self.assertEqual(mod.find_mega_runtime_bin(build,source), target)

    def test_rejects_host_triplet_only(self):
        with TemporaryDirectory() as d:
            build=Path(d)/'build'; source=Path(d)/'source'
            (build/'vcpkg_installed'/'x64-windows'/'bin').mkdir(parents=True)
            with self.assertRaisesRegex(RuntimeError, 'x64-windows-mega'):
                mod.find_mega_runtime_bin(build,source)

if __name__ == '__main__': unittest.main()
