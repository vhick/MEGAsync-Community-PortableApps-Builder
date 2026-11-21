# Evidence and verification matrix — kit b1r9

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
| Real b1r7 Qt/MSVC compatibility probe | WINDOWS-COMPILED-PROBE: baseline failed STL4043, targeted macro probe succeeded |
| Real b1r7 Windows source compilation | WINDOWS-COMPILED (partial): SDK and MEGAsync object compilation progressed; final MEGAsync.exe link FAILED/BLOCKED with WinRT LNK2019 |
| b1r8 WinRT link preflight | FAILED/BLOCKED: real MSVC 19.44 C2065 E_FAIL undeclared in probe.cpp; linker not reached |
| b1r9 corrected WinRT link preflight | STATIC-VALIDATED only; real Windows compilation/link pending |
| Complete b1r9 Windows application build | NOT YET VERIFIED; b1r7 reached final link and failed |
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

**The user did run b1r8 on GitHub-hosted Windows and the WindowsApp probe failed at C2065. No completed b1r8 or b1r9 application build, real runtime sync, installer execution or release publication is evidenced.** Earlier Windows builds reached application compilation and linking, but did not produce a working application. A new GitHub-hosted `windows-2022` run is required to validate b1r9; an interactive Windows session and controlled MEGA test account are still required for portability claims.

## Actual authoring checks run

- `python -m unittest discover -v -s tests` (48 deterministic static/fixture tests after b1r9 change): PASS on Linux authoring container
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

## 21 November 2026 b1r3 GitHub workflow-registration failure / b1r4 change

Screenshot shows main workflow listed as `.github/workflows/build-portableapps.yml` and new failures completing in about one second, while the packaging-only workflow retains its human-readable name. Inspected b1r3 YAML puts `${{ runner.temp }}` in `jobs.build.env`, but GitHub's context availability table excludes `runner` at that location. Thus the workflow is rejected before Windows runner allocation. This is **SOURCE-INSPECTED** local YAML and screenshot-correlated, not an independently fetched GitHub error page. b1r4 initializes `RUNNER_TEMP`-based short paths in a PowerShell step and writes them to `GITHUB_ENV`. A static regression test checks that no job-level env references `runner` and that the initialization happens before application checkout. GitHub dispatch success remains **NOT YET VERIFIED** until the user runs b1r4.

## 21 November 2026 b1r4 MEGAsync compilation error / b1r5 change

**WINDOWS-COMPILED (partial, user-provided log; application target FAILED):**
`logs_121526272643.zip` captures a real Windows GitHub Actions run. The CMake configuration and a substantial source build progressed through the SDK, and the first fatal source-build diagnostic was `C2220` in `MEGAsync.vcxproj` when compiling `src/MEGASync/syncs/control/MegaIgnoreManager.cpp`. The real underlying warning was `C4996` / `STL4043` caused by Qt 5.15.2 `QStringList`/`QList` using MSVC's deprecated `stdext::checked_array_iterator` in `xutility`. The MSVC warning itself specifically recommends `_SILENCE_STDEXT_ARR_ITERS_DEPRECATION_WARNING`.

**SOURCE-INSPECTED:** At official source tag `v6.7.1.0_Win`, `src/MEGASync/CMakeLists.txt` declares `add_executable(MEGAsync WIN32)` and defines compile options for this target. b1r5 adds a `PRIVATE`, `MSVC`-conditional compatibility macro to **that target only** using exact source anchors, preserving `/WX` for unrelated warnings. Static regression fixtures and workflow checks are local only. Windows compilation with b1r5, data containment, live cloud sync, launcher, ZIP/installer, and release publication are **NOT YET VERIFIED**. Another compiler error could surface when the actual build resumes.

## 21 November 2026 b1r6/b1r7 adaptive compiler preflight

The b1r5 always-on source macro was replaced by a real Qt/MSVC compile check that runs after Qt is retrieved and before costly vcpkg dependencies. Baseline uses `/WX` and exercises `QList<QString>::operator==`, matching the b1r4 failure. A target-only STL4043 workaround is applied solely if baseline fails with known STL4043/C4996 diagnostics and a second targeted compile succeeds. Missing MSVC APIs and other failures stop. A JSON report accompanies the packaged build. **The b1r7 WinRT linker log independently verifies the successful targeted Qt/MSVC preflight and substantial application compilation; b1r9 full linking and runtime portability remain NOT YET VERIFIED.**

## 21 November 2026 b1r6 Windows diagnostic evidence and b1r7 correction

**AUTOMATED-RUNTIME-TESTED (compiler probe only):** Uploaded `logs_121547965466.zip` and `qt-msvc-compatibility-diagnostics.zip` demonstrate that the real Windows MSVC 19.44 (toolset 14.44.35207), Qt 5.15.2 baseline Qt list-comparison probe failed with STL4043/C4996, while the targeted `_SILENCE_STDEXT_ARR_ITERS_DEPRECATION_WARNING` probe compiled successfully. **FAILED/BLOCKED:** the source CMake adapter then rejected the valid second `target_compile_definitions(MEGAsync ...)` statement. `v6.7.1.0_Win/src/MEGASync/CMakeLists.txt` includes a main PUBLIC definition and a conditional PRIVATE CRASH_BACKEND_URL definition inside `if(USE_BREAKPAD)`. b1r7 replaces the over-strict guard with unique Windows target declaration verification and retains fail-closed handling for incompatible target changes. **STATIC-VALIDATED locally only; b1r8 Windows application compilation, launcher runtime, profile containment, ZIP, installer and publication are NOT YET VERIFIED.**

## 21 November 2026 b1r7 Windows linker failure and b1r8 correction

**WINDOWS-COMPILED (partially):** `logs_121549679805.zip` contains a successful Windows Qt/MSVC targeted compatibility probe, successful vcpkg dependencies, MEGA SDK compilation, and a long MEGAsync compile that reached final executable linkage. **FAILED/BLOCKED:** Visual Studio `DesktopManager.obj` produced `LNK2019` for `WINRT_IMPL_RoGetActivationFactory` and `WINRT_IMPL_RoOriginateLanguageException`, followed by `LNK1120` for two unresolved externals. No final MEGAsync executable was produced. Microsoft documents `WindowsApp.lib` as the C++/WinRT umbrella import library. The new b1r8 WindowsApp probe and target-specific source adapter have **STATIC-VALIDATED** fixture coverage only; the *real* Windows link probe, complete application linker, PortableApps ZIP, installer, and end-user behavior are **NOT YET VERIFIED**.

## 21 November 2026 b1r8 WinRT probe failure and b1r9 correction

**WINDOWS-COMPILED (probe FAILED/BLOCKED):** The user-provided `logs_121566860828.zip` and `winrt-link-compatibility-diagnostics.zip` show MSVC 19.44 / SDK 10.0.26100.0 successfully configuring the probe but failing in `probe.cpp` at `C2065: E_FAIL undeclared`. The b1r8 WinRT `WindowsApp` import-library linkage was **not tested**, and no full application build occurred. The accompanying JSON reports `configure: passed`, `build: failed:1`, and `status: FAILED/BLOCKED`.

**STATIC-VALIDATED b1r9 correction:** `scripts/winrt_link_probe/probe.cpp` now explicitly includes `<winerror.h>` before using `E_FAIL` in `winrt::check_hresult`. New regression tests verify that ordering and the presence of the two WinRT reference paths, plus the existing CMake `WindowsApp` library. Real b1r9 Windows compilation/link, launcher behavior, installer, synchronization and profile isolation remain **NOT YET VERIFIED**.
