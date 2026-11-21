# MEGA Desktop Community PortableApps Builder Kit — b1r9 (experimental, NOT yet runtime verified)

**Mode:** PORTABLEAPPS only. **Upstream:** https://github.com/meganz/MEGAsync. This repository is an INDEPENDENT, community source-build project and is not affiliated with or endorsed by MEGA Limited or PortableApps.com.

**Important:** This ZIP is the *builder SOURCE KIT*, not an already compiled MEGA Desktop executable. The earlier b1r4 workflow and the b1r6 Qt/MSVC preflight were executed on Windows GitHub Actions runners (see uploaded diagnostics), and the b1r7 source compilation reached final linking (see the uploaded log); the b1r8 Windows run reached the WindowsApp test and failed during probe compilation due to an undeclared `E_FAIL`. The full upstream Qt/SDK build could fail because of dependency or GitHub hosted-runner limitations. The delivered solution cannot be considered successfully working until the GitHub workflow and interactive Windows acceptance tests pass. `publish_release` defaults to **false** for legal and runtime-safety reasons.

## What is included

- `.github/workflows/build-portableapps.yml`: independent official-tag discovery, pinned upstream source + SDK checkout, exact source data path patch, vcpkg/Qt setup, actual app source build, genuine MSVC C++ root launcher, completed PortableApps folder and validated ZIP, shared installer, dry-run, optional publication.
- `.github/workflows/packaging-only.yml`: reuses a **known, original validated ZIP** from a release in this builder repo with mandatory SHA-256 verification and no upstream recompilation.
- `launcher/main.cpp` and `launcher/CMakeLists.txt`: real compiled Win64 launcher with pre-launch portable profile, job child tracking and simultaneous installed MEGA process guard. No host registry cleanup and no fake EXE.
- `scripts/detect_msvc_qt_compat.py` and `scripts/qt_msvc_probe/`: real MSVC `/WX` compiler probes using the downloaded Qt SDK and Qt's `QList<QString>::operator==`. Leave the target unchanged when compatible; apply a verified fix only after diagnosing the exact known STL4043 failure.
- `scripts/patch_msvc_qt_compat.py`: target-only, fail-closed compatibility adapter called **conditionally by the Qt probe**, never unconditionally by the workflow.
- `scripts/ensure_winrt_link.py`, `scripts/winrt_link_probe/`, and `scripts/patch_winrt_link.py`: Windows SDK C++/WinRT **compile + link** preflight, target-private `WindowsApp` linkage when verified necessary, and failure diagnostics before expensive vcpkg work.
- `scripts/patch_source.py`: fail-closed source adapter for `src/MEGASync/MegaApplication.cpp` `loadDataPath()`; preserves MEGA's native profile ACL routine. Does not tamper with installed MEGA data.
- `scripts/resolve.py`: numeric Windows stable-release selection; rejects RC/prereleases, non-Windows tags, drafts and missing requested versions.
- `scripts/stage.py`, `scripts/make_icons.py`, `scripts/packaging_only.py`: genuine PE tests, original community icons (not MEGA artwork), Qt deployment, vcpkg DLL packaging, layout and ZIP validation, SHA-256 and provenance.
- `scripts/verify_vcpkg_path.py`: fail early if Windows MSBuild dependency paths are too long.
- `scripts/verify_vcpkg_checkout.py`: require a full-history, non-partial vcpkg checkout before CMake configure; catches incomplete version-tree checkouts early.
- `tests/`: 48 deterministic **static/fixture** tests covering dynamic preflight decisions, compiler source patching, workflow integration, vcpkg checkout, and regression safety. These are not Windows MSVC, GUI or portability acceptance tests.
- `docs/`: audit, licensing, procedure, limitations, release safety and Windows acceptance checklist.

## b1r9: fix the WindowsApp compiler probe (21 Nov 2026)

**FAILED/BLOCKED (real user Windows run):** `logs_121566860828.zip` and
`winrt-link-compatibility-diagnostics.zip` show that the b1r8 probe's CMake
configuration passed on VS 2022/MSVC 19.44 and Windows SDK 10.0.26100.0,
but compiling `scripts/winrt_link_probe/probe.cpp` stopped at:
`error C2065: 'E_FAIL': undeclared identifier` (line 13). No WindowsApp
linking, application compilation or package construction occurred in that run.
This is a missing explicit header in the community probe, *not* a WindowsApp
import-library failure. Microsoft's Windows SDK defines `E_FAIL` in `winerror.h`.

**b1r9 correction:** Explicitly `#include <winerror.h>` before the C++/WinRT
namespace headers. Preserve the genuine WinRT activation and exception paths
and the actual `target_link_libraries(... WindowsApp)` link test; do not create
stub WinRT implementations or skip compilation. Regression tests now assert
that the SDK header precedes `E_FAIL` and that both paths are still exercised.
The WindowsApp test, full application build, launcher, installer and real sync
are **NOT YET VERIFIED for b1r9**.

## b1r8: WindowsApp C++/WinRT linkage (21 Nov 2026)

**FAILED/BLOCKED evidence:** `logs_121549679805.zip` shows the b1r7 source build
progressing past vcpkg, the conditional STL4043 Qt/MSVC fix, and nearly all
MEGAsync sources. Its final **linker** failed with exactly two `LNK2019`
references from `DesktopManager.obj`: `WINRT_IMPL_RoGetActivationFactory` and
`WINRT_IMPL_RoOriginateLanguageException` (`LNK1120`). The actual upstream
`v6.7.1.0_Win/src/MEGASync/platform/win/DesktopManager.cpp` uses the Windows
SDK C++/WinRT TaskbarManager API. Microsoft's Windows C++/WinRT documentation
requires linking to the **WindowsApp.lib** umbrella import library.

**b1r8 correction:** `scripts/winrt_link_probe/` compiles and links a small
Windows SDK C++/WinRT sample against `WindowsApp` on the actual Windows x64
MSVC runner, after the Qt compatibility probe but **before** costly vcpkg
compilation. It does **not** execute Windows Runtime APIs. If the link probe
fails, the job fails closed and uploads `winrt-link-compatibility-diagnostics`.
If it passes, `scripts/patch_winrt_link.py` verifies the upstream Windows
MEGAsync target, checks source-level WinRT usage, and adds only
`target_link_libraries(MEGAsync PRIVATE WindowsApp)` inside the Windows MSVC
branch. It does not overwrite upstream library declarations, alter the
SDK, disable notifications/taskbar support, or silence linker errors. If
upstream already links WindowsApp, the adapter leaves the target unchanged.
An upstream target rename or missing evidence is reported, not guessed.

The JSON report `out/winrt-link-compatibility.json` is packaged alongside
`out/compiler-compatibility.json` and embedded as
`Other/Source/WINRT-LINK-COMPATIBILITY.json` in a validated ZIP. All runtime
portability and GUI behavior remain **NOT YET VERIFIED**. Passing a miniature
link probe cannot prove the complete application links or runs.

## b1r7: handle real upstream CMake definition structure (21 Nov 2026)

The user's b1r6 Windows run reached the **real** Qt/MSVC preflight: baseline failed with
`C4996` / `STL4043` as expected and the targeted recompile **succeeded** using
`_SILENCE_STDEXT_ARR_ITERS_DEPRECATION_WARNING`. The run then failed in our source
adapter, which incorrectly required exactly one `target_compile_definitions(MEGAsync...)`
command. Official `v6.7.1.0_Win` has TWO valid commands: the main `PUBLIC` target
definitions and a `PRIVATE CRASH_BACKEND_URL` within `if(USE_BREAKPAD)`.

b1r7 verifies the **unique Windows `add_executable(MEGAsync WIN32)` declaration**
and inserts the conditional `PRIVATE` definition immediately after it, leaving all
upstream compile definitions untouched (including Breakpad). It tolerates harmless
whitespace changes but fails closed on missing, duplicate, or unexpectedly renamed
Windows targets. The macro is still applied **only** when the actual Windows
compiler proves the specific issue and the targeted test passes. Regression
fixtures replicate the two upstream definition blocks. The b1r7 user-run log confirms this Qt patch reached the final Windows
application link stage; linker errors prevented a finished executable. The
launcher, installer and runtime still require separate verification.

## b1r6/b1r7 adaptive compiler compatibility (21 Nov 2026)

After the real Qt download and **before vcpkg** (to avoid a costly dependency compile on known toolchain incompatibility), the workflow compiles an isolated Qt `QList<QString>::operator==` probe twice *only when needed*, using the same MSVC Visual Studio 2022 generator and Qt Core package. The `/WX` warning-as-error policy is preserved. Results:

1. **Baseline compiles:** no source patch is applied.
2. **Baseline fails explicitly with STL4043/C4996 and checked_array_iterator:** recompile the same probe with the specific `_SILENCE_STDEXT_ARR_ITERS_DEPRECATION_WARNING` definition; apply the target-specific upstream patch only if that second compile succeeds.
3. **Missing MSVC API or unknown failure:** stop before vcpkg; do not automatically weaken warning handling or patch application code.

The workflow writes `out/compiler-compatibility.json`, and the independently validated ZIP embeds it under `Other/Source/COMPILER-COMPATIBILITY.json`. This records the detected Qt and compiler versions, whether any patch was applied, and the verification stage. Probe build logs remain in the runner's short temporary build directory. **A successful preflight is not proof that the entire application compiles.** Future versions may introduce unrelated breaking changes and still require a builder revision.

## Historical b1r5 fixed compiler compatibility remedy (21 Nov 2026)

`logs_121526272643.zip` shows the **b1r4 workflow now runs and compiles the MEGA SDK**. The previous vcpkg/lib­sodium errors are absent. The `MEGAsync` target then fails while compiling `syncs/control/MegaIgnoreManager.cpp` because Qt 5.15.2's `QList` headers instantiate deprecated `stdext::checked_array_iterator` from Microsoft STL (`xutility`), producing **STL4043 / C4996**. Upstream MEGAsync treats warnings as errors (`C2220`). This is a build-toolchain compatibility problem, not evidence of faulty sync logic.

The existing `scripts/patch_msvc_qt_compat.py` adapter applies a **target-verified, fail-closed** CMake source adapter to `src/MEGASync/CMakeLists.txt`. It adds `_SILENCE_STDEXT_ARR_ITERS_DEPRECATION_WARNING` **only to the `MEGAsync` target and only when building with MSVC**. It does **not** disable `/WX`, does **not** broadly disable `C4996`, and does **not** modify cryptography or synced-file algorithms. The workflow calls this patch conditionally, only after the real compiler probe has established that it is needed and works. Multiple deterministic source-patch regression tests check the change and reject unexpected upstream drift. The b1r7 Windows log confirms compilation reached the final application link stage; executable linking did not succeed.

## b1r4 GitHub Actions workflow registration fix

b1r3 introduced three `${{ runner.temp }}` expressions under `jobs.build.env` while shortening vcpkg/Qt/source paths. **GitHub rejects that syntax before allocating a Windows runner**, even though the file passes ordinary YAML parsing. It may display the filename `.github/workflows/build-portableapps.yml` instead of the declared workflow name and fail in approximately one second.

b1r4 keeps the same short paths but initializes `QT_ROOT`, `SOURCE_ROOT` and `BUILD_ROOT` in the first PowerShell step *after checkout*, using Windows' `RUNNER_TEMP` variable. The step writes those values into `GITHUB_ENV` for subsequent steps. Added focused GitHub expression-context regression tests. This fixes the invalid-workflow declaration, **not** the unverified application compilation or runtime portability. Existing failed runs remain in GitHub Actions history.

## Prerequisites

- A new standalone GitHub repository containing this kit, public or private at your discretion.
- GitHub Actions enabled, GitHub-hosted Windows runners and access to GitHub/Qt/vcpkg dependencies.
- No local compiler, no Git command-line initialization, no installed MEGA required to trigger CI.
- For published builds, a genuine **non-commercial** use/distribution right, compliance with MEGA's licence and third-party notices. The publisher is opt-in.

## GitHub Desktop quick start

1. On GitHub, create a **new repository** such as `MEGAsync-Community-PortableApps-Builder`. Do **not** fork `meganz/MEGAsync`.
2. Consider **Private** initially, while checking runtime and licensing. In GitHub Desktop select **File → Clone Repository**, select this new repo.
3. Extract the builder ZIP into the CLONED REPOSITORY ROOT (not into an extra subfolder). Enable hidden files so `.github/workflows` is copied intact.
4. In GitHub Desktop check all files, enter commit summary `Fix missing WinRT probe E_FAIL SDK header - b1r9`, commit, then **Push origin**.
5. Open GitHub repository → **Actions** → `MEGA Desktop Community PortableApps - source build` → **Run workflow**. Leave `upstream_version` blank to choose the newest stable Windows tag; set `publish_release=false` for the first build.
6. Follow each step's green/red status. A failed `Install verified-route Qt`, `Build actual MEGA Desktop application`, or `Stage and independently validate ZIP` step indicates no complete package; do not use partial outputs.
7. On success and publish disabled, download the workflow artifact from the completed run. It contains the ZIP, installer, `ZIP-SHA256.txt`, `compiler-compatibility.json`, and `winrt-link-compatibility.json`. On preflight failure, download `qt-msvc-compatibility-diagnostics` or `winrt-link-compatibility-diagnostics` to inspect the relevant compiler/linker logs. The app package is **not** this builder ZIP.
8. Extract `MEGAsyncPortable_...zip` to an NTFS or ReFS folder and start **MEGAsyncPortable.exe**. Alternatively run the independent `.paf.exe` installer after separate installer acceptance.
9. After complete Windows acceptance (see `docs/WINDOWS-TESTING.md`), you can rerun using `publish_release=true`, but ONLY if non-commercial distribution and notices are authorised. Then check your own repository's **Releases** section.

## Portable data and upgrades

The launcher passes an absolute `MEGA_PORTABLE_DATA_DIR` before app startup. The patch in MEGA's own `loadDataPath` uses it to store MEGAsync configuration, sessions and logs under:

    MEGAsyncPortable\Data\MEGAsync\

That path is excluded from code/installer overwrites. **Do not delete Data**, move an actively syncing folder, or assume portable profile credentials remain valid on another Windows account. `Data/MEGAsync` contains login material and should be secured. The launcher rejects FAT/exFAT and checks for potentially unsafe symlink/junction directories. It refuses to start if any other MEGAsync.exe is running.

For upgrades, fully exit the app from the tray and ensure all MEGA processes are stopped. Make a full backup of the portable folder (and separately back up external synced files). Replace app binaries or use an independently tested installer WITHOUT deleting `Data`. Roll back the same way, but app database schema downgrades may be incompatible; always keep pre-upgrade backups. Moving drives may invalidate synced-folder paths. **Never enable automatic two-way sync after moving until mapped local folders are verified.** Wrong mappings can result in cloud/local deletions.

This builder does **not** perform implicit migration from the installed app, does **not** create host autostart, does **not** register shell extensions, and does **not** promiscuously harvest AppData or registry keys.

## Testing and trust

The earlier b1r2 revision fixed the b1r1 GitHub Actions failure logged on 21 Nov 2026: vcpkg was obtained with `--filter=blob:none`, causing on-demand historical port Git object downloads to fail when GitHub DNS was unavailable. It now uses `git clone --no-single-branch` (full history), checks SHA and non-partial/non-shallow status before CMake. A network outage while fetching the full clone can still fail, but no CMake work is attempted until the clone is structurally verified.

b1r3 addresses the subsequent `logs_121516712196.zip` failure: libsodium 1.0.20#3 MSBuild could not open two C sources. The failing uncollapsed compiler path is 264 characters long under GitHub's `D:\a\Repo\Repo` checkout. b1r3 puts the full-history vcpkg checkout into the job-local short `RUNNER_TEMP\vcpkg` and keeps upstream source/Qt/build directories under the short runner temp root, performs a strict path-length preflight before clone, retains exact vcpkg SHA verification, and uses the source-evidenced `x64-windows-mega` target triplet when staging DLLs. Windows verification is still pending.

The local authoring tests included: Python syntax, resolver test fixtures, patch fail-closed fixtures, vcpkg Git history fixtures, static C++ launcher text checks, and workflow YAML parsing. **Windows application compilation, launcher runtime, Qt dependencies, GUI, notifications, actual sync, installer use and release publication have NOT been performed in this environment.** See `docs/EVIDENCE.md`.

**Critical limitations:** MEGA Desktop upstream has an app-specific restrictive **non-commercial** source licence, not an ordinary open-source licence. Custom community cloud icon is included in place of MEGA's trademarked logo. The application itself may still contain MEGA's official assets, so redistribution rights and branding require independent review. Shell/runtime traces, integrated updater and framework caches are not fully audited with runtime evidence. If any unexpected host modification occurs, stop and file evidence before using this build with valuable synced files.

## References

- MEGA code: https://github.com/meganz/MEGAsync
- Windows source build: https://github.com/meganz/MEGAsync/blob/v6.7.1.0_Win/README.win.md
- MEGA specific licence: https://github.com/meganz/MEGAsync/blob/v6.7.1.0_Win/LICENCE.md
- Shared installer action: https://github.com/vhick/Portable-Package-Builder/blob/v1.0.0/action.yml
- Shared publisher action: https://github.com/vhick/portable-release-publisher/blob/v1.1.1/action.yml

Read `docs/AUDIT.md`, `docs/WINDOWS-TESTING.md`, and `docs/EVIDENCE.md` before using real cloud data.
