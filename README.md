# Korlang Package Registry (KPM)

The official package registry for the Korlang programming language.

[![Website](https://img.shields.io/badge/website-korlang.org-blue)](https://korlang.github.io/registry)
[![Packages](https://img.shields.io/badge/packages-dynamic-orange)](index.json)

## How it Works
KPM is a **decentralized, static registry**. 
- **Index:** `index.json` contains a lightweight list of all packages.
- **Manifests:** `packages/*.json` contain full metadata for specific packages.
- **Hosting:** Hosted entirely on GitHub Pages / CDN.

## Usage

### Install a Package
```bash
kpm install <package-name>
```

### Browse Packages
Visit the [Web UI](https://korlang.github.io/registry) to search and explore libraries.

## For Package Authors
Want to publish a library?
See [CONTRIBUTING.md](CONTRIBUTING.md) for the submission guide.

## Development

To run the registry tooling locally:

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Validate registry state:
   ```bash
   python manage.py validate
   ```

3. Regenerate index:
   ```bash
   python manage.py index
   ```

4. Serve the UI:
   ```bash
   python -m http.server
   ```
   Open `http://localhost:8000` in your browser.

## License
MIT
