"""Regression tests grounded in the real v6.7.1.0_Win Qt resource contract."""
import hashlib
import importlib.util
import io
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import subprocess
import sys
import unittest
import zipfile

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('mega_stage',ROOT/'scripts'/'stage.py')
mod=importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

RESOURCES=mod.EXPECTED_RCC


def fixture_rcc():
    return b'qres'+bytes(range(64))


def fixture_pe():
    b=bytearray(256);b[:2]=b'MZ';b[0x3c:0x40]=(0x80).to_bytes(4,'little');b[0x80:0x84]=b'PE\0\0';b[0x84:0x86]=(0x8664).to_bytes(2,'little')
    return bytes(b)


def create_test_archive(path,missing=(),damaged=()):
    contents={
       'MEGAsyncPortable/MEGAsyncPortable.exe':fixture_pe(),
       'MEGAsyncPortable/App/MEGAsync/MEGAsync.exe':fixture_pe(),
       'MEGAsyncPortable/App/AppInfo/appinfo.ini':b'[Version]\nPackageVersion=6.7.1.0',
       'MEGAsyncPortable/App/AppInfo/appicon.ico':b'icon fixture',
       'MEGAsyncPortable/Data/':b''}
    manifest=[]
    for name in RESOURCES:
        if name in missing:continue
        data=fixture_rcc() if name not in damaged else b'BAD!'+bytes(range(64))
        contents['MEGAsyncPortable/App/MEGAsync/'+name]=data
        # Manifest uses original expected payload so tampering fails even if valid signature.
        expected=fixture_rcc()
        manifest.append({'name':name,'size':len(expected),'sha256':hashlib.sha256(expected).hexdigest()})
    contents[mod.RESOURCE_MANIFEST]=json.dumps({'resources':manifest}).encode()
    with zipfile.ZipFile(path,'w') as z:
        for name,b in contents.items():z.writestr(name,b)


class RuntimeResourceTests(unittest.TestCase):
    def test_discovers_all_upstream_declared_resources(self):
        with TemporaryDirectory() as d:
            gui=Path(d)/'src/MEGASync/gui/gui.cmake';gui.parent.mkdir(parents=True)
            gui.write_text('\n'.join(f'qt5_add_binary_resources({r[:-4]} "sample.qrc")' for r in RESOURCES))
            self.assertEqual(mod.required_rcc_from_upstream(d),RESOURCES)

    def test_source_change_missing_required_resource_fails_closed(self):
        with TemporaryDirectory() as d:
            gui=Path(d)/'src/MEGASync/gui/gui.cmake';gui.parent.mkdir(parents=True)
            gui.write_text('qt5_add_binary_resources(Resources_common "one.qrc")')
            with self.assertRaisesRegex(RuntimeError,'contract changed'):
                mod.required_rcc_from_upstream(d)

    def test_copy_same_build_only_and_preserve_checksums(self):
        with TemporaryDirectory() as d:
            out=Path(d)/'Release';out.mkdir();app=Path(d)/'Stage';app.mkdir()
            exe=out/'MEGAsync.exe';exe.write_bytes(fixture_pe())
            for name in RESOURCES:(out/name).write_bytes(fixture_rcc())
            rows=mod.copy_rcc_from_exact_build(exe,app,RESOURCES)
            self.assertEqual(len(rows),5)
            self.assertEqual([row['name'] for row in rows],list(RESOURCES))
            self.assertTrue(all((app/name).read_bytes()==fixture_rcc() for name in RESOURCES))

    def test_missing_companion_fails_before_zip(self):
        with TemporaryDirectory() as d:
            out=Path(d)/'Release';out.mkdir();app=Path(d)/'Stage';app.mkdir()
            exe=out/'MEGAsync.exe';exe.write_bytes(fixture_pe())
            for name in RESOURCES[1:]:(out/name).write_bytes(fixture_rcc())
            with self.assertRaisesRegex(RuntimeError,'Resources_common.rcc'):
                mod.copy_rcc_from_exact_build(exe,app,RESOURCES)

    def test_corrupt_rcc_rejected(self):
        with TemporaryDirectory() as d:
            p=Path(d)/'qml.rcc';p.write_bytes(b'NOTR'+bytes(64))
            with self.assertRaisesRegex(RuntimeError,'invalid RCC'):
                mod.check_rcc(p)

    def test_zip_complete_validates(self):
        with TemporaryDirectory() as d:
            z=Path(d)/'package.zip';create_test_archive(z)
            mod.validate_zip(z)

    def test_zip_missing_resource_rejected(self):
        with TemporaryDirectory() as d:
            z=Path(d)/'package.zip';create_test_archive(z,missing=('qml.rcc',))
            with self.assertRaisesRegex(RuntimeError,'omitted'):
                mod.validate_zip(z)

    def test_zip_resource_checksum_rejected(self):
        with TemporaryDirectory() as d:
            z=Path(d)/'package.zip';create_test_archive(z,damaged=('Resources_dark.rcc',))
            with self.assertRaisesRegex(RuntimeError,'Invalid resource payload'):
                mod.validate_zip(z)

    def test_launcher_build_embeds_original_community_icon(self):
        cm=(ROOT/'launcher/CMakeLists.txt').read_text()
        workflow=(ROOT/'.github/workflows/build-portableapps.yml').read_text()
        rc=(ROOT/'launcher/portable_icon.rc').read_text()
        self.assertIn('main.cpp portable_icon.rc',cm)
        self.assertIn('1 ICON "appicon.ico"',rc)
        self.assertIn('python scripts/make_icons.py launcher',workflow)
        self.assertIn('python scripts/verify_launcher_icon.py',workflow)
        self.assertLess(workflow.index('python scripts/make_icons.py launcher'),workflow.index('cmake -G \'Visual Studio 17 2022\' -A x64 -S launcher'))

    def test_compiler_preflight_checks_rcc_post_build(self):
        ps=(ROOT/'scripts/check_build.ps1').read_text()
        self.assertTrue(all(x in ps for x in RESOURCES))
        self.assertIn("-ne 'qres'",ps)

    def test_asset_generation_produces_multiresolution_ico(self):
        with TemporaryDirectory() as d:
            result=subprocess.run([sys.executable,str(ROOT/'scripts/make_icons.py'),d],capture_output=True,text=True)
            self.assertEqual(result.returncode,0,result.stderr)
            icon=(Path(d)/'appicon.ico').read_bytes()
            self.assertEqual(icon[:4],b'\x00\x00\x01\x00')
            self.assertTrue((Path(d)/'appicon_16.png').is_file())
            self.assertTrue((Path(d)/'appicon_32.png').is_file())

if __name__=='__main__': unittest.main()
