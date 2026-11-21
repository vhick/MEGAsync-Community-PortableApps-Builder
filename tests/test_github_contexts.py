"""Prevent GitHub-server workflow rejection that ordinary YAML parsing misses.

GitHub's runner context does not exist in jobs.<job_id>.env;
it becomes available only once a job is assigned to a runner.
This is a focused regression test for the b1r3 1-second failures,
not a substitute for full actionlint or an actual Actions run.
"""
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
MAIN = ROOT / '.github' / 'workflows' / 'build-portableapps.yml'
OTHER = ROOT / '.github' / 'workflows' / 'packaging-only.yml'


def job_level_environment(content):
    # Check every jobs.<id>.env section, not env keys on individual steps.
    return re.findall(r'(?ms)^    env:\n(.*?)(?=^    steps:)', content)


class GitHubContextTests(unittest.TestCase):
    def test_job_env_never_uses_runner_context(self):
        for path in (MAIN, OTHER):
            with self.subTest(file=path.name):
                data = path.read_text(encoding='utf-8')
                blocks = job_level_environment(data)
                self.assertTrue(blocks, 'expected at least one job-level env block')
                for block in blocks:
                    self.assertNotRegex(block, r'\$\{\{\s*runner\.',
                                        'runner context is invalid in jobs.<job_id>.env')

    def test_invalid_b1r3_pattern_would_be_caught(self):
        bad = ('jobs:\n  build:\n    env:\n'
               '      QT_ROOT: ${{ runner.temp }}\\mega-qt\n'
               '    steps:\n      - run: echo test\n')
        self.assertRegex(job_level_environment(bad)[0], r'\$\{\{\s*runner\.')

    def test_short_paths_are_initialized_inside_runner_step(self):
        workflow = MAIN.read_text(encoding='utf-8')
        self.assertIn('name: MEGA Desktop Community PortableApps - source build', workflow)
        init = workflow.index('      - name: Initialize short Windows build paths')
        test = workflow.index('      - name: Test resolver and fail-closed source patch fixture')
        acquire = workflow.index('      - name: Acquire exact upstream tag and its pinned SDK submodule')
        self.assertLess(init, test)
        self.assertLess(init, acquire)
        step = workflow[init:test]
        self.assertIn('shell: pwsh', step)
        self.assertIn('$env:RUNNER_TEMP', step)
        self.assertIn('$env:GITHUB_ENV', step)
        for key, name in [('QT_ROOT', 'mega-qt'), ('SOURCE_ROOT', 'mega-src'),
                          ('BUILD_ROOT', 'mega-build')]:
            self.assertIn(f"{key} = (Join-Path $root '{name}')", step)
        self.assertIn('"$($entry.Key)=$value" >> $env:GITHUB_ENV', step)


if __name__ == '__main__':
    unittest.main()
