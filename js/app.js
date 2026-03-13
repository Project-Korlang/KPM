// State
const state = {
  packages: [],
  meta: {},
  filter: '',
  category: 'all',
  sort: 'updated_at',
  darkMode: localStorage.getItem('kpm_theme') === 'dark'
};

// Elements
const app = document.getElementById('app');
const searchInput = document.getElementById('search-input');
const themeToggle = document.getElementById('theme-toggle');

// Init
async function init() {
  applyTheme();
  
  // Routing
  window.addEventListener('hashchange', router);
  
  try {
    const res = await fetch('index.json');
    const data = await res.json();
    state.packages = data.packages;
    state.meta = data;
    
    router();
  } catch (e) {
    app.innerHTML = `<div class="loading">Failed to load registry index.<br>${e}</div>`;
  }
}

// Router
function router() {
  const hash = window.location.hash;
  
  if (hash.startsWith('#package/')) {
    const name = hash.split('/')[1];
    renderPackageDetail(name);
  } else if (hash.startsWith('#author/')) {
    const handle = hash.split('/')[1];
    renderAuthorProfile(handle);
  } else if (hash === '#stats') {
    renderStats();
  } else if (hash === '#submit') {
    renderSubmit();
  } else {
    renderHome();
  }
  
  window.scrollTo(0, 0);
  updateNavState();
}

function updateNavState() {
    document.querySelectorAll('.nav-links a').forEach(a => {
        a.classList.remove('active');
        if (a.getAttribute('href') === window.location.hash || (window.location.hash === '' && a.getAttribute('href') === '#')) {
            a.classList.add('active');
        }
    });
}

// Pages
function renderHome() {
  const recent = state.packages.slice(0, 3);
  
  app.innerHTML = `
    <div class="hero">
        <h1>Find and share Korlang packages</h1>
        <p>The decentralized package registry for the Korlang ecosystem.</p>
    </div>

    <div class="search-section">
      <div class="search-bar">
        <input type="text" id="search-input" placeholder="Search packages (Press '/')..." value="${state.filter}">
      </div>
      <div class="filters" id="category-filters">
        <div class="chip ${state.category === 'all' ? 'active' : ''}" onclick="setCategory('all')">All</div>
      </div>
    </div>

    <div class="home-grid">
        <div class="main-content">
            <h3>Explorer</h3>
            <div id="package-list" class="package-grid"></div>
        </div>
        <aside class="sidebar">
            <h3>Recently Updated</h3>
            <div class="recent-list">
                ${recent.map(p => `
                    <div class="recent-item">
                        <a href="#package/${p.name}">${p.name}</a>
                        <span class="recent-ver">${p.version}</span>
                    </div>
                `).join('')}
            </div>
            
            <div class="registry-info">
                <h3>Registry Stats</h3>
                <p>Packages: ${state.packages.length}</p>
                <p>Generated: ${new Date(state.meta.generated_at).toLocaleDateString()}</p>
                <a href="#stats" class="btn btn-sm">View full stats</a>
            </div>
        </aside>
    </div>
  `;
  
  // Re-bind search
  document.getElementById('search-input').addEventListener('input', (e) => {
    state.filter = e.target.value;
    filterAndRender();
  });
  
  // Populate categories
  const categories = new Set();
  state.packages.forEach(p => {
     (p.keywords || []).forEach(k => categories.add(k));
  });

  const filterContainer = document.getElementById('category-filters');
  Array.from(categories).slice(0, 10).forEach(cat => {
      const chip = document.createElement('div');
      chip.className = `chip ${state.category === cat ? 'active' : ''}`;
      chip.innerText = cat;
      chip.onclick = () => setCategory(cat);
      filterContainer.appendChild(chip);
  });
  
  filterAndRender();
}

async function renderPackageDetail(name) {
  app.innerHTML = `<div class="loading">Loading ${name}...</div>`;
  
  try {
    const res = await fetch(`packages/${name}.json`);
    if (!res.ok) throw new Error("Package not found");
    const pkg = await res.json();
    
    // Check if author is verified
    let verifiedBadge = '';
    try {
        const authRes = await fetch(`authors/${pkg.authors[0]}.json`);
        if (authRes.ok) {
            const author = await authRes.json();
            if (author.verified) verifiedBadge = '<span class="verified-badge" title="Verified Author">✅</span>';
        }
    } catch(e) {}

    app.innerHTML = `
      <div class="detail-container">
        <div class="pkg-header-detail">
            <div class="pkg-title-row">
                <h1>${pkg.name} ${verifiedBadge}</h1>
                <span class="pkg-version-large">${pkg.version}</span>
            </div>
            <p class="pkg-desc-large">${pkg.description}</p>
        </div>
        
        <div class="install-section">
            <label>Install Command</label>
            <div class="install-box">
                <code>kpm install ${pkg.name}</code>
                <button class="copy-btn" onclick="navigator.clipboard.writeText('kpm install ${pkg.name}')">Copy</button>
            </div>
        </div>
        
        <div class="detail-grid">
            <div class="detail-main">
                <section>
                    <h3>Readme</h3>
                    <div class="readme-container" id="readme-box">
                        ${pkg.readme_url ? '<p>Loading readme...</p>' : '<p>No readme available.</p>'}
                    </div>
                </section>

                <section>
                    <h3>Dependencies</h3>
                    <div class="dependency-graph">
                        ${renderDependencyTree(pkg.dependencies || {})}
                    </div>
                </section>
            </div>

            <aside class="detail-sidebar">
                <div class="meta-box">
                    <h4>Meta</h4>
                    <p><strong>License:</strong> ${pkg.license}</p>
                    <p><strong>Published:</strong> ${new Date(pkg.published_at).toLocaleDateString()}</p>
                    <p><strong>Korlang:</strong> <code>${pkg.korlang_version}</code></p>
                </div>

                <div class="meta-box">
                    <h4>Links</h4>
                    <ul class="link-list">
                        ${pkg.repository ? `<li><a href="${pkg.repository}" target="_blank">Repository</a></li>` : ''}
                        ${pkg.homepage ? `<li><a href="${pkg.homepage}" target="_blank">Homepage</a></li>` : ''}
                        ${pkg.documentation_url ? `<li><a href="${pkg.documentation_url}" target="_blank">Documentation</a></li>` : ''}
                        <li><a href="${pkg.download_url}">Download Tarball</a></li>
                    </ul>
                </div>

                <div class="meta-box">
                    <h4>Authors</h4>
                    <ul class="author-list">
                        ${pkg.authors.map(a => `<li><a href="#author/${a}">${a}</a></li>`).join('')}
                    </ul>
                </div>

                <div class="meta-box">
                    <h4>Integrity</h4>
                    <p><small>SHA-256 Checksum:</small></p>
                    <code class="checksum-display">${pkg.checksum.sha256.substring(0, 16)}...</code>
                    ${pkg.checksum.signature ? '<p class="sig-status">🔒 GPG Signed</p>' : '<p class="sig-status">🔓 Unsigned</p>'}
                </div>
            </aside>
        </div>
      </div>
    `;

    if (pkg.readme_url) {
        fetchReadme(pkg.readme_url);
    }
  } catch (e) {
    app.innerHTML = `<div class="error">Error: ${e.message}</div>`;
  }
}

function renderDependencyTree(deps) {
    const keys = Object.keys(deps);
    if (keys.length === 0) return '<p>No dependencies.</p>';
    
    return `
        <ul class="tree">
            ${keys.map(k => `
                <li>
                    <div class="tree-node">
                        <a href="#package/${k}">${k}</a>
                        <span class="tree-ver">${deps[k]}</span>
                    </div>
                </li>
            `).join('')}
        </ul>
    `;
}

async function fetchReadme(url) {
    try {
        const res = await fetch(url);
        const text = await res.text();
        // Minimal markdown rendering (replace code blocks and links)
        const html = text
            .replace(/```([\s\S]*?)```/g, '<pre><code>$1</code></pre>')
            .replace(/`([^`]+)`/g, '<code>$1</code>')
            .replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2">$1</a>');
            
        document.getElementById('readme-box').innerHTML = html;
    } catch(e) {
        document.getElementById('readme-box').innerHTML = '<p>Error loading readme.</p>';
    }
}

async function renderAuthorProfile(handle) {
    app.innerHTML = `<div class="loading">Loading author...</div>`;
    try {
        const res = await fetch(`authors/${handle}.json`);
        if (!res.ok) throw new Error("Author not found");
        const author = await res.json();

        app.innerHTML = `
            <div class="detail-container">
                <div class="author-profile">
                    <div class="author-header">
                        <img src="https://www.gravatar.com/avatar/${author.email_hash}?s=100&d=identicon" class="author-avatar">
                        <div class="author-info">
                            <h1>${author.name} ${author.verified ? '✅' : ''}</h1>
                            <p class="author-handle">@${author.handle}</p>
                            <p>Joined ${new Date(author.joined_at).toLocaleDateString()}</p>
                        </div>
                    </div>

                    <div class="author-links">
                        ${author.github_url ? `<a href="${author.github_url}" target="_blank" class="btn">GitHub</a>` : ''}
                        ${author.website_url ? `<a href="${author.website_url}" target="_blank" class="btn">Website</a>` : ''}
                    </div>

                    <div class="author-packages">
                        <h3>Packages by ${author.name}</h3>
                        <div class="package-grid">
                            ${state.packages.filter(p => p.authors.includes(handle)).map(p => `
                                <div class="package-card">
                                    <a href="#package/${p.name}" class="pkg-name">${p.name}</a>
                                    <p>${p.description}</p>
                                </div>
                            `).join('')}
                        </div>
                    </div>
                </div>
            </div>
        `;
    } catch (e) {
        app.innerHTML = `
            <div class="detail-container">
                <h1>${handle}</h1>
                <p>Profile not found.</p>
                <h3>Packages by this author</h3>
                <ul>
                    ${state.packages.filter(p => p.authors.includes(handle)).map(p => `<li><a href="#package/${p.name}">${p.name}</a></li>`).join('')}
                </ul>
            </div>
        `;
    }
}

function renderStats() {
    const totalPkgs = state.packages.length;
    const totalAuthors = new Set(state.packages.flatMap(p => p.authors)).size;

    app.innerHTML = `
        <div class="detail-container">
            <h1>Registry Statistics</h1>
            <div class="stats-grid">
                <div class="stat-card">
                    <div class="stat-value">${totalPkgs}</div>
                    <div>Packages</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">${totalAuthors}</div>
                    <div>Authors</div>
                </div>
            </div>
            
            <div class="chart-section">
                <h3>Package Distribution</h3>
                <div class="chart-container">
                    <canvas id="categoryChart"></canvas>
                </div>
            </div>
        </div>
    `;

    const counts = {};
    state.packages.forEach(p => {
        const cat = (p.keywords && p.keywords[0]) || 'Uncategorized';
        counts[cat] = (counts[cat] || 0) + 1;
    });

    const ctx = document.getElementById('categoryChart').getContext('2d');
    new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: Object.keys(counts),
            datasets: [{
                data: Object.values(counts),
                backgroundColor: ['#0d6efd', '#6610f2', '#6f42c1', '#d63384', '#dc3545', '#fd7e14', '#ffc107', '#198754']
            }]
        },
        options: { responsive: true }
    });
}

function renderSubmit() {
    app.innerHTML = `
        <div class="detail-container">
            <h1>Submit a Package</h1>
            <p>Publish your Korlang library to the community.</p>
            
            <div class="submit-steps">
                <div class="step">
                    <h4>1. Prepare</h4>
                    <p>Host your code on GitHub/GitLab and create a tagged release.</p>
                </div>
                <div class="step">
                    <h4>2. Manifest</h4>
                    <p>Create a JSON manifest using the tool below.</p>
                </div>
                <div class="step">
                    <h4>3. Pull Request</h4>
                    <p>Fork the registry repo and add your manifest to <code>packages/</code>.</p>
                </div>
            </div>

            <div class="generator-box">
                <h3>Manifest Generator</h3>
                <div class="form-grid">
                    <input type="text" id="gen-name" placeholder="Package Name (e.g. my-lib)" class="form-control">
                    <input type="text" id="gen-version" placeholder="Version (1.0.0)" class="form-control">
                    <input type="text" id="gen-desc" placeholder="Description" class="form-control">
                    <input type="text" id="gen-repo" placeholder="Repo URL" class="form-control">
                    <button class="btn btn-primary" onclick="generateManifest()">Generate JSON</button>
                </div>
                <pre id="gen-output" class="json-output"></pre>
            </div>
        </div>
    `;
}

function generateManifest() {
    const name = document.getElementById('gen-name').value;
    const version = document.getElementById('gen-version').value;
    const desc = document.getElementById('gen-desc').value;
    const repo = document.getElementById('gen-repo').value;
    
    const json = {
        name: name,
        version: version,
        description: desc,
        authors: ["YOUR_HANDLE"],
        license: "MIT",
        repository: repo,
        keywords: [],
        categories: ["other"],
        dependencies: {},
        dev_dependencies: {},
        korlang_version: "^0.1.0",
        entry_point: "src/lib.kor",
        checksum: { "sha256": "DOWNLOAD_YOUR_TARBALL_AND_HASH_IT" },
        download_url: repo + "/archive/refs/tags/v" + version + ".tar.gz",
        published_at: new Date().toISOString()
    };
    
    document.getElementById('gen-output').innerText = JSON.stringify(json, null, 2);
}

// Logic
function filterAndRender() {
  const container = document.getElementById('package-list');
  if (!container) return;
  container.innerHTML = '';
  
  const filtered = state.packages.filter(p => {
    const matchesSearch = p.name.toLowerCase().includes(state.filter.toLowerCase()) || 
                          p.description.toLowerCase().includes(state.filter.toLowerCase());
    const matchesCat = state.category === 'all' || (p.keywords && p.keywords.includes(state.category));
    return matchesSearch && matchesCat;
  });

  filtered.forEach(p => {
    const card = document.createElement('div');
    card.className = 'package-card';
    card.innerHTML = `
      <div class="pkg-header">
        <a href="#package/${p.name}" class="pkg-name">${p.name}</a>
        <span class="pkg-version">${p.version}</span>
      </div>
      <div class="pkg-desc">${p.description}</div>
      <div class="pkg-meta">
        <span>by <a href="#author/${p.authors[0]}">${p.authors[0]}</a></span>
        <span>${new Date(p.updated_at).toLocaleDateString()}</span>
      </div>
    `;
    container.appendChild(card);
  });
  
  if (filtered.length === 0) {
      container.innerHTML = '<div style="grid-column: 1/-1; text-align:center; padding: 40px;">No packages found.</div>';
  }
}

function setCategory(cat) {
    state.category = cat;
    renderHome();
}

// Utils
function applyTheme() {
    if (state.darkMode) {
        document.documentElement.setAttribute('data-theme', 'dark');
        themeToggle.innerText = '☀';
    } else {
        document.documentElement.removeAttribute('data-theme');
        themeToggle.innerText = '🌙';
    }
}

themeToggle.addEventListener('click', () => {
    state.darkMode = !state.darkMode;
    localStorage.setItem('kpm_theme', state.darkMode ? 'dark' : 'light');
    applyTheme();
});

// Keyboard
document.addEventListener('keydown', (e) => {
    if (e.key === '/' && document.activeElement !== document.getElementById('search-input')) {
        e.preventDefault();
        document.getElementById('search-input')?.focus();
    }
});

// Start
init();
