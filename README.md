# MEGA Desktop Community PortableApps Builder Kit — b1r3 (experimental, NOT yet runtime verified)

**Mode:** PORTABLEAPPS only. **Upstream:** https://github.com/meganz/MEGAsync. This repository is an INDEPENDENT, community source-build project and is not affiliated with or endorsed by MEGA Limited or PortableApps.com.

**Important:** This ZIP is the *builder SOURCE KIT*, not an already compiled MEGA Desktop executable. The submitted workflows have not been executed on Windows by the kit author. The full upstream Qt/SDK build could fail because of dependency or GitHub hosted-runner limitations. The delivered solution cannot be considered successfully working until the GitHub workflow and interactive Windows acceptance tests pass. `publish_release` defaults to **false** for legal and runtime-safety reasons.

## What is included

- `.github/workflows/build-portableapps.yml`: independent official-tag discovery, pinned upstream source + SDK checkout, exact source data path patch, vcpkg/Qt setup, actual app source build, genuine MSVC C++ root launcher, completed PortableApps folder and validated ZIP, shared installer, dry-run, optional publication.
- `.github/workflows/packaging-only.yml`: reuses a **known, original validated ZIP** from a release in this builder repo with mandatory SHA-256 verification and no upstream recompilation.
- `launcher/main.cpp` and `launcher/CMakeLists.txt`: real compiled Win64 launcher with pre-launch portable profile, job child tracking and simultaneous installed MEGA process guard. No host registry cleanup and no fake EXE.
- `scripts/patch_source.py`: fail-closed source adapter for `src/MEGASync/MegaApplication.cpp` `loadDataPath()`; preserves MEGA's native profile ACL routine. Does not tamper with installed MEGA data.
- `scripts/resolve.py`: numeric Windows stable-release selection; rejects RC/prereleases, non-Windows tags, drafts and missing requested versions.
- `scripts/stage.py`, `scripts/make_icons.py`, `scripts/packaging_only.py`: genuine PE tests, original community icons (not MEGA artwork), Qt deployment, vcpkg DLL packaging, layout and ZIP validation, SHA-256 and provenance.
- `scripts/verify_vcpkg_path.py`: fail early if Windows MSBuild dependency paths are too long.
- `scripts/verify_vcpkg_checkout.py`: require a full-history, non-partial vcpkg checkout before CMake configure; catches incomplete version-tree checkouts early.
- `tests/`: small deterministic **static/fixture** tests; these are not GUI or portability acceptance tests.
- `docs/`: audit, licensing, procedure, limitations, release safety and Windows acceptance checklist.

## Prerequisites

- A new standalone GitHub repository containing this kit, public or private at your discretion.
- GitHub Actions enabled, GitHub-hosted Windows runners and access to GitHub/Qt/vcpkg dependencies.
- No local compiler, no Git command-line initialization, no installed MEGA required to trigger CI.
- For published builds, a genuine **non-commercial** use/distribution right, compliance with MEGA's licence and third-party notices. The publisher is opt-in.

## GitHub Desktop quick start

1. On GitHub, create a **new repository** such as `MEGAsync-Community-PortableApps-Builder`. Do **not** fork `meganz/MEGAsync`.
2. Consider **Private** initially, while checking runtime and licensing. In GitHub Desktop select **File → Clone Repository**, select this new repo.
3. Extract the builder ZIP into the CLONED REPOSITORY ROOT (not into an extra subfolder). Enable hidden files so `.github/workflows` is copied intact.
4. In GitHub Desktop check all files, enter commit summary `Add MEGA Desktop Community PortableApps Builder b1r3`, commit, then **Push origin**.
5. Open GitHub repository → **Actions** → `MEGA Desktop Community PortableApps - source build` → **Run workflow**. Leave `upstream_version` blank to choose the newest stable Windows tag; set `publish_release=false` for the first build.
6. Follow each step's green/red status. A failed `Install verified-route Qt`, `Build actual MEGA Desktop application`, or `Stage and independently validate ZIP` step indicates no complete package; do not use partial outputs.
7. On success and publish disabled, download the workflow artifact from the completed run. It contains the ZIP, installer, and ZIP-SHA256.txt. The app package is **not** this builder ZIP.
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

The Linux/container-based authoring tests completed: Python syntax, resolver test fixtures, patch fail-closed fixtures, vcpkg Git history fixtures, static C++ launcher text checks, and workflow YAML parsing. **Windows application compilation, launcher runtime, Qt dependencies, GUI, notifications, actual sync, installer use and release publication have NOT been performed in this environment.** See `docs/EVIDENCE.md`.

**Critical limitations:** MEGA Desktop upstream has an app-specific restrictive **non-commercial** source licence, not an ordinary open-source licence. Custom community cloud icon is included in place of MEGA's trademarked logo. The application itself may still contain MEGA's official assets, so redistribution rights and branding require independent review. Shell/runtime traces, integrated updater and framework caches are not fully audited with runtime evidence. If any unexpected host modification occurs, stop and file evidence before using this build with valuable synced files.

## References

- MEGA code: https://github.com/meganz/MEGAsync
- Windows source build: https://github.com/meganz/MEGAsync/blob/v6.7.1.0_Win/README.win.md
- MEGA specific licence: https://github.com/meganz/MEGAsync/blob/v6.7.1.0_Win/LICENCE.md
- Shared installer action: https://github.com/vhick/Portable-Package-Builder/blob/v1.0.0/action.yml
- Shared publisher action: https://github.com/vhick/portable-release-publisher/blob/v1.1.1/action.yml

Read `docs/AUDIT.md`, `docs/WINDOWS-TESTING.md`, and `docs/EVIDENCE.md` before using real cloud data.
