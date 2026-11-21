"""Bounded Windows path check for MEGA SDK's libsodium MSBuild project.

In the 2026-11-21 b1r2 log, an uncollapsed path with four parent segments
was 264 characters. Two libsodium source file C1083 errors followed.
Using a short vcpkg checkout path prevents that specific failure pattern.
This is an early structural check, NOT a Windows compilation test.
"""
import argparse
import ntpath

# Real relative source paths from libsodium 1.0.20 vs2022 project.
RELATIVE_SOURCES = (
    r"..\..\..\..\src\libsodium\crypto_pwhash\scryptsalsa208sha256\nosse\pwhash_scryptsalsa208sha256_nosse.c",
    r"..\..\..\..\src\libsodium\crypto_pwhash\scryptsalsa208sha256\sse\pwhash_scryptsalsa208sha256_sse.c",
)
PROJECT_SUBPATH = r"buildtrees\libsodium\x64-windows-mega-rel\builds\msvc\vs2022\libsodium"


def max_uncollapsed_path(vcpkg_root: str) -> tuple[int, str]:
    if not isinstance(vcpkg_root, str) or not ntpath.isabs(vcpkg_root):
        raise ValueError('Expected an absolute Windows vcpkg path')
    if vcpkg_root.startswith('\\\\'):
        raise ValueError('vcpkg path must be on a local drive, not a UNC network share')
    base = ntpath.join(ntpath.normpath(vcpkg_root), PROJECT_SUBPATH)
    candidates = [ntpath.join(base, relative) for relative in RELATIVE_SOURCES]
    longest = max(candidates, key=len)
    return len(longest), longest


def validate(vcpkg_root: str, threshold: int = 240) -> int:
    length, path = max_uncollapsed_path(vcpkg_root)
    # Headroom under 260 matters for the trailing NUL and Windows tooling.
    if length >= threshold:
        raise RuntimeError(
            f'Potential MAX_PATH MSBuild source failure: {length} chars '
            f'(limit for this preflight is {threshold-1}). '
            f'Choose a shorter vcpkg location. Longest path: {path}'
        )
    print(f'STATIC-VALIDATED libsodium MSBuild source path: {length} chars (< {threshold})')
    return length


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--root', required=True)
    a = p.parse_args()
    validate(a.root)
