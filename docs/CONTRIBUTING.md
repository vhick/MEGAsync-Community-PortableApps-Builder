# GitHub Desktop commit — b1r16

**Summary**
`Fix launcher-only recovery from published GitHub Releases - b1r16`

**Description**
```
Fix the b1r15 workflow failure when a successful source build was published
as a GitHub Release instead of an unpublished Actions artifact.

Automatically find the matching release through the original successful
source-build Run ID, or accept an exact explicit release tag.

Verify same-repository provenance, release state, source-run backlink,
asset identity and GitHub digest (when present), original ZIP SHA-256,
SHA256SUMS.txt, and embedded upstream version/commit before reuse.

Rebuild only the cache-contained C++ launcher and red M icon. Preserve
MEGAsync binaries and Qt RCC resources, PortableApps Data safety, and the
shared installer/release integrations. Add release-source regression tests.
```

**Status:** b1r16 local fixtures and static checks only. The full Windows
launcher refresh, installer, and actual Qt cache containment need testing.
