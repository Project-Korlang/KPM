# Contributing to the Korlang Registry

We welcome new packages! This registry is decentralized and Git-based. To publish a package, you submit a Pull Request.

## 1. Prepare Your Package

Ensure your package is hosted on a public repository (GitHub, GitLab, etc.) and has a release tag.

1. Create a release (e.g., `v1.0.0`) and download the source code tarball (or zip).
2. Calculate the SHA-256 checksum of the tarball.
   ```bash
   # Linux/macOS
   shasum -a 256 v1.0.0.tar.gz
   
   # Windows (PowerShell)
   Get-FileHash v1.0.0.zip -Algorithm SHA256
   ```

## 2. Create a Manifest

Create a file named `packages/your-package-name.json`. Use the `manage.py` validator or the web UI generator to ensure it is correct.

**Example:**
```json
{
  "name": "my-utils",
  "version": "1.0.0",
  "description": "A collection of helpful utilities",
  "authors": ["your-handle"],
  "license": "MIT",
  "repository": "https://github.com/your-handle/my-utils",
  "keywords": ["utils", "helper"],
  "categories": ["dev-tool"],
  "dependencies": {},
  "dev_dependencies": {},
  "korlang_version": "^0.1.0",
  "entry_point": "src/lib.kor",
  "checksum": {
    "sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
  },
  "download_url": "https://github.com/your-handle/my-utils/archive/refs/tags/v1.0.0.tar.gz",
  "published_at": "2023-10-27T10:00:00Z"
}
```

## 3. Submit Your Author Profile (First Time Only)

If you haven't published before:
1. Create `authors/your-handle.json`.
2. Use `python manage.py generate-author your-handle` to scaffold.
3. Fill in your details.

## 4. Open a Pull Request

1. Fork this repository.
2. Add your files:
   - `packages/my-package.json`
   - `authors/your-handle.json` (if new)
3. Run local validation:
   ```bash
   pip install -r requirements.txt
   python manage.py validate
   python manage.py lint
   python manage.py verify my-package
   ```
4. Commit and Push. Open a PR to `main`.

## Automated Checks
Your PR will be automatically checked for:
- Schema validity.
- Checksum correctness (the CI will download your package to verify).
- Consistency.

Once merged, your package will appear on the registry website within minutes.
