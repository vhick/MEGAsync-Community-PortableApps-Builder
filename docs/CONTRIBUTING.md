# GitHub Desktop commit — b1r12

Summary:

`Fix MEGAsync missing Qt resources and embed launcher icon - b1r12`

Description:

```text
Fix the user-confirmed resource loading error by packaging all five source-built Qt .rcc files alongside MEGAsync.exe.

Discover resource targets from upstream gui.cmake and validate their binary headers, sizes, source hashes, package hashes and manifest before installer generation.

Prevent packaging-only from recycling older broken ZIPs missing these required resources.

Embed a consistent original community cloud icon into the compiled root launcher and AppInfo without copying MEGA trademarked artwork.

Add early post-build resource checks and regression tests. Preserve the prior Qt/MSVC, WinRT, vcpkg, data redirection, launcher, custom-NSIS and release publisher implementations.

Update builder/package revision to b1r12.
```

Extract kit at repository root, keeping `.github/` contents, commit and push. Run the full **source build**, not packaging-only against the broken b1r11 ZIP. Keep `publish_release=false` until actual Windows runtime acceptance and legal review.
