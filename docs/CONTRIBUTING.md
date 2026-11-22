# GitHub Desktop commit — b1r11

**Summary**

`Fix packaging-only GitHub run provenance check - b1r11`

**Description**

Fix b1r10 packaging-only run rejection caused by requiring a leading slash
in the GitHub REST API workflow path.

Verify the source run against the canonical GitHub workflow ID, repository,
source run ID, manual dispatch status and exact build workflow path.

Retain original ZIP SHA-256 and manifest verification, independently validated
ZIP recovery, compiled launcher, and pinned shared installer/publisher.

Add regression tests for relative-path workflow metadata, wrong workflow IDs,
wrong repositories, wrong run IDs, and unintended workflow paths.

Update packaging-only default revision and builder release identity to b1r11.
