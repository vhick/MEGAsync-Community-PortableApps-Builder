"""Static sanity checks for source patch, not interactive Windows app tests."""
import pathlib,re,sys
root=pathlib.Path(__file__).parents[1]
launcher=(root/'launcher'/'main.cpp').read_text(encoding='utf-8')
assert 'MEGA_PORTABLE_DATA_DIR' in launcher
assert 'AssignProcessToJobObject' in launcher
assert 'TerminateProcess(pi.hProcess' in launcher
assert 'OtherMegaRunning' in launcher
assert 'GetModuleFileNameW' in launcher
assert 'SetEnvironmentVariableW' in launcher
assert 'SHChangeNotifyRegister' not in launcher
assert 'RemoveDirectoryW(' not in launcher
assert 'RegDelete' not in launcher
print('STATIC-VALIDATED: launcher code checks (not runtime tests)')
