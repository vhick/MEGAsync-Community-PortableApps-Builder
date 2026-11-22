## 22 November 2026 b1r13 runtime startup user confirmation / b1r14 icon update

**USER-CONFIRMED**: The user stated "Working good now" for b1r13 and showed the PortableApps menu entry "MEGA Desktop Community" with a blue cloud icon. Treat this as a successful user-reported startup result. The screenshot does not independently establish synchronization, crash recovery, Windows state containment, safe relocation or installed MEGA coexistence. **SOURCE-INSPECTED**: b1r13 `scripts/make_icons.py` intentionally generates a generic cloud, so the icon issue is by design, not a failed Windows icon-loader or packaging subsystem. **STATIC-VALIDATED**: b1r14 replaces it with original red MP artwork, aligns menu and launcher ICO, and adds an icon-only repackage workflow that must verify a successful source run, original SHA, source-build identity and unchanged app files. **NOT YET VERIFIED**: b1r14 Windows compiler/installer/runtime re-run.

## 22 November 2026 b1r12 Windows test failure and b1r13 correction

**USER-SUPPLIED WINDOWS CI EVIDENCE:** `logs_121755836431.zip` shows 80 tests executed, 2 failures in the first fixture-test step: (1) Windows short `RUNNER~1` and long `runneradmin` aliases compared with `Path.__eq__` despite being the same file; (2) `scripts/make_icons.py` requires Pillow, but dependency installation happened after the tests and raised `ModuleNotFoundError`. This run reached no upstream checkout or real application build. b1r13 moves pinned dependency installation before tests, verifies Pillow/aqt imports, uses filesystem identity comparison in the test, and adds five regression tests. These changes are STATIC-VALIDATED locally; full Windows CI and runtime operation remain NOT YET VERIFIED.

## b1r11 runtime failure observed on Windows (22 November 2026)

**USER-CONFIRMED:** b1r11 finished building and appeared in PortableApps Platform; a user-run MEGAsync process exited after showing "Error loading application resources". The attached `MEGAsync.log` explicitly reported four missing binary Qt resources: `Resources_common.rcc`, `Resources_qml.rcc`, `qml.rcc`, and `Resources_dark.rcc`. Upstream gui.cmake also generates `Resources_light.rcc`. This means the earlier *structural ZIP validation passed a package that was functionally incomplete.* No successful login, sync, or runtime data isolation has been established.

**SOURCE-INSPECTED:** `src/MEGASync/gui/gui.cmake` for `v6.7.1.0_Win` declares `qt5_add_binary_resources` for all five resources and copies them beside the compiled MEGAsync.exe using POST_BUILD. `scripts/stage.py` in b1r11 copied only the EXE. `launcher/CMakeLists.txt` did not embed a Win32 icon, and community artwork was used for AppInfo. Source: https://github.com/meganz/MEGAsync/blob/v6.7.1.0_Win/src/MEGASync/gui/gui.cmake

**STATIC-VALIDATED (b1r12 fixture tests):** Resource discovery, exact-output selection, copying, SHA-256 manifest, corruption/missing-file failure, mandatory ZIP contents, icon build wiring and asset generation. A new Windows run is required for actual RCC asset integrity and the embedded Win32 icon check. Official logo is not used without separate trademark permission.

---

## b1r10 packaging-only provenance rejection / b1r12 correction (22 November 2026)

**FAILED/BLOCKED (real GitHub Actions run, user-provided log):**
`logs_121744908397.zip` records `SOURCE_RUN_ID=44918203381`,
`NEW_REVISION=b1r10`, and a 64-hex SHA256. After checking out the builder,
`Fetch exact same-repository release ZIP` threw `Source run does not belong to
this builder source-build workflow` in its original inline regex. The path
check required a leading `/` before `.github`, whereas the documented GitHub
REST run `path` is `.github/workflows/build-portableapps.yml@main`.
Original ZIP download/hash validation and NSIS installer generation were NOT
reached. The checksum is not independently validated by this failed run.

**STATIC-VALIDATED (b1r12 local fixtures):** Added exact run/workflow identity
verification against GitHub API responses including ID, repository, relative
path, manual-dispatch event and completed state, without weakening the original
SHA, artifact-name, source identity or package checks. GitHub API acceptance,
artifact recovery, NSIS execution and interactive runtime safety remain
NOT YET VERIFIED until a new Windows run is performed.

## b1r9 Windows build evidence, 21 November 2026 UTC

User-supplied `logs_121571335574.zip` confirms MEGAsync application x64 source compilation, the native C++ root launcher compilation, and independent PortableApps ZIP verification. The pinned shared Package Builder rejected forward slashes in its `running-exe` input. The workflow uploaded `independently-validated-zip-installer-failed` as a recoverable artifact from run `44918203381`. Installer generation and running MEGA were NOT verified.

b1r10 uses Windows-style `App\MEGAsync\MEGAsync.exe`, adds source-input preflight, and permits same-run repository artifact recovery without recompiling upstream. These changes have local fixture validation only until next hosted Windows run.

# Evidence and verification matrix — kit b1r12

| Stage | Latest supported status |
|---|---|
| Upstream tag `v6.7.1.0_Win` and SHA `650c9a2df326d7bf28d64e9f6e1588998757a862` | SOURCE-INSPECTED and WINDOWS-COMPILED (b1r9 GitHub run) |
| MEGA SDK compilation | WINDOWS-COMPILED (b1r9 run) |
| Adaptive Qt/MSVC probe and target-only fix | WINDOWS-COMPILED-PROBE and Windows build success (b1r9) |
| C++/WinRT WindowsApp link preflight and main app link | WINDOWS-COMPILED (b1r9 run) |
| MEGAsync.exe x64 source compilation | WINDOWS-COMPILED (b1r9 run) |
| MEGAsyncPortable.exe genuine C++ launcher | WINDOWS-COMPILED (b1r9 run) |
| PortableApps ZIP staging, integrity and x64 PE structure | STATIC-VALIDATED on Windows in b1r9 run |
| ZIP copy inside failed-installer artifact | Uploaded in b1r9 run (actual ZIP bytes not independently inspected here) |
| Shared custom-NSIS installer with b1r9 input | FAILED/BLOCKED — forward slash path rejected before NSIS |
| Shared custom-NSIS installer with corrected b1r10 input | NOT YET VERIFIED on hosted Windows |
| New same-run artifact recovery route | STATIC-VALIDATED by simulated fixtures; GitHub API and download not yet executed |
| Real installer install/reinstall/upgrade/rollback | NOT YET VERIFIED |
| Launch, login, data containment, real cloud sync, notifications | NOT YET VERIFIED |
| Empty-folder persistence, symlink handling, post-exit host scans | NOT YET VERIFIED at runtime |
| TraceGuard/ShellGuard | NOT IMPLEMENTED; residual host state needs runtime evidence |
| Release Publisher dry run and publication | NOT YET VERIFIED |
| User-confirmed functioning portable package | NOT YET VERIFIED |

## Local b1r10 authoring checks

- `python -m unittest discover -s tests -q` — 57 PASS (local static/fixture tests)
- `python scripts/smoke_tests.py` — PASS (static launcher-source assertions only)
- `python -m compileall -q scripts tests` — PASS
- Both workflow YAML files parse with PyYAML — PASS (not equivalent to GitHub server-side validation)
- The builder ZIP integrity and manifest checks are conducted before handoff.

The historical entries below preserve what was known **at the time of each older revision**. Where they state that compilation was unverified, the b1r9 result above supersedes those older statuses. No interactive Windows application test is demonstrated by the supplied log.

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
