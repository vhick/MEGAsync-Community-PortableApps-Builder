# GitHub Desktop commit information

Suggested repository: `MEGAsync-Community-PortableApps-Builder` (independent of upstream).

Commit summary:
`Fix WindowsApp WinRT linker dependency - b1r8`

Description:
`Fix the b1r6 adaptive Qt/MSVC compatibility preflight source-patch failure.

The real Windows compiler baseline reports STL4043/C4996, and the targeted compatibility probe succeeds. Official MEGAsync v6.7.1.0_Win defines target_compile_definitions(MEGAsync) twice: one general PUBLIC block and one optional Breakpad PRIVATE block.

Replace the incorrect exactly-one-definition guard with validation of the unique Windows MEGAsync executable declaration. Add a conditional target-private fix only when the real compiler probe requires it. Preserve upstream Breakpad settings, /WX, the source-built portable-data adapter, vcpkg improvements, launcher, installer and release publisher.

Add a Windows SDK C++/WinRT link probe, source-inspected target-private WindowsApp linkage, fail-closed diagnostics, and regression tests. Preserve b1r7 Qt/MSVC, vcpkg, and portable data safety. Full b1r8 Windows compilation and runtime remain unverified.`

The first build MUST be unpublished and evaluated on a disposable test account. See README and WINDOWS-TESTING.md.
