"""Assemble and independently validate the source-built PortableApps ZIP."""
import argparse, hashlib, json, pathlib, shutil, subprocess, sys, zipfile
ROOT='MEGAsyncPortable'; REV='b1r2'
def sha256(p):
    h=hashlib.sha256()
    with open(p,'rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''): h.update(b)
    return h.hexdigest()
def pe_kind(path):
    with open(path,'rb') as f:
        if f.read(2)!=b'MZ':raise ValueError('Not a PE file: '+str(path))
        f.seek(0x3c); offset=int.from_bytes(f.read(4),'little');f.seek(offset)
        if f.read(4)!=b'PE\0\0':raise ValueError('Missing PE signature: '+str(path))
        return int.from_bytes(f.read(2),'little')
def main():
    ap=argparse.ArgumentParser()
    for field in ('source','build','launcher','qt','tag','version','sha','sdk-sha','vcpkg-sha','out'):
        ap.add_argument('--'+field,required=True)
    a=ap.parse_args(); out=pathlib.Path(a.out);out.mkdir(parents=True,exist_ok=True)
    stage=out/ROOT
    if stage.exists():shutil.rmtree(stage)
    info=stage/'App'/'AppInfo';app=stage/'App'/'MEGAsync';others=stage/'Other'/'Source'
    for p in (info,app,others,stage/'Data'):p.mkdir(parents=True,exist_ok=True)
    exe_candidates=list(pathlib.Path(a.build).rglob('MEGAsync.exe'))
    exe_candidates=[p for p in exe_candidates if p.parent.name.lower() in ('release','relwithdebinfo')]
    if len(exe_candidates)!=1:raise RuntimeError(f'Expected one compiled MEGAsync.exe, found: {exe_candidates}')
    shutil.copy2(exe_candidates[0],app/'MEGAsync.exe')
    launcher=pathlib.Path(a.launcher)
    if launcher.name.lower()!='megasyncportable.exe' or not launcher.is_file():raise RuntimeError('Missing compiled native launcher')
    shutil.copy2(launcher,stage/'MEGAsyncPortable.exe')
    for binary in (stage/'MEGAsyncPortable.exe',app/'MEGAsync.exe'):
        if pe_kind(binary)!=0x8664:raise RuntimeError('Expected genuine 64-bit Windows PE: '+str(binary))
    qt=pathlib.Path(a.qt);deploy=qt/'bin'/'windeployqt.exe'
    if not deploy.is_file():raise RuntimeError('Qt windeployqt not found: '+str(deploy))
    # Deployment may need Qt plugins and QML tree; keep every reported failure fatal.
    command=[str(deploy),'--release','--compiler-runtime','--qmldir',str(pathlib.Path(a.source)/'src'/'MEGASync'),str(app/'MEGAsync.exe')]
    subprocess.run(command,check=True,timeout=1800)
    # vcpkg defaults to dynamic x64-windows; deployment of those runtime DLLs
    # is separate from Qt's windeployqt and must be contained in App/MEGAsync.
    vcpkgbins=pathlib.Path(a.build)/'vcpkg_installed'/'x64-windows'/'bin'
    if not vcpkgbins.is_dir():
        vcpkgbins=pathlib.Path(a.source)/'vcpkg_installed'/'x64-windows'/'bin'
    if not vcpkgbins.is_dir():raise RuntimeError('Cannot locate compiled vcpkg dynamic dependency DLLs')
    for dll in vcpkgbins.glob('*.dll'):
        target=app/dll.name
        if target.exists() and sha256(target)!=sha256(dll):
            raise RuntimeError('Conflicting Qt/vcpkg DLL version: '+dll.name)
        if not target.exists():shutil.copy2(dll,target)
    # Optional sandboxed GFX worker is a build target or dependency on some versions.
    for worker in pathlib.Path(a.build).rglob('mega-desktop-app-gfxworker.exe'):
        if worker.parent.name.lower() in ('release','relwithdebinfo'):
            shutil.copy2(worker,app/worker.name)
    if not (app/'platforms'/'qwindows.dll').is_file():raise RuntimeError('Qt platform plugin missing after deployment')
    subprocess.run([sys.executable,str(pathlib.Path(__file__).with_name('make_icons.py')),str(info)],check=True)
    (info/'appinfo.ini').write_text(f'''[Format]
Type=PortableApps.comFormat
Version=3.5

[Details]
Name=MEGA Desktop Community Portable
AppID=MEGAsyncCommunityPortable
Publisher=Community source build (unofficial)
Homepage=https://github.com/meganz/MEGAsync
Category=Internet
Description=Community-built portable launcher for MEGA cloud sync. Not affiliated with MEGA.
Language=Multilingual

[License]
Shareable=true
OpenSource=false
Freeware=true
CommercialUse=false
EULAVersion=1

[Version]
PackageVersion={a.version}
DisplayVersion={a.version} {REV}

[Control]
Icons=1
Start=MEGAsyncPortable.exe
BaseAppID=MEGAsyncCommunityPortable
''',encoding='utf-8',newline='\n')
    for name in ('LICENCE.md','CREDITS.md'):
        src=pathlib.Path(a.source)/name
        if not src.is_file():raise RuntimeError('Missing upstream legal notice: '+name)
        shutil.copy2(src,others/name)
    shutil.copy2(pathlib.Path(__file__).parents[1]/'launcher'/'main.cpp',others/'CommunityLauncher.cpp')
    (others/'PORTABILITY-LIMITS.txt').write_text('WARNING: Only source data-path redirection is implemented. Native Explorer extension, update, Qt and OS traces remain unverified. Use NTFS/ReFS. Check sync folder destinations before connecting. No signed or official status is claimed.\n',encoding='utf-8')
    identity={ 'upstream_tag':a.tag,'upstream_commit':a.sha,'sdk_submodule_commit':a.sdk_sha,
        'vcpkg_commit':a.vcpkg_sha,'source_build':True,'launcher':'C++/MSVC','arch':'x64',
        'qt':str(qt),'kit_revision':REV,'portable_profile_env':'MEGA_PORTABLE_DATA_DIR',
        'portable_source_patch':'MegaApplication::loadDataPath()','runtime_validation':'NOT YET VERIFIED'}
    (others/'BUILD-IDENTITY.json').write_text(json.dumps(identity,indent=2,ensure_ascii=False),encoding='utf-8')
    zipname=f'MEGAsyncPortable_{a.version}_{REV}_x64.zip';dest=out/zipname
    with zipfile.ZipFile(dest,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6,allowZip64=True) as z:
        for f in sorted(stage.rglob('*')):
            rel=f.relative_to(stage.parent).as_posix()
            if f.is_dir():z.writestr(rel+'/',b'')
            else:z.write(f,rel)
    print('Package:',dest,'SHA256:',sha256(dest))
    validate_zip(dest)
    (out/'ZIP-SHA256.txt').write_text(f'{sha256(dest)}  {dest.name}\n',encoding='utf-8')
    env=pathlib.Path(str(out/'build-outputs.env'))
    env.write_text(f'ZIP_FILE={dest}\nPACKAGE_REVISION={REV}\n',encoding='utf-8')
def validate_zip(path):
    with zipfile.ZipFile(path) as z:
        bad=z.testzip()
        if bad:raise RuntimeError('Corrupt archive: '+bad)
        names=set(z.namelist())
        for name in (f'{ROOT}/MEGAsyncPortable.exe',f'{ROOT}/App/MEGAsync/MEGAsync.exe',f'{ROOT}/App/AppInfo/appinfo.ini',f'{ROOT}/App/AppInfo/appicon.ico',f'{ROOT}/Data/'):
            if name not in names:raise RuntimeError('Missing file/directory: '+name)
        for n in names:
            p=pathlib.PurePosixPath(n)
            if '..' in p.parts or not n.startswith(ROOT+'/'):raise RuntimeError('Unsafe archive member: '+n)
        for member in (f'{ROOT}/MEGAsyncPortable.exe',f'{ROOT}/App/MEGAsync/MEGAsync.exe'):
            # Re-use in-memory structure parsing for zipped executable
            import io
            b=io.BytesIO(z.read(member));assert b.read(2)==b'MZ';b.seek(0x3c);b.seek(int.from_bytes(b.read(4),'little'));assert b.read(4)==b'PE\0\0';assert int.from_bytes(b.read(2),'little')==0x8664
    print('STATIC-VALIDATED ZIP:',path)
if __name__=='__main__':main()
