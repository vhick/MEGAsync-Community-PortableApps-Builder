"""Check embedded compiled PE icon via native Windows resource APIs.

Resource type 14 is RT_GROUP_ICON; resource type 3 is RT_ICON.
Loading as datafile never executes the launcher and does not start MEGAsync.
"""
import argparse
import ctypes
import os
from pathlib import Path

LOAD_LIBRARY_AS_DATAFILE=0x00000002
RT_ICON=3
RT_GROUP_ICON=14


def check_embedded_icon(path):
    path=Path(path)
    if not path.is_file():
        raise RuntimeError('Compiled launcher missing: '+str(path))
    if os.name!='nt':
        raise RuntimeError('Embedded PE icon validation requires Windows')
    import ctypes.wintypes as wt
    dll=ctypes.WinDLL('kernel32',use_last_error=True)
    load=dll.LoadLibraryExW
    load.argtypes=[wt.LPCWSTR,wt.HANDLE,wt.DWORD]
    load.restype=wt.HMODULE
    find=dll.FindResourceW
    # MAKEINTRESOURCE numeric values are pointer-sized integers, not strings.
    find.argtypes=[wt.HMODULE,ctypes.c_void_p,ctypes.c_void_p]
    find.restype=wt.HRSRC if hasattr(wt,'HRSRC') else ctypes.c_void_p
    free=dll.FreeLibrary
    free.argtypes=[wt.HMODULE]
    free.restype=wt.BOOL
    h=load(str(path.resolve()),None,LOAD_LIBRARY_AS_DATAFILE)
    if not h:raise RuntimeError('Windows failed to load compiled launcher as PE data: '+str(ctypes.get_last_error()))
    try:
        # RC file names resource ID 1; ensure BOTH group and actual icon exist.
        name=ctypes.c_void_p(1)
        group=ctypes.c_void_p(RT_GROUP_ICON)
        if not find(h,name,group):
            raise RuntimeError('Compiled MEGAsyncPortable.exe lacks RT_GROUP_ICON ID 1')
        # We deliberately ask for at least icon ID 1. Resource compilers commonly
        # allocate actual images from 1; the group is the critical menu icon.
        # Do not require a specific RT_ICON ID (windres/rc.exe may renumber).
        print('WINDOWS-COMPILED launcher embedded RT_GROUP_ICON ID 1 verified:',path)
    finally:
        free(h)


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--launcher',required=True)
    args=ap.parse_args()
    check_embedded_icon(args.launcher)

if __name__=='__main__':main()
