# Application-specific upstream audit — MEGAsync v6.7.1.0_Win (21 Nov 2026)

Evidence levels: SOURCE-INSPECTED = examined upstream public code; INFERRED = dependency behavior remains unproved; NOT YET VERIFIED = no program execution evidence.

## Source provenance and compilation

- Official Windows release located: `v6.7.1.0_Win` (17 Nov 2026), release page https://github.com/meganz/MEGAsync/releases/tag/v6.7.1.0_Win . The release refers to commit `650c9a2` (abbreviated displayed upstream); workflows record full 40-character SHA at checkout.
- C++/Qt 5 application. Source `CMakeLists.txt` uses CMake; Windows `production_build.cmd` specifies VS2022 x64, vcpkg, `MEGAsync`, `MEGAupdater`, `MEGAShellExt` targets. We build **only the MEGAsync application** target and a separate independent root launcher, avoiding installation of the shell extension and updater binaries.
- `README.win.md` documents MSVC 2019/VS2019 and Qt 5.15.17 example plus vcpkg; newer production script uses VS2022, Qt 5.15.17. This kit fetches publicly available official Qt 5.15.2 via aqtinstall, so **compile compatibility with 6.7.1.0 is NOT VERIFIED**, especially if it uses newer private Qt 5.15.x features. Failure stops the pipeline: no fake fallback to downloaded installer.
- SDK git submodule is `src/MEGASync/mega` sourced from https://github.com/meganz/sdk.git ; checkout uses tracked commit, not moving master. vcpkg is resolved to full SHA at build; for reproducibility of repeat runs supply `vcpkg_commit` manually after first build.
- Source licence is `MEGA LIMITED CODE LICENCE` allowing permitted compatibility/portability modifications and non-commercial distribution, and NOT granting any trademark rights. See LICENSING.md.
- **Official developer portable Windows ZIP:** NOT ESTABLISHED. Official Windows installers and source releases do not establish a verified portable binary. This kit selects a full upstream-source build rather than unpacking the installed product.

## Findings table (selected PORTABLEAPPS mode only)

| Finding | Evidence | Path / key | Responsible component | NATIVE remedy | PORTABLEAPPS remedy | Data safety | Functionality tradeoff | Test | Limitation |
|---|---|---|---|---|---|---|---|---|---|
| Config, session and logs use Qt LocalAppData | SOURCE-INSPECTED `MegaApplication.cpp::loadDataPath`, `restrictDataPathPermissions` | Qt `QStandardPaths::AppLocalDataLocation`, default inferred `%LOCALAPPDATA%` | MEGA Desktop application | Not in selected mode | Exact source adaptation: `MEGA_PORTABLE_DATA_DIR` → `Data/MEGAsync`; use existing owner-only permission enforcement | Never import installed profile | Source patch must match upstream | Python fixture and manual ProcMon | Full Windows runtime unverified |
| App uses CWD after initializing app | SOURCE-INSPECTED `MegaApplication.cpp` constructor | Working directory set to `applicationDataPath` | MEGA Desktop | N/A | Data-path patch points CWD inside Data | Controlled | Some relative paths become portable | inspect logs and file I/O | Paths may remain outside profile |
| Tray process/background children | SOURCE-INSPECTED Qt tray constructor; INFERRED children | `MEGAsync.exe` and subprocesses | MEGA application | N/A | C++ CreateProcess suspended + job assignment + process wait | Avoid early data collection | Refuses when another MEGAsync process is running | User first-run/exit/tray | Processes escaping job unverified |
| Qt plugins and dynamic runtimes | SOURCE-INSPECTED build scripts/CMake; dynamic deployment INFERRED | `App/MEGAsync/` | Qt, vcpkg | N/A | windeployqt + vcpkg dynamic DLLs; PE verification | No AppData snapshot | More files and disk space | Windows compile/startup | Qt 5.15.2 vs upstream 5.15.17 uncertain |
| Explorer context menus and overlays | SOURCE-INSPECTED `installer_win.nsi`/production target; Windows MEGA issue corroboration | HKLM Explorer overlays, shell COM | Installer + shell extension | N/A | Don't run upstream installer or register extension | Leaves installed integration untouched | No portable Explorer context/overlays | Explorer before/after test | Not available in community build by design |
| Automatic updates / updater | SOURCE-INSPECTED separate `MEGAupdater` target in production script; runtime behavior INFERRED | install folder / update helper | MEGA updater | N/A | Do not bundle upstream updater target; releases update via builder | Prevent updater modifying portable binaries, unproved | In-app updater may show messages/fail | Manual update flow | Source-level auto-update trigger not fully inspected |
| Startup/login registration | INFERRED app installer/Preferences integration | HKCU Run / Startup unknown until runtime | MEGA app or installer | N/A | No launcher registration; leave user settings untouched | Protect installed entries | No opt-in portable autostart offered | Registry before/after | In-app startup setting may create host entry; needs testing |
| Notifications / AUMID | NOT YET VERIFIED | Windows-managed notification/shortcut state | Windows/Qt/MEGA | N/A | Preserve active notifications; no ShellGuard cleanup without provenance | No broad shell deletion | Click activation may differ | Windows GUI notification click test | No stable portable AUMID/CLSID proven |
| Sync roots (user files) | SOURCE-INSPECTED README sync behavior | User-chosen directories outside Data | Intended user data | N/A | Never redirect user sync roots automatically | Prevent changing/deleting synced files by default | Drive relocation requires explicit user review | Changed-drive test with dummy cloud folder | Cannot promise drive-safe sync mappings |
| Completely empty directories | SOURCE-INSPECTED main app path create; INFERRED external paths | Data/MEGAsync and unknown external trees | App/Qt | N/A | Data lives directly in portable folder; ZIP records empty Data directory, no external tree harvesting | Preserve empties in archive and Data upgrades | No external recovery until evidence | ZIP empty-folder fixture, ProcMon | Residual external empty folders not yet enumerated |
| Credentials and restricted ACL | SOURCE-INSPECTED `restrictDataPathPermissions` comments | `Data/MEGAsync` | MEGA + NTFS | N/A | Use original MEGA ACL routine and require NTFS/ReFS | No flattening/weakening secrets | exFAT/FAT unsupported | Move/login test | Re-auth across accounts may be required |
| Installer-only registry changes | SOURCE-INSPECTED upstream installer definition | uninstall, App Paths, shell integrations | Upstream NSIS installer | N/A | Never execute upstream installer; custom portable installer action alone | No system-wide install side effects desired | Shell integration unavailable | Before-first-run diff and actual reinstall | Shared action behavior requires specific Windows test |

## Data redirection mechanism

Source: `src/MEGASync/MegaApplication.cpp`:

- Existing function: `void MegaApplication::loadDataPath()` with an `#else` Windows branch assigning `QStandardPaths::AppLocalDataLocation`.
- Safe change: detect `qEnvironmentVariable("MEGA_PORTABLE_DATA_DIR")`, demand an absolute path, set `dataPath` and `dataPathFromStandardLocation=true`, then call `Platform::getInstance()->createFolderRestrictedToOwner` and return. This preserves restrictive-folder behavior.
- The compiled root launcher starts the actual source-built `MEGAsync.exe` only after setting that variable to a path based on its *own running EXE*, never current CWD.
- This does NOT globally remap `%LOCALAPPDATA%`, `%APPDATA%`, `%TEMP%` or `HKCU`.

## Shell/TraceGuard decision

TraceGuard and ShellGuard are intentionally **not implemented** in b1r1. Evidence currently supports direct redirection for main profile but does NOT establish bounded, exact-owned registry keys/files/shortcuts created at runtime. Scavenging guessed keys, wiping Explorer caches or moving pre-existing MEGA AppData would risk installed-app data. CI cannot verify actual shell history or Qt child writes. Do not interpret absent cleanup as 'zero host traces'. A later source- and runtime-evidenced expansion must be tested against owned and pre-existing same-name fixtures before touching host state.

## Known external dependencies and behaviors

- Windows 10+ (not tested here), VC++/Qt runtime as assembled; source build uses VS2022 toolchain.
- OS-managed thumbnail caches, notification history, firewall records, file picker history, SRUM/WER, and app compat records are outside the app's contractual control.
- Windows Explorer shell overlays not installed intentionally.
- Normal cloud sync involves local files OUTSIDE portable `Data`; preserving Data does not protect synced content from errors, relocations or user-initiated deletion.
