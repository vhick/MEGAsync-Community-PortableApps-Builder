"""Fail-closed, Windows-only source adapter for MEGAsync C++/WinRT linker imports.

The verified upstream Windows DesktopManager.cpp uses C++/WinRT.  Microsoft's
supported WindowsApp.lib umbrella import library supplies its runtime entry
points. This adapter does not change notification/taskbar functionality and
never modifies SDK or linker warning settings.
"""
from __future__ import annotations
import argparse
import re
from pathlib import Path
from patch_msvc_qt_compat import TARGET, WIN_TARGET

DESKTOP = Path('src/MEGASync/platform/win/DesktopManager.cpp')
WINRT_HEADERS = re.compile(r'(?m)^\s*#\s*include\s*<winrt/Windows\.[^>]+>')
WINRT_USAGE = re.compile(r'\bwinrt::(?:try_get_activation_factory|Windows::UI::Shell|hresult_error)\b')
LINK_START = re.compile(r'(?im)^[ \t]*target_link_libraries[ \t]*\([ \t]*MEGAsync\b')
LINKED_LIB = re.compile(r'(?i)(?<![A-Za-z0-9_])WindowsApp(?:\.lib)?(?![A-Za-z0-9_])')
INSERT = (
    '    # Community WinRT link correction: Windows SDK C++/WinRT runtime imports.\n'
    '    # WindowsApp is a system SDK import library, not a bundled DLL.\n'
    '    if (MSVC)\n'
    '        target_link_libraries(MEGAsync PRIVATE WindowsApp)\n'
    '    endif()\n'
)


def linked_libraries_for_megasync(cmake: str) -> list[str]:
    """Read both one-line and multiline target_link_libraries commands.

    Unlike a regex ending only on its own line, this supports legitimate
    upstream shorthand such as target_link_libraries(MEGAsync PRIVATE WindowsApp).
    """
    contents = []
    for match in LINK_START.finditer(cmake):
        start = match.end()
        depth = 1
        for index in range(start, len(cmake)):
            char = cmake[index]
            if char == '(':
                depth += 1
            elif char == ')':
                depth -= 1
                if depth == 0:
                    contents.append(cmake[start:index])
                    break
        else:
            raise RuntimeError('Unterminated MEGAsync target_link_libraries command')
    return contents


def patch(root: Path) -> str:
    path = root / TARGET
    desktop = root / DESKTOP
    if not path.is_file() or not desktop.is_file():
        raise RuntimeError('MEGAsync CMake target or source-inspected Windows DesktopManager.cpp not found')
    cmake = path.read_text(encoding='utf-8-sig')
    source = desktop.read_text(encoding='utf-8-sig')
    targets = list(WIN_TARGET.finditer(cmake))
    if len(targets) != 1:
        raise RuntimeError('MEGAsync Windows executable anchor changed; refusing WinRT CMake patch')
    has_headers = bool(WINRT_HEADERS.search(source))
    has_calls = bool(WINRT_USAGE.search(source))
    if has_headers != has_calls:
        raise RuntimeError('WinRT Windows source evidence changed; review includes and API calls before adapting linker')
    if not has_headers:
        # A verified removal of both source includes and WinRT calls needs no link.
        print('SOURCE-INSPECTED: no WinRT includes or calls in DesktopManager; no link patch')
        return 'not-needed'
    direct = linked_libraries_for_megasync(cmake)
    if any(LINKED_LIB.search(re.sub(r'(?m)#.*$', '', body)) for body in direct):
        print('SOURCE-INSPECTED: upstream MEGAsync already links WindowsApp; no patch')
        return 'already-upstream'
    # Do not treat comments or unrelated targets as proof that MEGAsync links it.
    anchor = targets[0]
    modified = cmake[:anchor.end()] + INSERT + cmake[anchor.end():]
    if modified.count('target_link_libraries(MEGAsync PRIVATE WindowsApp)') != 1:
        raise RuntimeError('WinRT patch integrity validation failed')
    path.write_text(modified, encoding='utf-8', newline='\n')
    print(f'SOURCE-INSPECTED: WindowsApp import-library link added to MSVC MEGAsync only: {path}')
    return 'target-private-windowsapp'


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('source_root', type=Path)
    print(patch(parser.parse_args().source_root))
