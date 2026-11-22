"""STATIC check of reviewed launcher source, never substitutes for Windows runtime."""
from pathlib import Path

src=(Path(__file__).resolve().parents[1]/'launcher/main.cpp').read_text(encoding='utf-8')
checks=[
    'SetPortableQtCaches(data)',
    'SetEnvironmentVariableW(L"QML_DISK_CACHE_PATH", qmlCache.c_str())',
    'SetEnvironmentVariableW(L"QT_DISABLE_SHADER_DISK_CACHE", L"1")',
    'SetEnvironmentVariableW(L"QSG_RHI_DISABLE_SHADER_DISK_CACHE", L"1")',
    'SetEnvironmentVariableW(L"QML_DISABLE_DISK_CACHE", L"1")',
    'IsAsciiPath(qmlCache)',
]
for c in checks:
    if c not in src: raise SystemExit(f'Qt portable cache source control missing: {c}')
if src.index('SetPortableQtCaches(data))') >= src.index('CreateProcessW(exe.c_str()'):
    raise SystemExit('Qt portable cache policy must be applied BEFORE CreateProcessW')
for bad in ('SetEnvironmentVariableW(L"APPDATA"', 'SetEnvironmentVariableW(L"LOCALAPPDATA"', 'SetEnvironmentVariableW(L"TEMP"'):
    if bad in src: raise SystemExit('Broad host environment override is prohibited: '+bad)
print('STATIC-VALIDATED: portable Qt cache policy is configured before child launch')
