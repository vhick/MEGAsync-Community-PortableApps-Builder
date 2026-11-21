"""Source-inspected, fail-closed MEGAsync-only MSVC STL4043 compatibility adapter.

Only called after real /WX Qt/MSVC probes establish both the specific warning
and that the exact macro fixes it.  The upstream target may legitimately have
MULTIPLE target_compile_definitions() calls (including USE_BREAKPAD); these are
not an indicator of CMake drift and must remain untouched.
"""
import argparse
import re
from pathlib import Path

TARGET = Path('src/MEGASync/CMakeLists.txt')
DEFINITION = '_SILENCE_STDEXT_ARR_ITERS_DEPRECATION_WARNING'
# Verify one actual WIN32 target creation, not the count of compilation options.
# Matching a real CMake command anchored to a line prevents comments from
# masquerading as build targets and supports ordinary CMake whitespace changes.
WIN_TARGET = re.compile(
    r'(?mi)^(?P<block>[ \t]*if[ \t]*\([ \t]*WIN32[ \t]*\)[ \t]*\n'
    r'[ \t]*add_executable[ \t]*\([ \t]*MEGAsync[ \t]+WIN32[ \t]*\)[ \t]*(?:\#[^\n]*)?\n)'
)
INSERT = '    # Community compatibility: applied only after real Qt/MSVC STL4043 probes.\n    # Target-private; preserve upstream /WX and all other warning diagnostics.\n    if (MSVC)\n        target_compile_definitions(MEGAsync PRIVATE\n            _SILENCE_STDEXT_ARR_ITERS_DEPRECATION_WARNING)\n    endif()\n'


def patch(root: Path) -> Path:
    path = root / TARGET
    if not path.is_file():
        raise RuntimeError(f'Missing upstream MEGAsync CMake target file: {path}')
    source = path.read_text(encoding='utf-8-sig')
    if DEFINITION in source:
        raise RuntimeError('Compatibility definition already exists; inspect upstream before changing it')
    matches = list(WIN_TARGET.finditer(source))
    if len(matches) != 1:
        raise RuntimeError(f'Upstream CMake Windows target declaration changed; expected exactly one WIN32 MEGAsync executable, found {len(matches)}')
    anchor = matches[0]
    # Insertion is immediately after add_executable(MEGAsync WIN32) INSIDE the
    # upstream Windows branch. Other definitions, including optional Breakpad,
    # remain unchanged regardless of their number/order.
    modified = source[:anchor.end()] + INSERT + source[anchor.end():]
    if modified.count(DEFINITION) != 1:
        raise RuntimeError('Internal error: compatibility adapter was not inserted exactly once')
    path.write_text(modified, encoding='utf-8', newline='\n')
    print(f'SOURCE-INSPECTED: probe-confirmed MSVC STL4043 macro applied to MEGAsync only: {path}')
    return path


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('source_root', type=Path)
    patch(parser.parse_args().source_root)
