Before login, verify `App\MEGAsync` contains all five `.rcc` files and `Other\Source\RCC-RESOURCE-MANIFEST.json` lists their SHA-256 checksums. Check `MEGAsyncPortable.exe` shows the same community icon in Windows Explorer and the PortableApps Platform. If application resources fail to load, do NOT create or modify live sync jobs; collect logs and verify the packaged files.

# Manual Windows acceptance procedure (required before use or publication)

Use a disposable Windows 10/11 test profile and a test MEGA account with **unimportant** files. Before testing, back up all local and cloud folders. Do not validate a brand-new build against production sync data.

1. Inspect build logs for tagged upstream SHA, SDK SHA, vcpkg SHA, successful source build, independently verified compiled 64-bit `MEGAsync.exe` and `MEGAsyncPortable.exe`, intact ZIP and shared installer SHA. A green workflow does NOT prove the steps below.
2. Use a test NTFS path containing spaces and Unicode, e.g. `C:\Temp\Portátil Prueba\MEGAsyncPortable`. Launch root `MEGAsyncPortable.exe` from an unrelated CWD. Verify sign-in, menus, icons, tray startup, status and exit.
3. Verify **all** persistent app configuration and cache state with Windows Process Monitor (ProcMon). Filter for app process tree and inspect file/registry writes before and after launch, and check `Data\MEGAsync` credentials, session and logs. Verify no `LOCALAPPDATA\Mega Limited\MEGAsync` profile was moved/altered. If paths elsewhere appear, mark portability FAILED and do not publish until owner attribution is known.
4. Create nested `Data\MEGAsync\a\b` empty directories, close the application, update the ZIP/app binaries without touching Data; verify empty directories survive. Repeat with actual profile files and a killed process; the build has no external recovery scavenger.
5. Simultaneous installed app check: start an installed MEGAsync, attempt portable start, expect the compiled root launcher to refuse; stop installed app gracefully. Verify installed profile byte hashes, registry and shortcuts remain unchanged.
6. Test a controlled two-way sync (test data only), a one-way backup and selective sync. Pause and resume. Exit from tray while synchronizing and observe process descendants. Verify launcher does not exit early, and does not kill unfinished sync with no warning.
7. Test status notifications, clicking toast notifications, taskbar identity, credential persistence, file dialogs and share links. Report any AUMID/CLSID or shell state created. Do not delete registry keys or shortcuts without ownership evidence.
8. Before first run, snapshot HKCU Run, user Start Menu, App Paths, Explorer overlay keys and HKCU class registrations. Repeat during app runtime, after tray exit and after a power-cycle. Keep the separate installed client and its shell extensions intact.
9. Relocate to different NTFS folder and change drive letter; ensure linked local sync roots still point to correct folders before resuming. If not, safely **disable affected sync**, do not let it propagate deletions to cloud.
10. Perform a custom-NSIS installer run in an isolated test profile. Verify it installs to the expected folder, has no unauthorized autorun/shell integration, and launches the compiled root launcher. Reinstall an upgrade with existing Data and nested empty directories; verify no Data deletion and no installed-app configuration changes.
11. Test rollback with a complete pre-upgrade backup, acknowledging MEGA database migration may prohibit downgrading. Test with read-only Data, locked files, account switch and insufficient space. Preserve all backups through test.
12. Compare process/file/registry traces before and after every test, and record differences with owning component. Mark failed evidence and restrict publication unless all contractual requirements pass.

Avoid ProcMon against valuable installed profiles or real cloud data. The native notification, tray, Explorer and sync interactions cannot be reliably proven on a headless GitHub runner.

## WinRT linking and shell behavior (b1r9)

- In GitHub Actions, confirm `Verify WindowsApp C++/WinRT linkage and source adapter` completes with `WINDOWS-COMPILED-LINK-PROBE`, then confirm the full application `MEGAsync.exe` link succeeds independently. The miniature probe must never be presented as a full application build.
- Confirm portable and separately installed MEGA Desktop applications' tray and notification identities are not mixed. Observe taskbar pin requests and toast click activation under a regular (non-elevated) Windows account. Do not automatically approve shell registration or taskbar pinning.
- Audit and compare Windows registry, Start Menu, Explorer, and host AppData before/after launch; do not delete ambiguous or pre-existing items. Record remaining traces; these tests cannot run in a headless GitHub Actions job.


## b1r15 targeted Qt cache acceptance (mandatory interactive Windows test)

- **Before launch:** close all installed and portable MEGA clients. Snapshot file names and hashes (including empty directories) under `%LOCALAPPDATA%\Mega Limited\MEGAsync\cache\qmlcache` and `%LOCALAPPDATA%\cache\qtshadercache-*`. Never delete these paths.
- Start the rebuilt root `MEGAsyncPortable.exe` from a movable NTFS folder; inspect `Data\Cache\QML` for new .qmlc files after UI use and restart. The child environment should provide `QML_DISK_CACHE_PATH` before Qt initialization.
- Check no **new** attributed MEGA QML cache files appear at the old host path. Observe the shader cache using ProcMon; with Qt's disk-cache disable flags, no persistent shader files should be generated. Whether an empty directory still appears must be verified on the actual Windows runtime.
- Test a path containing spaces, and separately a Unicode path: the latter intentionally disables optional QML disk caching rather than falling back to LocalAppData on Qt 5.15.
- Compare installed-app profile and cache snapshots before and after launch. Do not delete or move shared host cache files. Test a disposable sync job, restart and tray exit, and monitor Qt descendant processes for unexpected cache activity.
- If either old host location continues receiving new files attributable to portable MEGA, mark containment **FAILED** and supply ProcMon/file logs; do not claim perfect portability.
