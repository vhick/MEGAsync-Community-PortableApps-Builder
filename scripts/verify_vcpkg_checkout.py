"""Fail closed on shallow/partial vcpkg clones before manifest version lookups.

A vcpkg versioned port can refer to historical Git tree hashes. A partial clone
may lazily fetch them one-by-one at CMake configure time; a temporary outage
can then look like a mass dependency failure. We require a complete Git clone.
This is a structural preflight, not a guarantee that external port downloads
or package compilation will succeed.
"""
import argparse
import pathlib
import re
import subprocess


def git(repo: pathlib.Path, *args: str, allow_missing: bool = False) -> str:
    result = subprocess.run(
        ["git", "-C", str(repo), *args],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
        check=False,
    )
    if result.returncode != 0:
        if allow_missing and result.returncode == 1:
            return ""
        raise RuntimeError(f"git {' '.join(args)} failed ({result.returncode}): {result.stderr.strip()}")
    return result.stdout.strip()


def validate(repo: pathlib.Path, expected_sha: str) -> str:
    if not re.fullmatch(r"[0-9a-fA-F]{40}", expected_sha):
        raise ValueError("Expected an exact 40-character Git commit SHA")
    if not (repo / ".git").exists():
        raise RuntimeError("vcpkg checkout is not an independent Git repository")
    actual = git(repo, "rev-parse", "--verify", "HEAD")
    if actual.lower() != expected_sha.lower():
        raise RuntimeError(f"vcpkg revision mismatch: expected {expected_sha}, got {actual}")
    if git(repo, "rev-parse", "--is-shallow-repository") != "false":
        raise RuntimeError("vcpkg is shallow; versioned ports need historical Git trees")
    if git(repo, "config", "--local", "--get", "remote.origin.promisor", allow_missing=True):
        raise RuntimeError("vcpkg is a partial/promisor clone, with lazy historical-object downloads")
    if git(repo, "config", "--local", "--get", "remote.origin.partialclonefilter", allow_missing=True):
        raise RuntimeError("vcpkg is a partial clone (partialclonefilter set)")
    # Ensure that the selected object is a commit and that history is available.
    if git(repo, "cat-file", "-t", actual) != "commit":
        raise RuntimeError("Selected vcpkg revision is not a commit")
    count = int(git(repo, "rev-list", "--all", "--count"))
    if count < 2:
        raise RuntimeError("vcpkg checkout has no meaningful historical commits")
    print(f"STATIC-VALIDATED full-history vcpkg checkout: {actual}; {count} reachable commits")
    return actual


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=pathlib.Path, required=True)
    parser.add_argument("--sha", required=True)
    args = parser.parse_args()
    validate(args.repo, args.sha)
