# GitHub Desktop commit information — b1r9

Repository: `MEGAsync-Community-PortableApps-Builder` (independent of MEGA upstream).

**Commit summary:**

`Fix WinRT E_FAIL compiler probe missing SDK header - b1r9`

**Description:**

Fix the b1r8 WindowsApp preflight failure where the test program referenced E_FAIL without including its Windows SDK declaration, causing C2065 before linking.

Explicitly include winerror.h in the C++/WinRT probe, before use of E_FAIL. Preserve both tested runtime import paths and real WindowsApp.lib linkage; do not bypass the probe or suppress errors.

Add regression tests for the required header, include order and real WinRT probe/link coverage. Preserve the previous dynamic Qt/MSVC compatibility, vcpkg dependency and Windows path fixes, source-built application, portable data adapter, compiled launcher, installer, and release publisher.

Update package revision and documentation to b1r9.

Run with publish_release=false using disposable test data; Windows application build, sync and installer have not yet passed.
