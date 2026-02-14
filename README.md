# 📦 KPM Registry: The Korlang Package Ecosystem

[![Registry Status](https://img.shields.io/badge/Registry-Online-success)](https://project-korlang.github.io/KPM/)
[![Korlang Version](https://img.shields.io/badge/Korlang-1.0--alpha-blue)](https://github.com/Project-Korlang/Korlang-Compiler)

The official decentralized registry for **Korlang** packages. KPM (Korlang Package Manager) uses this repository as its primary source of truth for discovering, verifying, and downloading native Korlang libraries.

---

## 🚀 Quick Start

### 1. Register the Registry
Add the official registry to your local KPM configuration:
\`\`\`bash
korlang kpm registry add official https://project-korlang.github.io/KPM/
\`\`\`

### 2. Install a Package
\`\`\`bash
kpm install <package-name>
\`\`\`

### 3. Initialize a Project
\`\`\`bash
korlang new my-project
\`\`\`

---

## 🛠️ For Developers

### Registry Structure
- \`packages/\`: Contains individual JSON manifests for every registered package.
- \`authors/\`: Metadata for verified package maintainers.
- \`index.json\`: The compressed master index used for fast CLI discovery.

### Submitting a Package
1. **Fork** this repository.
2. Add your package manifest to \`packages/<your-package>.json\`.
3. Ensure your source code is hosted on a supported platform (GitHub/GitLab).
4. Open a **Pull Request**.

---

## 🎨 Visualizing the Ecosystem
Visit the [KPM Web Interface](https://project-korlang.github.io/KPM/) to browse trending packages, view documentation, and check dependency graphs.

---
*Built with ❤️ for the Korlang Community.*

