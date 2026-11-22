# GitHub Desktop commit — b1r13

**Commit summary**

`Fix Windows CI test dependencies and path aliases - b1r13`

**Commit description**

Fix two b1r12 pre-build test failures seen on the GitHub-hosted Windows runner.

Install the pinned Python dependencies, including Pillow and aqtinstall, before running tests. Verify both imports and avoid a duplicate dependency-install step.

Correct installer-path regression tests to compare file identity with `Path.samefile()` rather than text representations of the Windows `RUNNER~1` 8.3 alias and `runneradmin` long directory name.

Add five Windows bootstrap regression tests. Retain the b1r12 fixes for all five MEGAsync Qt `.rcc` files and the embedded community launcher icon, as well as the verified adaptive Qt/MSVC, WinRT, vcpkg and shared-action integrations.

Update the builder and output revision to b1r13. Keep release publication off pending real Windows runtime acceptance.
