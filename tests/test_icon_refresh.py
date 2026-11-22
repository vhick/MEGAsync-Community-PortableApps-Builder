"""Source-identity / Data safety tests for the b1r14 icon-only repackaging."""
import hashlib
import importlib
import json
from pathlib import Path
import re
import shutil
import sys
from tempfile import TemporaryDirectory
import unittest
import zipfile

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from stage import ROOT as PACKAGE_ROOT, EXPECTED_RCC, validate_zip
from refresh_icons_only import refresh, revisioned_display_version, ICON_PNGS
from make_icons import generate


def fake_pe():
    b=bytearray(512)
    b[:2]=b'MZ'
    b[0x3c:0x40]=(0x80).to_bytes(4,'little')
    b[0x80:0x84]=b'PE\0\0'
    b[0x84:0x86]=(0x8664).to_bytes(2,'little')
    return bytes(b)


def build_fixture(root: Path):
    stage=root/PACKAGE_ROOT
    app=stage/'App/MEGAsync'
    info=stage/'App/AppInfo'
    other=stage/'Other/Source'
    for p in (app,info,other,stage/'Data/Nested/Empty'):
        p.mkdir(parents=True,exist_ok=True)
    (stage/'Data/Nested/data.txt').write_text('user bytes must not change')
    (app/'MEGAsync.exe').write_bytes(fake_pe())
    (app/'companion.dll').write_bytes(b'unchanged dll payload')
    (stage/'MEGAsyncPortable.exe').write_bytes(fake_pe())
    manifest=[]
    for resource in EXPECTED_RCC:
        body=b'qres'+bytes(range(64))
        (app/resource).write_bytes(body)
        manifest.append({'name':resource,'size':len(body),'sha256':hashlib.sha256(body).hexdigest()})
    (other/'RCC-RESOURCE-MANIFEST.json').write_text(json.dumps({'resources':manifest}))
    (other/'BUILD-IDENTITY.json').write_text(json.dumps({'kit_revision':'b1r13','upstream_commit':'a'*40,'source_build':True,'runtime_validation':'NOT YET VERIFIED'}))
    (info/'appinfo.ini').write_text('[Version]\nPackageVersion=6.7.1.0\nDisplayVersion=6.7.1.0 b1r13\n')
    (info/'appicon.ico').write_bytes(b'old generic icon')
    return stage


class IconRefreshTests(unittest.TestCase):
    def test_new_community_icon_is_red_not_generic_cloud(self):
        from PIL import Image
        with TemporaryDirectory() as d:
            path=Path(d)
            generate(path)
            for size in ICON_PNGS:
                with Image.open(path/f'appicon_{size}.png') as im:
                    self.assertEqual(im.size,(size,size))
            with Image.open(path/'appicon.ico') as ico:
                self.assertTrue({(16,16),(32,32),(48,48),(256,256)}.issubset(ico.ico.sizes()))
            with Image.open(path/'appicon_32.png') as im:
                center=im.convert('RGBA').getpixel((16,5))
            self.assertGreater(center[0],100)
            self.assertGreater(center[0],center[2])
            self.assertNotEqual(center[:3],(30,49,69))

    def test_generated_artwork_is_deterministic(self):
        with TemporaryDirectory() as d:
            a,b=Path(d)/'a',Path(d)/'b'
            generate(a);generate(b)
            self.assertEqual(sorted(p.name for p in a.iterdir()),sorted(p.name for p in b.iterdir()))
            for p in a.iterdir():self.assertEqual(p.read_bytes(),(b/p.name).read_bytes())

    def test_icon_only_zip_preserves_original_app_and_data(self):
        with TemporaryDirectory() as d:
            root=Path(d);stage=build_fixture(root)
            icons=root/'newicons';launcher_icons=root/'launchericons'
            generate(icons);generate(launcher_icons)
            launcher=root/'MEGAsyncPortable.exe';launcher.write_bytes(fake_pe())
            original_app=(stage/'App/MEGAsync/MEGAsync.exe').read_bytes()
            original_dll=(stage/'App/MEGAsync/companion.dll').read_bytes()
            result=refresh(stage,launcher,launcher_icons/'appicon.ico',icons,root/'out','b'*64)
            validate_zip(result)
            with zipfile.ZipFile(result) as z:
                base=PACKAGE_ROOT+'/'
                self.assertEqual(z.read(base+'App/MEGAsync/MEGAsync.exe'),original_app)
                self.assertEqual(z.read(base+'App/MEGAsync/companion.dll'),original_dll)
                self.assertIn(base+'Data/Nested/Empty/',z.namelist())
                self.assertEqual(z.read(base+'Data/Nested/data.txt'),b'user bytes must not change')
                self.assertEqual(z.read(base+'App/AppInfo/appicon.ico'),icons.joinpath('appicon.ico').read_bytes())
                self.assertIn(b'b1r14',z.read(base+'App/AppInfo/appinfo.ini'))
                ident=json.loads(z.read(base+'Other/Source/BUILD-IDENTITY.json'))
                self.assertEqual(ident['kit_revision'],'b1r14')
                self.assertEqual(ident['source_builder_revision'],'b1r13')
                self.assertEqual(ident['upstream_commit'],'a'*40)
                self.assertEqual(ident['original_zip_sha256'],'b'*64)
                self.assertTrue(ident['icon_only_repackage'])
            self.assertIn(result.name,(root/'out/ZIP-SHA256.txt').read_text())

    def test_refuses_mismatched_launcher_and_menu_assets(self):
        with TemporaryDirectory() as d:
            root=Path(d);stage=build_fixture(root);generate(root/'icons')
            launcher=root/'MEGAsyncPortable.exe';launcher.write_bytes(fake_pe())
            bad=root/'different.ico';bad.write_bytes(b'wrong')
            with self.assertRaisesRegex(RuntimeError,'do not match'):
                refresh(stage,launcher,bad,root/'icons',root/'out','b'*64)

    def test_invalid_original_checksum_rejected(self):
        with TemporaryDirectory() as d:
            root=Path(d);stage=build_fixture(root);generate(root/'icons')
            launcher=root/'MEGAsyncPortable.exe';launcher.write_bytes(fake_pe())
            with self.assertRaisesRegex(RuntimeError,'checksum missing or invalid'):
                refresh(stage,launcher,root/'icons/appicon.ico',root/'icons',root/'out','bad')

    def test_safe_refuse_unknown_revision_and_app_missing(self):
        with TemporaryDirectory() as d:
            root=Path(d);stage=build_fixture(root);generate(root/'icons')
            launcher=root/'MEGAsyncPortable.exe';launcher.write_bytes(fake_pe())
            (stage/'Other/Source/BUILD-IDENTITY.json').write_text(json.dumps({'kit_revision':'unknown','upstream_commit':'a'*40}))
            with self.assertRaisesRegex(RuntimeError,'revision missing'):
                refresh(stage,launcher,root/'icons/appicon.ico',root/'icons',root/'out','b'*64)

    def test_icon_only_workflow_verifies_success_sha_and_retains_zip_on_installer_failure(self):
        workflow=(ROOT/'.github/workflows/refresh-icons-only.yml').read_text(encoding='utf-8')
        for expected in ('scripts/verify_source_run.py','original_zip_sha256',"conclusion -ne 'success'",'scripts/packaging_only.py',
                         'scripts/refresh_icons_only.py', 'scripts/verify_launcher_icon.py',
                         'vhick/Portable-Package-Builder@v1.0.0','vhick/portable-release-publisher@v1.1.1',
                         'MEGA-icon-only-b1r14-installer-failed', "'App\\MEGAsync\\MEGAsync.exe'", "dry-run: 'true'", "dry-run: 'false'"):
            self.assertIn(expected,workflow)
        self.assertLess(workflow.index('scripts/packaging_only.py'),workflow.index('scripts/refresh_icons_only.py'))
        self.assertLess(workflow.index('scripts/refresh_icons_only.py'),workflow.index('vhick/Portable-Package-Builder@v1.0.0'))

    def test_full_source_stage_and_launcher_use_same_icon(self):
        stage=(ROOT/'scripts/stage.py').read_text(encoding='utf-8')
        self.assertIn('sha256(launcher_icon)!=sha256(info/\'appicon.ico\')',stage)
        self.assertIn('portable_icon.rc',(ROOT/'launcher/CMakeLists.txt').read_text(encoding='utf-8'))


if __name__=='__main__':unittest.main()
