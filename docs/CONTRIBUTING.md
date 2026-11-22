# GitHub Desktop commit — b1r15

**Summary:**
`Redirect QML cache and prevent shared Qt shader cache writes - b1r15`

**Description:**
```
Keep the user-confirmed b1r14 MEGAsync application and custom red M icon intact.

Add launcher-only Qt cache policy: redirect Qt 5.15 QML disk cache to portable
Data\Cache\QML, disable optional OpenGL/RHI shader disk caches for the
portable child process, and use a fail-safe no-QML-disk-cache fallback for
Unicode or extremely long portable paths.

Do not redirect global APPDATA, LOCALAPPDATA, or TEMP. Never delete shared
or preexisting host cache directories and preserve installed MEGA profiles.

Update the launcher-and-icons-only GitHub Actions workflow to reuse a verified
source-built MEGAsync ZIP without recompiling the application, preserve the
App/MEGAsync subtree byte-for-byte, and retain SHA-256 verification and
custom-NSIS installer/release-publisher integrations.

Add targeted cache-policy regression checks, Windows manual acceptance
procedures, and update kit revision to b1r15.
```

**Status:** Source/static validated only; real b1r15 Windows runtime cache
containment, installer upgrade and installed-app coexistence not yet verified.
