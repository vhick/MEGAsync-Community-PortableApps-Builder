"""Conditionally applied MEGAsync-only MSVC STL4043 compatibility adapter.

Invoke ONLY after a real Qt/MSVC compile probe proves that the same code fails
with STL4043 and passes with the target-specific suppression. Never disable /WX.
"""
import argparse
from pathlib import Path

TARGET = Path('src/MEGASync/CMakeLists.txt')
ANCHOR = 'if (WIN32)\n    add_executable(MEGAsync WIN32)\n'
DEFINITION = '_SILENCE_STDEXT_ARR_ITERS_DEPRECATION_WARNING'
INSERT = '''    # Community Windows build compatibility: Qt 5 may use deprecated
    # stdext::checked_array_iterator in some headers. Newer MSVC emits
    # STL4043/C4996, fatal under the existing /WX warning policy.
    # Scope only this deprecation acknowledgment to the MEGAsync target;
    # do not turn off /WX or suppress all C4996 diagnostics.
    if (MSVC)
        target_compile_definitions(MEGAsync PRIVATE
            _SILENCE_STDEXT_ARR_ITERS_DEPRECATION_WARNING)
    endif()
'''


def patch(root: Path) -> Path:
    path = root / TARGET
    if not path.is_file():
        raise RuntimeError(f'Missing upstream MEGAsync CMake target file: {path}')
    source = path.read_text(encoding='utf-8-sig')
    if DEFINITION in source:
        raise RuntimeError('Compatibility definition already exists; inspect upstream before changing it')
    if source.count(ANCHOR) != 1:
        raise RuntimeError(f'Upstream CMake target declaration changed; expected one known anchor, found {source.count(ANCHOR)}')
    if source.count('target_compile_definitions(MEGAsync') != 1:
        raise RuntimeError('Upstream MEGAsync compile-definition structure changed; review required')
    patched = source.replace(ANCHOR, ANCHOR + INSERT, 1)
    path.write_text(patched, encoding='utf-8', newline='\n')
    print(f'SOURCE-INSPECTED: applied probe-verified MEGAsync-only MSVC/Qt STL4043 adapter: {path}')
    return path


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('source_root', type=Path)
    patch(parser.parse_args().source_root)
