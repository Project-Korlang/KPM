# KPM Registry Roadmap

This document outlines the development plan for the Korlang Package Manager Registry.

## Phase 1: Foundation (Completed)
- [x] JSON Schema validation for manifests and authors.
- [x] Python CLI (`manage.py`) for management and CI checks.
- [x] Static website for browsing packages.
- [x] Decentralized Git-based submission workflow.

## Phase 2: Enhanced Metadata & Security (Completed)
- [x] **Package Signing:** Authors can sign tarballs with GPG; registry verifies them.
- [x] **Verified Publishers:** Authors can list public keys and be marked as verified.
- [x] **Dependency Visualization:** Nested dependency tree in the Web UI.
- [x] **CLI Discovery:** `manage.py search` for finding packages.
- [x] **UI Overhaul:** Modern layout with dark mode, recent updates, and author profiles.

## Phase 3: Scaling & Backend (Deferred)
Future features when a backend is introduced:
- [ ] **Download Tracking:** Lightweight serverless counter.
- [ ] **Package Search API:** JSON API for faster CLI fuzzy search.
- [ ] **Private Registries:** Spec for self-hosting.
- [ ] **Mirror Support:** Multi-region availability.
- [ ] **Advanced Version Resolution:** SAT-solver for complex dependency graphs.
