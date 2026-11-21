# Evidence and verification matrix — kit b1r1

| Stage | Current evidence |
|---|---|
| Upstream latest observed release: v6.7.1.0_Win | SOURCE-INSPECTED (21 Nov 2026; not compiled) |
| Upstream C++/Qt CMake and Windows build targets | SOURCE-INSPECTED |
| MEGA application data-path source adapter | SOURCE-INSPECTED anchor + STATIC-VALIDATED fixture only |
| Source licence and limited redistribution rights | SOURCE-INSPECTED |
| Pinned package action v1.0.0 inputs/outputs | SOURCE-INSPECTED action.yml |
| Pinned publisher action v1.1.1 inputs | SOURCE-INSPECTED action.yml |
| Stable numeric resolver | STATIC-VALIDATED unit fixtures only |
| Python scripts syntactically valid | STATIC-VALIDATED in Linux authoring container |
| Workflow YAML parse | STATIC-VALIDATED in authoring container |
| Actual app Windows compilation | NOT YET VERIFIED |
| Genuine launcher Windows compilation | NOT YET VERIFIED |
| Startup and login, profile isolation | NOT YET VERIFIED |
| Real sync/backup behavior | NOT YET VERIFIED |
| Complete Qt/vcpkg runtime deployment | NOT YET VERIFIED |
| Empty-directory handling | STATIC-VALIDATED ZIP construction logic; runtime NOT YET VERIFIED |
| TraceGuard/ShellGuard cleanup | NOT IMPLEMENTED (no safe allowlist proven) |
| Win notifications + click activation | NOT YET VERIFIED |
| Autostart | NOT IMPLEMENTED (not requested) |
| PortableApps ZIP generation | NOT YET VERIFIED on Windows |
| Actual custom-NSIS installer generation | NOT YET VERIFIED |
| Real install, reinstall, upgrade, rollback | NOT YET VERIFIED |
| Publisher dry-run and publication | NOT YET VERIFIED |
| Desktop appbars, multi-monitor status bars | NOT APPLICABLE |
| User-confirmed functioning package | NOT YET VERIFIED |

**No Windows compile, real runtime sync, installer execution, or release publication took place during authoring of this kit.** A GitHub-hosted `windows-2022` run is the first real compilation test; an interactive Windows session and controlled MEGA test account are still required for portability claims.

## Actual authoring checks run

- `python -m unittest discover -v -s tests` (4 fixtures): PASS
- `python scripts/smoke_tests.py`: PASS (static text assertions, not program execution)
- `python -m compileall -q scripts tests`: PASS
- `yaml.safe_load` on the two workflows: PASS

SHA-256 of the *builder* ZIP is separately reported with the generated download. Production artifacts and their hashes are not known until the GitHub workflow executes.
