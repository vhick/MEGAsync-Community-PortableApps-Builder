"""Headless Windows SDK WindowsApp link preflight before costly vcpkg compilation.

The actual b1r7 full MEGAsync link reached two LNK2019 WinRT imports. Microsoft
specifies WindowsApp.lib for C++/WinRT. This program validates that WindowsApp
is usable by the runner before applying a source-inspected, target-private link.
It never executes a GUI app and never synthesizes unresolved symbol shims.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import subprocess
import sys
from patch_winrt_link import patch

REV = 'b1r9'


def invoke(command: list[str]) -> tuple[int, str]:
    result = subprocess.run(command, capture_output=True, text=True,
                            encoding='utf-8', errors='replace', timeout=180)
    return result.returncode, result.stdout + '\n' + result.stderr


def verify(project: Path, source: Path, work: Path, report: Path,
           executor=invoke) -> dict:
    info = {'revision': REV, 'status': 'FAILED/BLOCKED', 'library': 'WindowsApp',
            'platform': 'Windows/MSVC/x64', 'mode': None, 'configure': 'not-run',
            'build': 'not-run', 'evidence': 'C++/WinRT Windows SDK import-library link probe'}
    try:
        if not (project / 'CMakeLists.txt').is_file() or not (project / 'probe.cpp').is_file():
            raise RuntimeError('Missing genuine WinRT link-probe project')
        if not (source / 'src/MEGASync/CMakeLists.txt').is_file():
            raise RuntimeError('Upstream MEGAsync target file missing')
        work.mkdir(parents=True, exist_ok=True)
        commands = (
            (['cmake', '-G', 'Visual Studio 17 2022', '-A', 'x64',
              '-S', str(project), '-B', str(work)], 'configure', 'cmake-configure.log'),
            (['cmake', '--build', str(work), '--config', 'Release', '--parallel', '2'],
             'build', 'cmake-build.log'),
        )
        for command, name, filename in commands:
            return_code, output = executor(command)
            (work / filename).write_text(output, encoding='utf-8')
            info[name] = 'passed' if return_code == 0 else f'failed:{return_code}'
            if return_code != 0:
                print(output[-12000:], file=sys.stderr)
                raise RuntimeError(f'WindowsApp C++/WinRT {name} preflight failed; inspect {filename}')
        info['mode'] = patch(source)
        info['status'] = 'WINDOWS-COMPILED-LINK-PROBE'
        return info
    except Exception as exc:
        info['error'] = f'{type(exc).__name__}: {exc}'
        raise
    finally:
        report.parent.mkdir(parents=True, exist_ok=True)
        report.write_text(json.dumps(info, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source', required=True, type=Path)
    p.add_argument('--work', required=True, type=Path)
    p.add_argument('--report', required=True, type=Path)
    a = p.parse_args()
    project = Path(__file__).resolve().parent / 'winrt_link_probe'
    outcome = verify(project, a.source, a.work, a.report)
    print('WINDOWS-COMPILED-LINK-PROBE: ' + json.dumps(outcome, ensure_ascii=False))

if __name__ == '__main__':
    main()
