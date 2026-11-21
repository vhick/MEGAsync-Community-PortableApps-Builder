# Troubleshooting

- **Workflow absent:** Push the `.github/workflows` folder to default branch, enable Actions on GitHub, ensure ZIP not extracted into a nested folder.
- **Stable release lookup fails:** Check GitHub API status/token; a 404 from a requested version is a real failure; no fallback to unverified master. Specify `v6.7.1.0_Win` or a newer exact stable Windows tag.
- **Qt download or CMake configure fails:** Upstream's internal Windows recipe references Qt 5.15.17; the kit uses public Qt 5.15.2. This is a known compatibility risk. Do not downgrade security or bypass compile errors. Save logs and compare upstream `README.win.md` with current CMake requirements.
- **vcpkg dependencies take too long or break:** The entire project and SDK are large. Record full `VCPKG_SHA`; rerun with that exact SHA for reproducibility. Free hosted runner has finite disk, RAM and job limits.
- **Source patch refuses to run:** Upstream changed the data-path function. This is deliberate. Inspect actual new source before rewriting the patch; do not add blind substitutions.
- **Launcher refuses to run:** It requires NTFS/ReFS, no symlink/junction Data, packaged application executable, no other `MEGAsync.exe`, and a working job object. Installed MEGAsync must be fully exited, not just its window closed.
- **Qt platform error (`qwindows.dll`):** windeployqt output incomplete or runtime package mismatch. Do not copy DLLs from random installed application directories.
- **App reports missing updater or shell extension:** Updater and Explorer shell registration are intentionally excluded; source runtime behavior is not fully adapted yet. Do not run upstream installer inside the portable root.
- **Sync folders missing after moving:** Stop syncs before proceeding. Drive-specific absolute paths can cause unintended sync changes.
- **Installer fails after ZIP success:** The workflow preserves the independent ZIP as a diagnostic artifact, marks job failed, and skips publication. Use packaging-only workflow only with the exact original ZIP digest.
- **Notification failure or host registry traces:** Capture evidence with ProcMon and compare to installed app. Never clean shared keys or existing shortcuts indiscriminately.
- **Public release issue:** Check MEGA's non-commercial licence, trademark restrictions and dependency notices. The kit never claims official signing or PortableApps certification.
