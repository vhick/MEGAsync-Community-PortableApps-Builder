## b1r12 Windows CI tests fail before compilation (two failures)

The actual runner log `logs_121755836431.zip` failed 2 of 80 pre-build tests:
1. `test_pinned_windows_relative_path_is_accepted` compared Windows `runneradmin` vs `RUNNER~1` path text. b1r13 instead checks the underlying file with `Path.samefile()`. The installer path validation still requires the same allowed relative executable, real file containment and x64 PE header.
2. `test_asset_generation_produces_multiresolution_ico` raised `ModuleNotFoundError: No module named PIL`. b1r13 installs the pinned requirements (including Pillow) and checks imports before the entire test suite and Qt acquisition.

This was a test-environment failure, not a MEGA runtime failure. Run the FULL source-build workflow on b1r13 with publishing disabled; older ZIP files remain incomplete and cannot be made functional by installer-only packaging.

## Runtime: "Error loading application resources" (b1r11 and earlier)

The user-observed MEGAsync log contains `Missing resource file` for `Resources_common.rcc`, `Resources_qml.rcc`, `qml.rcc`, and `Resources_dark.rcc`. Upstream also builds `Resources_light.rcc`. b1r12 copies all five source-built .rcc files from the compiled executable folder to `App/MEGAsync` and checks their `qres` magic and SHA-256. This must not be confused with windeployqt: Qt framework DLL deployment alone is insufficient.

Old b1r9/b1r11 ZIPs cannot be repaired by running the packaging-only workflow unchanged. Build a fresh b1r12 full source ZIP, preserve the existing portable `Data`, and test with disposable sync folders. Do not copy app resources from a different version or delete the MEGA profile to conceal the problem.

## Menu and launcher icon

Earlier kits generated a neutral cloud icon only for AppInfo, so the compiled launcher had no embedded icon. b1r12 generates the same original community icon before Windows resource compilation and checks RT_GROUP_ICON. MEGA's code licence excludes rights to use its logo or trademarks: original community artwork remains intentionally distinct from the official MEGA icon.

## b1r10 packaging-only incorrectly rejects the source run ID

The uploaded `logs_121744908397.zip` confirms that `source_run_id=44918203381`,
`installer_package_revision=b1r10`, and a 64-character ZIP SHA-256 were received.
The workflow rejected the run at its provenance check because its regex required
`/.github/...` even though GitHub returns `.github/...@main`. This is not a
checksum failure. b1r12 uses `scripts/verify_source_run.py` to check the
relative workflow path, repository, original run ID, manual event and canonical
numeric workflow ID. Keep the exact SHA-256 and run ID only for historical installer testing; the old package lacks the required Qt RCC resources and must not be treated as a usable runtime package. Use the full b1r13 source build for the corrected application.

## b1r9 installer reports "running-exe must be a relative Windows .exe file"

The pinned shared action requires Windows backslashes. Both workflows now pass `App\MEGAsync\MEGAsync.exe` and test its existence and x64 PE structure first. The original b1r9 application ZIP was independently validated and uploaded as a workflow artifact, so use packaging-only with a `source_run_id` and an independently copied SHA-256 to rebuild ONLY the installer. This was a valid workaround for the earlier installer-input defect only. The original b1r9 ZIP lacks required Qt resources, so do not use installer-only packaging for a working release; rebuild from the full b1r13 source workflow.

# Troubleshooting

- **Workflow absent:** Push the `.github/workflows` folder to default branch, enable Actions on GitHub, ensure ZIP not extracted into a nested folder.
- **Stable release lookup fails:** Check GitHub API status/token; a 404 from a requested version is a real failure; no fallback to unverified master. Specify `v6.7.1.0_Win` or a newer exact stable Windows tag.
- **Qt download or CMake configure fails:** Upstream's internal Windows recipe references Qt 5.15.17; the kit uses public Qt 5.15.2. This is a known compatibility risk. Do not downgrade security or bypass compile errors. Save logs and compare upstream `README.win.md` with current CMake requirements.
- **vcpkg versioned ports fail with `could not fetch ... from promisor remote` / `Could not resolve host github.com`:** b1r1 used a partial clone (`--filter=blob:none`) and vcpkg needed historical Git trees. b1r2 performs a complete `git clone --no-single-branch`, verifies it is neither shallow nor partial, and checks the selected commit before running CMake. If the FULL clone itself fails, this is a genuine network/DNS problem: rerun the workflow when GitHub is reachable. Do not disable Git integrity checks or fabricate missing version trees.
- **libsodium 1.0.20 MSVC C1083 for `pwhash_scryptsalsa208sha256_{nosse,sse}.c`:** In the b1r2 user run, the source files exist upstream but a very long GitHub checkout made the unresolved source path 264 characters. b1r3 uses short `RUNNER_TEMP\vcpkg`, validates MAX_PATH headroom before any clone, and passes that same exact path to CMake. If it still fails, inspect the resulting `buildtrees/libsodium` full build log for a different cause; do not fabricate library source files or change cryptographic source code.
- **vcpkg dependencies take too long or break:** The entire project and SDK are large. Record full `VCPKG_SHA`; rerun with that exact SHA for reproducibility. Free hosted runner has finite disk, RAM and job limits.
- **Source patch refuses to run:** Upstream changed the data-path function. This is deliberate. Inspect actual new source before rewriting the patch; do not add blind substitutions.
- **Launcher refuses to run:** It requires NTFS/ReFS, no symlink/junction Data, packaged application executable, no other `MEGAsync.exe`, and a working job object. Installed MEGAsync must be fully exited, not just its window closed.
- **Qt platform error (`qwindows.dll`):** windeployqt output incomplete or runtime package mismatch. Do not copy DLLs from random installed application directories.
- **App reports missing updater or shell extension:** Updater and Explorer shell registration are intentionally excluded; source runtime behavior is not fully adapted yet. Do not run upstream installer inside the portable root.
- **Sync folders missing after moving:** Stop syncs before proceeding. Drive-specific absolute paths can cause unintended sync changes.
- **Installer fails after ZIP success:** The workflow preserves the independent ZIP as a diagnostic artifact, marks job failed, and skips publication. Use packaging-only workflow only with the exact original ZIP digest.
- **Notification failure or host registry traces:** Capture evidence with ProcMon and compare to installed app. Never clean shared keys or existing shortcuts indiscriminately.
- **Public release issue:** Check MEGA's non-commercial licence, trademark restrictions and dependency notices. The kit never claims official signing or PortableApps certification.

- **Main Actions workflow appears under filename and fails in ~1 second (b1r3):** GitHub Actions workflow parser rejects `${{ runner.temp }}` under `jobs.build.env` (`Unrecognized named-value: 'runner'`). b1r4 moves directory initialization to a job step using `$env:RUNNER_TEMP` and exports paths with `$env:GITHUB_ENV`. A plain YAML parser alone cannot catch this GitHub-specific error. Commit and push the full b1r4 kit before rerunning; old failed attempts remain visible in run history.

- **MEGAsync source compile fails with C2220 + C4996 / STL4043 in `xutility` (b1r4):** `QtCore/qstringlist.h`/`qlist.h` uses the deprecated MSVC `stdext::checked_array_iterator`, triggering a warning that the project's `/WX` turns fatal during `MegaIgnoreManager.cpp`. b1r5 applies an exact-source CMake adapter scoped to the `MEGAsync` target on MSVC: `_SILENCE_STDEXT_ARR_ITERS_DEPRECATION_WARNING`. It does not disable warning-as-error or broader deprecation warnings. If the source anchor changes, the build fails before compiling; inspect the exact upstream revision instead of bypassing safeguards. This remedy has local fixture coverage only until another Windows build succeeds.

- **Adaptive MSVC/Qt preflight fails (b1r6 onward):** Inspect `mega-qt-compat/baseline/cmake-configure.log` and `cmake-build.log` in the GitHub runner job logs. The preflight tests a real Qt `QList<QString>` comparison with `/WX` on the same MSVC toolchain. If the failure is STL4043/C4996, the targeted test must compile before the patch is applied. If compiler `C2039` says `stdext::make_checked_array_iterator` is absent (MSVC STL 14.51+), suppression is insufficient; use a verified compatible toolset/Qt build. Unknown warnings and errors are not silenced. `out/compiler-compatibility.json` captures the classification and reported compiler version when available. A passing preflight is not full MEGAsync compilation or a portability test.

- **b1r6 dynamic preflight passes targeted STL4043 probe but reports `Upstream MEGAsync compile-definition structure changed`:** The original source adapter required one `target_compile_definitions(MEGAsync ...)` command even though official `v6.7.1.0_Win` uses two (a PUBLIC block and a conditional PRIVATE Breakpad block). **b1r7 fixes this false guard**: it validates exactly one Windows executable declaration, inserts one conditional `PRIVATE` macro and preserves all existing compile definitions. An unknown target layout still fails closed.

- **b1r8 WindowsApp preflight stops with C2065 `E_FAIL` undeclared in `scripts/winrt_link_probe/probe.cpp`:** The probe omitted the SDK header that declares `E_FAIL`; this is a compile failure and **does not show that WindowsApp.lib is missing or broken**. b1r9 explicitly includes `<winerror.h>` and adds a header regression test. Re-run the full workflow unpublished; the WindowsApp probe must first compile and link successfully before vcpkg and the actual MEGAsync build continue.

- **b1r7 link fails with `DesktopManager.obj` LNK2019 `WINRT_IMPL_RoGetActivationFactory` / `WINRT_IMPL_RoOriginateLanguageException`:** The application is missing the documented Windows SDK `WindowsApp.lib` import library on its own MEGAsync link line. **b1r8** performs a real Windows SDK C++/WinRT compile-and-link probe before vcpkg and, only after it passes, adds target-private `WindowsApp` linkage on MSVC in the official Windows app CMake branch. If the probe fails, obtain `winrt-link-compatibility-diagnostics` from that run; do not suppress linker errors or disable Windows Runtime functionality. A probe pass does not guarantee the whole MEGAsync application links successfully.
