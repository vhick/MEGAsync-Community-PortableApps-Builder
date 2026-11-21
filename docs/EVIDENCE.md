# Evidence and verification matrix — kit b1r3

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

## 21 November 2026 b1r1 user-run evidence / b1r2 change

The uploaded GitHub Actions `logs_121512289382.zip` confirmed successful resolver, tag and SDK checkout, portability source patch, Qt acquisition, and vcpkg bootstrap. The Windows CMake configure step **FAILED** while vcpkg loaded historical versioned ports (`ffmpeg`, `openssl`, `sqlite3` and others): `fatal: could not fetch ... from promisor remote`, `Could not resolve host: github.com`. No application or launcher compile was reached.

b1r2 removes the vcpkg partial clone and shallow commit fetch, requires a full Git history, and performs an exact-SHA checkout verification and structural preflight. Local vcpkg Git history tests are STATIC-VALIDATED; **the corrected Windows build remains NOT YET VERIFIED** until a new GitHub Actions run is supplied.

## 21 November 2026 b1r2 user-run evidence / b1r3 change

Uploaded `logs_121516712196.zip` shows successful upstream release resolution, Qt acquisition, full vcpkg checkout (`9967a8eb5f4f5cd7be2b6717d31ddb7ff84c4751`, 31,526 reachable commits) and vcpkg bootstrap. It FAILED during CMake manifest installation of `libsodium:x64-windows-mega@1.0.20#3` with two MSVC `C1083` errors for `pwhash_scryptsalsa208sha256_nosse.c` and `pwhash_scryptsalsa208sha256_sse.c`. Both exist in upstream 1.0.20 source. The uncollapsed relative MSBuild project path was 264 characters under the very long runner checkout root; MAX_PATH is a likely cause, but Windows rerun is needed to confirm.

b1r3 installs vcpkg into short `RUNNER_TEMP\vcpkg`, places source/build/Qt under the same short job-local root, blocks long paths early, passes the exact temp path into CMake, and updates staging to use SDK's `x64-windows-mega` triplet instead of `x64-windows` host-tool triplet. Python fixture tests are STATIC-VALIDATED; Windows compilation, package generation, installer and runtime testing remain NOT YET VERIFIED.
