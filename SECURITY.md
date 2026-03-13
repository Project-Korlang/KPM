# Security Policy

## Package Integrity

### Checksums
Every package in the Korlang Registry is required to have a SHA-256 checksum in its manifest. This checksum is calculated from the source tarball at the `download_url`.

The KPM CLI and `manage.py` tool verify this checksum before installation or indexing. If the checksum does not match, the installation is aborted.

### Signing (Design)
We are currently rolling out a package signing system. Authors are encouraged to sign their package tarballs using GPG or Ed25519.
- **Workflow:**
  1. Author generates a keypair.
  2. Author publishes the public key in `authors/<handle>.json`.
  3. Author signs the tarball (`package.tar.gz.sig`).
  4. The signature is included in the package manifest under `checksum.signature`.
  5. The CLI verifies the signature against the author's public key.

## Reporting Vulnerabilities

If you discover a malicious package or a vulnerability in the registry infrastructure:

1. **Do NOT** open a public issue.
2. Email **security@korlang.org** immediately.
3. Include the package name, version, and a description of the threat.

We aim to acknowledge reports within 24 hours.

## Deprecation & Yanking

### Deprecation
Authors can mark a package version as deprecated by setting `"deprecated": true` in the manifest. Deprecated packages:
- Appear in search results with a warning.
- Trigger a warning when installed via CLI.
- Are still available for download to prevent breaking existing builds.

### Yanking
"Yanking" is reserved for critical security issues or malicious code. A yanked package:
- Is removed from the search index.
- Cannot be installed unless already present in a lockfile.
- The `download_url` may be removed or replaced with a tombstone.

To request a yank, contact the registry maintainers.

## Namespace Reservation
To prevent typosquatting and impersonation:
- Package names with a namespace (e.g., `google/protobuf`) require the namespace owner to be a verified author in `authors/`.
- The author's `handle` must match the namespace.
- Only that author can publish packages under that namespace.

## Review Process
All Pull Requests to the registry are automatically scanned for:
- Valid JSON syntax and Schema compliance.
- Checksum validity (the artifact is downloaded and hashed).
- Namespace ownership.
- Suspicious URLs (non-GitHub/GitLab domains flag a warning).
