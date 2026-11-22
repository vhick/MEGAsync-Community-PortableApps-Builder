# GitHub Desktop commit — b1r14

**Summary**

`Replace generic cloud with red portable icon and add icon-only rebuild - b1r14`

**Description**

Replace the original generic blue cloud with a distinctive red MP community icon in both the PortableApps menu and compiled launcher. Generate all PortableApps PNG sizes and the full Windows multiresolution ICO. Verify the launcher/menu ICO assets agree.

Add an opt-in icon-only GitHub Actions workflow that downloads an original verified successful source-build ZIP, compiles only the C++ launcher, preserves MEGAsync application files byte-for-byte, regenerates the ZIP and custom-NSIS installer, and keeps publication disabled by default.

Preserve b1r13 application compilation, Qt resources, portable-data handling, vcpkg and WinRT compatibility, installer and publisher integration. Update revision to b1r14 and add regression tests. This is an unofficial community build; MEGA trademark artwork is not distributed.
