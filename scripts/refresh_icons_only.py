"""Repackage a VERIFIED source-build ZIP with rebuilt cache-safe launcher and icons.

The source app's MEGAsync executable and all files under App/MEGAsync are kept
byte-identical, and the existing package's Data tree is never touched. The
launcher is genuinely recompiled, never patched in place using resource hacks.
"""
from __future__ import annotations
import argparse
import configparser
import hashlib
import json
from pathlib import Path
import re
import shutil
import zipfile
from stage import ROOT, REV, pe_kind, sha256, validate_zip

ICON_PNGS = (16, 32, 75, 128, 256)


def revisioned_display_version(src: str, version: str) -> str:
    # Only change the release identity line, not unrelated INI metadata.
    pattern = r'(?m)^DisplayVersion\s*=.*$'
    if len(re.findall(pattern, src)) != 1:
        raise RuntimeError('Source PortableApps appinfo.ini missing unique DisplayVersion')
    return re.sub(pattern, 'DisplayVersion=' + version + ' ' + REV, src)


def refresh(stage: Path, launcher: Path, launcher_ico: Path, generated_icons: Path,
            output: Path, original_sha256: str) -> Path:
    stage = Path(stage)
    launcher = Path(launcher)
    info = stage/'App'/'AppInfo'
    app = stage/'App'/'MEGAsync'
    others = stage/'Other'/'Source'
    if stage.name != ROOT or not app.is_dir() or not info.is_dir() or not others.is_dir():
        raise RuntimeError('Expected complete MEGAsyncPortable source-build staging')
    if not re.fullmatch('[0-9a-f]{64}', original_sha256.lower()):
        raise RuntimeError('Original ZIP checksum missing or invalid')
    if launcher.name.lower() != 'megasyncportable.exe' or pe_kind(launcher) != 0x8664:
        raise RuntimeError('Replacement launcher is not a valid compiled x64 Windows PE')
    if not (stage/'Data').is_dir():
        raise RuntimeError('Original portable Data directory is missing')
    manifest_path = others/'BUILD-IDENTITY.json'
    identity = json.loads(manifest_path.read_text(encoding='utf-8'))
    old_revision = identity.get('kit_revision')
    sha = identity.get('upstream_commit')
    if not isinstance(old_revision, str) or not re.fullmatch(r'b1r[0-9]+', old_revision):
        raise RuntimeError('Original builder revision missing or invalid')
    if not isinstance(sha, str) or not re.fullmatch(r'[0-9a-f]{40}', sha):
        raise RuntimeError('Original upstream commit missing or invalid')
    config = configparser.ConfigParser()
    ini_path = info/'appinfo.ini'
    old_ini = ini_path.read_text(encoding='utf-8')
    config.read_string(old_ini)
    version = config['Version']['PackageVersion']
    if not re.fullmatch(r'[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+', version):
        raise RuntimeError('Original application version not a verified numeric version')
    # An independent verification of the entire app subtree guards against
    # accidentally changing the known-working MEGAsync application binaries.
    before = {p.relative_to(app).as_posix(): sha256(p) for p in app.rglob('*') if p.is_file()}
    if not before or 'MEGAsync.exe' not in before:
        raise RuntimeError('No source-compiled application binary to preserve')
    if not launcher_ico.is_file() or not generated_icons.is_dir():
        raise RuntimeError('New community icon assets not generated')
    if sha256(launcher_ico) != sha256(generated_icons/'appicon.ico'):
        raise RuntimeError('Launcher icon and PortableApps menu icon do not match')
    for size in ICON_PNGS:
        if not (generated_icons/f'appicon_{size}.png').is_file():
            raise RuntimeError(f'Missing new PortableApps icon size {size}')

    shutil.copy2(launcher, stage/'MEGAsyncPortable.exe')
    for name in ('appicon.ico',) + tuple(f'appicon_{size}.png' for size in ICON_PNGS):
        shutil.copy2(generated_icons/name, info/name)
    ini_path.write_text(revisioned_display_version(old_ini, version), encoding='utf-8', newline='\n')
    identity['source_builder_revision'] = old_revision
    identity['kit_revision'] = REV
    identity['icon_only_repackage'] = False
    identity['launcher_only_repackage'] = True
    identity['portable_qt_cache_policy'] = 'QML_DISK_CACHE_PATH under Data/Cache/QML; shader disk cache disabled in child'
    identity['original_zip_sha256'] = original_sha256.lower()
    identity['original_megasync_sha256'] = before['MEGAsync.exe']
    identity['recompiled_launcher'] = True
    identity['runtime_validation'] = identity.get('runtime_validation', 'NOT YET VERIFIED')
    manifest_path.write_text(json.dumps(identity, indent=2, ensure_ascii=False)+'\n',encoding='utf-8')
    (others/'LAUNCHER-REPACK-IDENTITY.json').write_text(json.dumps({
        'mode':'launcher+icons only, source application binaries unchanged',
        'source_builder_revision':old_revision,
        'launcher_builder_revision':REV,
        'original_zip_sha256':original_sha256.lower(),
        'upstream_commit':sha,
        'icon_ico_sha256':sha256(launcher_ico),
        'portable_qt_cache_policy':'QML disk cache under Data; no shader disk cache',
        'app_file_count':len(before),
        'app_megasync_exe_sha256':before['MEGAsync.exe']},indent=2)+'\n',encoding='utf-8')
    after = {p.relative_to(app).as_posix(): sha256(p) for p in app.rglob('*') if p.is_file()}
    if before != after:
        raise RuntimeError('Launcher-only update unexpectedly changed MEGAsync app files')
    output.mkdir(parents=True, exist_ok=True)
    path = output/f'MEGAsyncPortable_{version}_{REV}_x64.zip'
    if path.exists(): raise RuntimeError('Refusing to overwrite an existing portable ZIP')
    with zipfile.ZipFile(path,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6,allowZip64=True) as z:
        for item in sorted(stage.rglob('*')):
            relative=item.relative_to(stage.parent).as_posix()
            if item.is_dir(): z.writestr(relative+'/',b'')
            else: z.write(item,relative)
    validate_zip(path)
    # Validate all menu icons are present with exact bytes in the new ZIP.
    with zipfile.ZipFile(path) as z:
        for name in ('appicon.ico',) + tuple(f'appicon_{n}.png' for n in ICON_PNGS):
            if z.read(f'{ROOT}/App/AppInfo/{name}') != (generated_icons/name).read_bytes():
                raise RuntimeError('Packaged icon checksum differs from generated icon: '+name)
    (output/'ZIP-SHA256.txt').write_text(f'{sha256(path)}  {path.name}\n',encoding='utf-8')
    return path


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--stage',type=Path,required=True)
    ap.add_argument('--launcher',type=Path,required=True)
    ap.add_argument('--launcher-ico',type=Path,required=True)
    ap.add_argument('--icons',type=Path,required=True)
    ap.add_argument('--out',type=Path,required=True)
    ap.add_argument('--original-sha256',required=True)
    a=ap.parse_args()
    path=refresh(a.stage,a.launcher,a.launcher_ico,a.icons,a.out,a.original_sha256)
    print('STATIC-VALIDATED LAUNCHER-ONLY ZIP:',path,'sha256',sha256(path))

if __name__=='__main__': main()
