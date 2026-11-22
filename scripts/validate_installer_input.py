"""Fail early if the pinned v1.0.0 shared Package Builder would reject running-exe."""
import argparse
from pathlib import Path
import re
from stage import pe_kind

# Verified against vhick/Portable-Package-Builder@v1.0.0 scripts/common.ps1
# Test-RelativeEXE: Windows backslashes only. No absolute paths or parent traversal.
SHARED_ACTION_EXE_PATTERN = re.compile(r"[A-Za-z0-9_.+ -]+(?:\\[A-Za-z0-9_.+ -]+)*\.exe", re.IGNORECASE)
EXPECTED_RELATIVE_EXE = r"App\MEGAsync\MEGAsync.exe"


def validate(source: Path, running_exe: str) -> Path:
    if running_exe != EXPECTED_RELATIVE_EXE:
        raise ValueError(f"Wrong application lock executable: {running_exe!r}")
    if not SHARED_ACTION_EXE_PATTERN.fullmatch(running_exe):
        raise ValueError("Shared Package Builder requires a relative Windows .exe path using backslashes")
    root = source.resolve(strict=True)
    target = root.joinpath(*running_exe.split("\\")).resolve(strict=True)
    if not target.is_relative_to(root) or not target.is_file():
        raise ValueError("Installer running-exe is outside package or missing")
    if pe_kind(target) != 0x8664:
        raise ValueError("MEGAsync.exe must be a compiled Windows x64 PE file")
    print("STATIC-VALIDATED shared installer running-exe:", running_exe)
    return target


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--running-exe", required=True)
    args = parser.parse_args()
    validate(args.source, args.running_exe)


if __name__ == "__main__":
    main()
