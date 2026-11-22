"""Real Qt/MSVC compiler preflight and evidence-based MEGAsync compatibility patch.

This script compiles Qt's QList<QString>::operator== with MSVC /WX before
expensive vcpkg installation. It never parses version numbers to predict
compiler behavior, never broad-disables warnings, and never patches the
upstream target unless BOTH (a) baseline fails specifically with STL4043 and
(b) the exact acknowledged warning compiles with /WX. Unknown breakage fails.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import re
import subprocess
import sys
from typing import Callable

from patch_msvc_qt_compat import patch as apply_target_patch

REVISION = 'b1r11'
RELATIVE_PROJECT = Path('scripts/qt_msvc_probe')
KNOWN_WARNING = re.compile(r'(?i)STL4043')
KNOWN_DEPRECATION = re.compile(r'(?i)checked_array_iterator')
KNOWN_CODE = re.compile(r'(?i)\bC4996\b')
MISSING_API = re.compile(r'(?i)(make_checked_array_iterator|checked_array_iterator)')
MISSING_CODE = re.compile(r'(?i)\bC2039\b|\bC2065\b|\bC3861\b')


def classify_failure(output: str) -> str:
    """Return proven class of failure; never infer STL4043 from C2220 alone."""
    if MISSING_API.search(output) and MISSING_CODE.search(output) and not KNOWN_WARNING.search(output):
        return 'removed_api'
    if KNOWN_WARNING.search(output) and KNOWN_CODE.search(output) and KNOWN_DEPRECATION.search(output):
        return 'stl4043'
    return 'unknown'


def commands(project: Path, build: Path, qt: Path, mode: str, generator: str = 'Visual Studio 17 2022') -> tuple[list[str], list[str]]:
    if mode not in ('baseline', 'stl4043'):
        raise ValueError('Unknown compiler preflight mode')
    return (
        ['cmake', '-G', generator, '-A', 'x64', f'-DCMAKE_PREFIX_PATH:PATH={qt}',
         f'-DMEGA_COMPAT_MODE:STRING={mode}', '-S', str(project), '-B', str(build)],
        ['cmake', '--build', str(build), '--config', 'Release', '--parallel', '2'],
    )


def run_command(args: list[str]) -> tuple[int, str]:
    result = subprocess.run(args, capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=180)
    return result.returncode, result.stdout + '\n' + result.stderr


def run_mode(project: Path, root: Path, qt: Path, mode: str,
             executor: Callable[[list[str]], tuple[int, str]] = run_command) -> tuple[bool, str, dict]:
    location = root / mode
    configure, build = commands(project, location, qt, mode)
    code, output = executor(configure)
    location.mkdir(parents=True, exist_ok=True)
    (location / 'cmake-configure.log').write_text(output, encoding='utf-8')
    if code != 0:
        return False, output, {'stage': 'configure', 'exit_code': code}
    code, build_output = executor(build)
    (location / 'cmake-build.log').write_text(build_output, encoding='utf-8')
    return code == 0, build_output, {'stage': 'build', 'exit_code': code}


def detect(qt: Path, source: Path, work: Path, report_path: Path,
           project: Path | None = None,
           executor: Callable[[list[str]], tuple[int, str]] = run_command) -> dict:
    project = project or Path(__file__).resolve().parents[1] / RELATIVE_PROJECT
    if not (qt / 'bin' / 'windeployqt.exe').is_file():
        raise RuntimeError(f'Qt deployment tools not found: {qt}')
    if not (project / 'CMakeLists.txt').is_file() or not (project / 'probe.cpp').is_file():
        raise RuntimeError(f'Compiler probe source missing: {project}')
    if not (source / 'src' / 'MEGASync' / 'CMakeLists.txt').is_file():
        raise RuntimeError('Upstream MEGAsync CMake source missing; cannot apply safe patch')
    work.mkdir(parents=True, exist_ok=True)
    report: dict = {'revision': REVISION, 'preflight': 'REAL_MSVC_QT_COMPILE', 'status': 'FAILED/BLOCKED',
                    'qt_path': str(qt), 'target': 'MEGAsync', 'macro': None,
                    'baseline': 'not-run', 'targeted': 'not-run'}
    try:
        baseline_ok, baseline_log, baseline_meta = run_mode(project, work, qt, 'baseline', executor)
        report['baseline'] = 'passed' if baseline_ok else f"failed:{baseline_meta['stage']}"
        report['baseline_classification'] = 'none' if baseline_ok else classify_failure(baseline_log)
        if not baseline_ok and baseline_meta['stage'] == 'configure':
            print('BASELINE CMAKE CONFIGURE FAILED: ' + baseline_log[-9000:], file=sys.stderr)
            raise RuntimeError('Cannot configure isolated Qt/MSVC compiler probe; inspect cmake-configure.log')
        if not baseline_ok:
            print('BASELINE C++ PROBE FAILED: ' + baseline_log[-9000:], file=sys.stderr)
        if baseline_ok:
            report['mode'] = 'unchanged'
        elif report['baseline_classification'] == 'stl4043':
            targeted_ok, targeted_log, targeted_meta = run_mode(project, work, qt, 'stl4043', executor)
            report['targeted'] = 'passed' if targeted_ok else f"failed:{targeted_meta['stage']}"
            if not targeted_ok:
                print('TARGETED C++ PROBE FAILED: ' + targeted_log[-9000:], file=sys.stderr)
                raise RuntimeError('Qt STL4043 compatibility test also failed; no source patch applied. '
                                   'Check targeted/cmake-build.log; compiler API may have changed.')
            # Safe source adapter only AFTER proving the exact fix with real /WX.
            apply_target_patch(source)
            report['mode'] = 'target-only-stl4043'
            report['macro'] = '_SILENCE_STDEXT_ARR_ITERS_DEPRECATION_WARNING'
        elif report['baseline_classification'] == 'removed_api':
            raise RuntimeError('Qt 5 checked-array-iterator API is missing in this MSVC STL. '
                               'A warning suppression cannot restore a removed API. '
                               'Use a verified compatible MSVC toolset or Qt source update.')
        else:
            raise RuntimeError('Unknown Qt/MSVC compile failure. No automatic warning suppression or '
                               'source patch will be applied; inspect baseline/cmake-build.log.')
        # Capture actual compiler and Qt identity emitted by CMake, not inferred.
        envfile = work / 'baseline' / 'probe-environment.txt'
        if not envfile.exists():
            raise RuntimeError('CMake completed but did not report compiler/Qt identity')
        report['toolchain'] = dict(line.split('=', 1) for line in envfile.read_text(encoding='utf-8').splitlines() if '=' in line)
        report['status'] = 'WINDOWS-COMPILED-PROBE'
        return report
    except Exception as exc:
        report['error'] = f'{type(exc).__name__}: {exc}'
        raise
    finally:
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--qt', type=Path, required=True)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--work', type=Path, required=True)
    parser.add_argument('--report', type=Path, required=True)
    parser.add_argument('--env', type=Path, required=True)
    args = parser.parse_args()
    try:
        report = detect(args.qt, args.source, args.work, args.report)
    except (RuntimeError, OSError, subprocess.TimeoutExpired) as exc:
        print('FAILED/BLOCKED adaptive Qt/MSVC preflight:', exc, file=sys.stderr)
        print('Probe logs and JSON report:', args.work, args.report, file=sys.stderr)
        raise SystemExit(1) from exc
    with args.env.open('a', encoding='utf-8', newline='\n') as stream:
        stream.write(f"MEGA_COMPAT_MODE={report['mode']}\n")
        stream.write(f"MEGA_COMPAT_REPORT={args.report}\n")
    print('WINDOWS-COMPILED-PROBE: Qt/MSVC preflight:', report['mode'])
    print('Toolchain:', json.dumps(report['toolchain'], ensure_ascii=False))
    print('NOTE: probe compilation does NOT prove complete MEGAsync compilation or runtime portability')


if __name__ == '__main__':
    main()
