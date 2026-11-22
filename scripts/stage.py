"""Assemble and independently validate the source-built PortableApps ZIP."""
import argparse, hashlib, json, pathlib, re, shutil, subprocess, sys, zipfile
ROOT='MEGAsyncPortable'; REV='b1r13'
EXPECTED_RCC = ('Resources_common.rcc','Resources_qml.rcc','Resources_light.rcc','Resources_dark.rcc','qml.rcc')
RESOURCE_MANIFEST = f'{ROOT}/Other/Source/RCC-RESOURCE-MANIFEST.json'
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
def find_mega_runtime_bin(build, source):
    checked=[]
    for base in (build,source):
        candidate=base/'vcpkg_installed'/'x64-windows-mega'/'bin'
        checked.append(str(candidate))
        if candidate.is_dir():
            return candidate
    raise RuntimeError('Cannot locate MEGA x64-windows-mega runtime DLL directory; inspected '+', '.join(checked))
def required_rcc_from_upstream(source):
    """Discover the binary resources declared by the exact upstream gui.cmake.

    This is deliberately narrow: only targets from qt5_add_binary_resources,
    not arbitrary files from the source tree or a developer workstation.
    """
    gui=pathlib.Path(source)/'src'/'MEGASync'/'gui'/'gui.cmake'
    if not gui.is_file():
        raise RuntimeError('Missing upstream gui/gui.cmake; cannot audit Qt resources')
    config=gui.read_text(encoding='utf-8')
    targets=re.findall(r'(?m)^\s*qt5_add_binary_resources\s*\(\s*([a-zA-Z][a-zA-Z_0-9]*)\b',config)
    if len(targets)!=len(set(targets)):
        raise RuntimeError('Duplicate Qt binary resource targets in upstream gui.cmake')
    discovered=tuple(n+'.rcc' for n in targets)
    if not set(EXPECTED_RCC).issubset(discovered):
        missing=sorted(set(EXPECTED_RCC)-set(discovered))
        raise RuntimeError('Upstream Qt resource contract changed; required target(s) absent: '+', '.join(missing))
    if len(discovered)>32:
        raise RuntimeError('Unexpected quantity of Qt resources; review source before packaging')
    return discovered


def check_rcc(p):
    """Qt external binary resources begin with qres and must be nonempty."""
    p=pathlib.Path(p)
    if not p.is_file():
        raise RuntimeError('Required runtime Qt resource missing: '+str(p))
    if p.stat().st_size < 64:
        raise RuntimeError('Runtime Qt resource is unexpectedly small: '+str(p))
    with p.open('rb') as f:
        if f.read(4)!=b'qres':
            raise RuntimeError('Runtime Qt resource has invalid RCC signature: '+str(p))
    return {'name':p.name,'size':p.stat().st_size,'sha256':sha256(p)}


def copy_rcc_from_exact_build(executable, app, resource_names):
    """Upstream gui.cmake copies all built RCC outputs beside MEGAsync.exe.

    Never search arbitrary source/installed folders or synthesize empty assets.
    """
    build_output=pathlib.Path(executable).parent
    result=[]
    for name in resource_names:
        candidate=build_output/name
        evidence=check_rcc(candidate)
        dest=pathlib.Path(app)/name
        shutil.copy2(candidate,dest)
        if sha256(dest)!=evidence['sha256']:
            raise RuntimeError('Staged Qt resource checksum mismatch: '+name)
        result.append(evidence)
    return result

def main():
    ap=argparse.ArgumentParser()
    for field in ('source','build','launcher','qt','tag','version','sha','sdk-sha','vcpkg-sha','compat-report','winrt-report','out'):
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
    # Upstream's binary Qt resources are separate from MEGAsync.exe. Neither
    # windeployqt nor copying the EXE automatically includes them.
    resource_names=required_rcc_from_upstream(a.source)
    resource_evidence=copy_rcc_from_exact_build(exe_candidates[0],app,resource_names)
    (others/'RCC-RESOURCE-MANIFEST.json').write_text(json.dumps({
        'origin':'same upstream compiled executable output directory',
        'source_definition':'src/MEGASync/gui/gui.cmake',
        'resources':resource_evidence
    },indent=2),encoding='utf-8')
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
    # The MEGA SDK's Windows target triplet is x64-windows-mega, NOT the
    # host-tools x64-windows triplet. Its overlay builds most ports static but
    # ffmpeg dynamic. Never silently copy host-triplet DLLs into the app.
    # Source/build are both considered because upstream may change its
    # manifest installed-directory layout between tagged releases.
    vcpkgbins=find_mega_runtime_bin(pathlib.Path(a.build),pathlib.Path(a.source))
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
    # Real compile-probe evidence is included verbatim for auditability.
    report_file=pathlib.Path(a.compat_report)
    if not report_file.is_file():raise RuntimeError('Compiler compatibility report missing')
    report=json.loads(report_file.read_text(encoding='utf-8'))
    if report.get('revision')!=REV or report.get('status')!='WINDOWS-COMPILED-PROBE':
        raise RuntimeError('Compiler preflight report is invalid or unsuccessful')
    if report.get('mode') not in ('unchanged','target-only-stl4043'):
        raise RuntimeError('Unrecognized Qt/MSVC compatibility mode')
    shutil.copy2(report_file,others/'COMPILER-COMPATIBILITY.json')
    winrt_file=pathlib.Path(a.winrt_report)
    if not winrt_file.is_file():raise RuntimeError('WindowsApp link preflight report missing')
    winrt=json.loads(winrt_file.read_text(encoding='utf-8'))
    if winrt.get('revision')!=REV or winrt.get('status')!='WINDOWS-COMPILED-LINK-PROBE':
        raise RuntimeError('WinRT WindowsApp link preflight report invalid or unsuccessful')
    if winrt.get('mode') not in ('target-private-windowsapp','already-upstream','not-needed'):
        raise RuntimeError('Unrecognized WindowsApp link preflight mode')
    shutil.copy2(winrt_file,others/'WINRT-LINK-COMPATIBILITY.json')
    identity={ 'upstream_tag':a.tag,'upstream_commit':a.sha,'sdk_submodule_commit':a.sdk_sha,
        'vcpkg_commit':a.vcpkg_sha,'source_build':True,'launcher':'C++/MSVC','arch':'x64',
        'qt':str(qt),'kit_revision':REV,'compiler_compatibility_mode':report['mode'],
        'compiler_probe_toolchain':report.get('toolchain', {}),
         'winrt_link_mode':winrt['mode'],'winrt_link_evidence':winrt['status'],'portable_profile_env':'MEGA_PORTABLE_DATA_DIR',
        'portable_source_patch':'MegaApplication::loadDataPath()','qt_rcc_resources':resource_evidence,'runtime_validation':'NOT YET VERIFIED'}
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
        for resource in EXPECTED_RCC:
            member=f'{ROOT}/App/MEGAsync/{resource}'
            if member not in names:
                raise RuntimeError('Required MEGAsync Qt resource omitted from ZIP: '+resource)
        if RESOURCE_MANIFEST not in names:
            raise RuntimeError('Runtime resource manifest missing from ZIP')
        manifest=json.loads(z.read(RESOURCE_MANIFEST))
        resources=manifest.get('resources')
        if not isinstance(resources,list) or len(resources)<len(EXPECTED_RCC):
            raise RuntimeError('Invalid staged Qt resource evidence')
        manifest_names=set()
        for item in resources:
            name=item.get('name','')
            if not re.fullmatch(r'[A-Za-z][A-Za-z_0-9]*\.rcc',name):
                raise RuntimeError('Untrusted resource name in manifest')
            if name in manifest_names:
                raise RuntimeError('Duplicate resource identity: '+name)
            manifest_names.add(name)
            member=f'{ROOT}/App/MEGAsync/{name}'
            if member not in names:
                raise RuntimeError('Resource manifest file absent: '+name)
            body=z.read(member)
            if len(body)<64 or not body.startswith(b'qres'):
                raise RuntimeError('Invalid resource payload inside ZIP: '+name)
            if item.get('size')!=len(body) or item.get('sha256')!=hashlib.sha256(body).hexdigest():
                raise RuntimeError('Resource checksum/size mismatch inside ZIP: '+name)
        if not set(EXPECTED_RCC).issubset(manifest_names):
            raise RuntimeError('Manifest does not cover all mandatory Qt resources')
        for n in names:
            p=pathlib.PurePosixPath(n)
            if '..' in p.parts or not n.startswith(ROOT+'/'):raise RuntimeError('Unsafe archive member: '+n)
        for member in (f'{ROOT}/MEGAsyncPortable.exe',f'{ROOT}/App/MEGAsync/MEGAsync.exe'):
            # Re-use in-memory structure parsing for zipped executable
            import io
            b=io.BytesIO(z.read(member));assert b.read(2)==b'MZ';b.seek(0x3c);b.seek(int.from_bytes(b.read(4),'little'));assert b.read(4)==b'PE\0\0';assert int.from_bytes(b.read(2),'little')==0x8664
    print('STATIC-VALIDATED ZIP:',path)
if __name__=='__main__':main()
