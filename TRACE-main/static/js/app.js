/* TRACE — Main Application JavaScript
   Handles navigation, data loading, charts, graphs, real-time feed */

// ── State ────────────────────────────────────────────────────────────────

const state = {
    currentView: 'dashboard',
    charts: {},
    graphs: {},
    map: null,
    feedTimer: null,
    alertPollTimer: null,
};

// ── Navigation ───────────────────────────────────────────────────────────

function navigateTo(view) {
    document.querySelectorAll('.view').forEach(v => v.classList.remove('active'));
    document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));

    const viewEl = document.getElementById(`view-${view}`);
    const navEl = document.querySelector(`.nav-item[data-view="${view}"]`);
    if (viewEl) viewEl.classList.add('active');
    if (navEl) navEl.classList.add('active');

    state.currentView = view;

    const titles = {
        dashboard: ['Dashboard', 'System Overview'],
        feed: ['Live Feed', 'Real-time Listing Detection'],
        vendors: ['Vendor Intelligence', 'Network Analysis & Profiling'],
        crypto: ['Crypto Tracing', 'Wallet Analysis & Fund Flow'],
        evidence: ['Evidence Locker', 'Chain-of-Custody & NDPS Dossier'],
        slang: ['Slang Engine', 'Hinglish / Punjabi / English Detection'],
        settings: ['Watchlist', 'Keyword Monitoring & System'],
    };
    const [title, sub] = titles[view] || ['', ''];
    document.getElementById('view-title').textContent = title;
    document.getElementById('view-subtitle').textContent = sub;

    loadView(view);
}

document.querySelectorAll('.nav-item').forEach(item => {
    item.addEventListener('click', e => {
        e.preventDefault();
        navigateTo(item.dataset.view);
    });
});

// ── API Helpers ──────────────────────────────────────────────────────────

async function api(path, opts = {}) {
    try {
        const res = await fetch(`/api${path}`, {
            headers: { 'Content-Type': 'application/json' },
            ...opts,
        });
        if (!res.ok) throw new Error(`API ${res.status}`);
        return await res.json();
    } catch (err) {
        console.error('API Error:', path, err);
        return null;
    }
}

// ── View Loaders ─────────────────────────────────────────────────────────

function loadView(view) {
    switch (view) {
        case 'dashboard': loadDashboard(); break;
        case 'feed': loadFeed(); break;
        case 'vendors': loadVendors(); break;
        case 'crypto': loadCrypto(); break;
        case 'evidence': loadEvidence(); break;
        case 'slang': loadSlang(); break;
        case 'settings': loadSettings(); break;
    }
}

// ── Dashboard ────────────────────────────────────────────────────────────

async function loadDashboard() {
    const stats = await api('/dashboard/stats');
    if (!stats) return;

    document.getElementById('stats-cards').innerHTML = `
        <div class="stat-card accent">
            <div class="stat-label">Total Listings</div>
            <div class="stat-value">${stats.total_listings}</div>
            <div class="stat-sub">${stats.drug_listings} flagged as drug-related</div>
        </div>
        <div class="stat-card warning">
            <div class="stat-label">Active Vendors</div>
            <div class="stat-value">${stats.total_vendors}</div>
            <div class="stat-sub">${stats.high_risk_vendors} high risk</div>
        </div>
        <div class="stat-card critical">
            <div class="stat-label">Unread Alerts</div>
            <div class="stat-value">${stats.unread_alerts}</div>
            <div class="stat-sub">${stats.critical_alerts} critical</div>
        </div>
        <div class="stat-card info">
            <div class="stat-label">Evidence Items</div>
            <div class="stat-value">${stats.total_evidence}</div>
            <div class="stat-sub">SHA-256 verified</div>
        </div>
        <div class="stat-card accent">
            <div class="stat-label">Tracked Wallets</div>
            <div class="stat-value">${stats.total_wallets}</div>
            <div class="stat-sub">${stats.total_transactions} transactions</div>
        </div>
    `;

    // Trends chart
    renderTrendsChart(stats.listings_by_day);
    // Alerts chart
    renderAlertsChart(stats.alerts_by_severity);
    // Recent alerts
    const alerts = await api('/dashboard/alerts?limit=8');
    if (alerts) renderAlertFeed(document.getElementById('recent-alerts'), alerts);

    document.getElementById('badge-count').textContent = stats.unread_alerts;
}

function renderTrendsChart(data) {
    const ctx = document.getElementById('chart-trends');
    if (!ctx) return;
    if (state.charts.trends) state.charts.trends.destroy();

    const labels = data.map(d => d.day ? d.day.slice(5) : '');
    state.charts.trends = new Chart(ctx, {
        type: 'line',
        data: {
            labels,
            datasets: [
                {
                    label: 'Total Listings',
                    data: data.map(d => d.count),
                    borderColor: '#4da6ff',
                    backgroundColor: 'rgba(77,166,255,0.08)',
                    fill: true,
                    tension: 0.3,
                    pointRadius: 3,
                    borderWidth: 2,
                },
                {
                    label: 'Drug Flagged',
                    data: data.map(d => d.drug_count),
                    borderColor: '#ff4757',
                    backgroundColor: 'rgba(255,71,87,0.08)',
                    fill: true,
                    tension: 0.3,
                    pointRadius: 3,
                    borderWidth: 2,
                }
            ]
        },
        options: chartOptions('Listings')
    });
}

function renderAlertsChart(data) {
    const ctx = document.getElementById('chart-alerts');
    if (!ctx) return;
    if (state.charts.alerts) state.charts.alerts.destroy();

    const colors = { critical: '#ff4757', warning: '#f5a623', info: '#4da6ff' };
    const labels = Object.keys(data);
    state.charts.alerts = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels,
            datasets: [{
                data: Object.values(data),
                backgroundColor: labels.map(l => colors[l] || '#666'),
                borderWidth: 0,
                hoverOffset: 4,
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            cutout: '65%',
            plugins: {
                legend: {
                    position: 'right',
                    labels: { color: '#8896a8', font: { size: 11, family: 'Inter' }, padding: 12 }
                }
            }
        }
    });
}

function renderAlertFeed(container, alerts) {
    container.innerHTML = alerts.map(a => `
        <div class="alert-item" onclick="markAlertRead(${a.id})">
            <div class="alert-dot ${a.severity}"></div>
            <div class="alert-content">
                <div class="alert-title">${esc(a.title)}</div>
                <div class="alert-message">${esc(a.message)}</div>
            </div>
            <div class="alert-time">${timeAgo(a.created_at)}</div>
        </div>
    `).join('');
}

async function markAlertRead(id) {
    await api(`/dashboard/alerts/${id}/read`, { method: 'POST' });
    loadDashboard();
}

// ── Live Feed ────────────────────────────────────────────────────────────

async function loadFeed() {
    const source = document.getElementById('filter-source')?.value || '';
    const minScore = (document.getElementById('filter-score')?.value || 0) / 100;
    const params = new URLSearchParams({ limit: '60', min_score: minScore });
    if (source) params.set('source', source);

    const listings = await api(`/listings?${params}`);
    if (!listings) return;

    const container = document.getElementById('feed-table');
    container.innerHTML = `
        <table>
            <thead><tr>
                <th>Time</th>
                <th>Source</th>
                <th>Text</th>
                <th>Substances</th>
                <th>Emoji</th>
                <th>Score</th>
                <th>Vendor</th>
            </tr></thead>
            <tbody>
            ${listings.map(l => {
                const score = l.combined_score || 0;
                const cls = score > 0.8 ? 'critical' : score > 0.6 ? 'high' : score > 0.4 ? 'medium' : score > 0.2 ? 'low' : 'clean';
                const substances = parseArr(l.detected_substances);
                const emoji = parseArr(l.detected_emoji);
                return `<tr>
                    <td class="text-mono">${timeAgo(l.detected_at)}</td>
                    <td><span class="source-badge ${l.source}">${l.source}</span></td>
                    <td class="text-truncate" title="${esc(l.text)}">${esc(l.text.slice(0, 100))}</td>
                    <td>${substances.map(s => `<span class="slang-tag">${s}</span>`).join(' ')}</td>
                    <td>${emoji.map(e => `<span style="font-size:16px">${e}</span>`).join(' ')}</td>
                    <td><span class="score-badge ${cls}">${score.toFixed(2)}</span></td>
                    <td class="text-mono">${l.vendor_id || '—'}</td>
                </tr>`;
            }).join('')}
            </tbody>
        </table>
    `;
}

// ── Vendors ──────────────────────────────────────────────────────────────

async function loadVendors() {
    const vendors = await api('/vendors?limit=30');
    if (!vendors) return;

    const container = document.getElementById('vendor-list');
    container.innerHTML = vendors.map(v => {
        const cls = v.risk_score > 0.8 ? 'critical' : v.risk_score > 0.6 ? 'high' : v.risk_score > 0.4 ? 'medium' : 'low';
        return `<div class="vendor-card" onclick="showVendor(${v.id})">
            <div class="vendor-name">
                ${esc(v.name)}
                <span class="score-badge ${cls}">${v.risk_score.toFixed(2)}</span>
            </div>
            <div class="vendor-handle">${esc(v.handle || '')} · ${v.platform}</div>
            <div class="vendor-meta">
                <span>${v.total_listings} listings</span>
                <span>${v.active_days} days active</span>
                <span class="source-badge ${v.platform}">${v.platform}</span>
            </div>
        </div>`;
    }).join('');

    loadVendorGraph();
}

async function loadVendorGraph() {
    const data = await api('/vendors/graph/data');
    if (!data || !data.nodes.length) return;

    const container = document.getElementById('vendor-graph');
    const nodes = new vis.DataSet(data.nodes.map(n => ({
        id: n.id,
        label: n.label,
        color: {
            background: n.platform === 'telegram' ? '#4da6ff' : '#ff4757',
            border: n.platform === 'telegram' ? '#2d7ad6' : '#d63447',
            highlight: { background: '#00d4aa', border: '#00b892' }
        },
        font: { color: '#e2e8f0', size: 11, face: 'Inter' },
        shape: 'dot',
        size: 10 + (n.risk_score || 0) * 15,
    })));

    const edges = new vis.DataSet(data.edges.map(e => ({
        from: e.from,
        to: e.to,
        label: e.label,
        color: { color: '#1e2a3a', highlight: '#00d4aa' },
        font: { color: '#4a5568', size: 9, face: 'JetBrains Mono' },
        width: 1 + e.value * 3,
        arrows: 'to',
    })));

    if (state.graphs.vendor) state.graphs.vendor.destroy();
    state.graphs.vendor = new vis.Network(container, { nodes, edges }, {
        physics: { stabilization: { iterations: 150 }, barnesHut: { gravitationalConstant: -3000 } },
        interaction: { hover: true, tooltipDelay: 200 },
        edges: { smooth: { type: 'continuous' } },
    });
}

async function showVendor(id) {
    const v = await api(`/vendors/${id}`);
    if (!v) return;
    const cls = v.risk_score > 0.8 ? 'critical' : v.risk_score > 0.6 ? 'high' : v.risk_score > 0.4 ? 'medium' : 'low';

    const linksHtml = (v.links || []).map(l => {
        const other = l.vendor_a === id ? l.name_b : l.name_a;
        const score = l.similarity_score;
        return `<div style="display:flex;gap:8px;align-items:center;padding:4px 0">
            <span style="color:var(--text-primary)">→ ${esc(other)}</span>
            <span class="score-badge ${score > 0.7 ? 'high' : 'medium'}">${(score * 100).toFixed(0)}%</span>
            <span style="font-size:10px;color:var(--text-dim)">${JSON.parse(l.link_types || '[]').join(', ')}</span>
        </div>`;
    }).join('');

    document.getElementById('vendor-detail').innerHTML = `
        <div style="display:grid;grid-template-columns:1fr 1fr;gap:16px">
            <div>
                <h4 style="color:var(--accent);font-size:14px;margin-bottom:12px">${esc(v.name)}</h4>
                <div class="sys-row"><span>Handle</span><span>${esc(v.handle || 'N/A')}</span></div>
                <div class="sys-row"><span>Platform</span><span>${v.platform}</span></div>
                <div class="sys-row"><span>Risk Score</span><span class="score-badge ${cls}">${v.risk_score.toFixed(3)}</span></div>
                <div class="sys-row"><span>Total Listings</span><span>${v.total_listings}</span></div>
                <div class="sys-row"><span>Active Days</span><span>${v.active_days}</span></div>
                <div class="sys-row"><span>Status</span><span>${v.status}</span></div>
                <div class="sys-row"><span>First Seen</span><span>${v.first_seen || 'N/A'}</span></div>
            </div>
            <div>
                <h4 style="color:var(--warning);font-size:12px;margin-bottom:8px">LINKED IDENTITIES (${(v.links || []).length})</h4>
                ${linksHtml || '<div style="color:var(--text-dim);font-size:11px">No cross-platform links detected</div>'}
            </div>
        </div>
    `;
}

// ── Crypto ───────────────────────────────────────────────────────────────

async function loadCrypto() {
    const wallets = await api('/crypto/wallets?limit=20');
    const txs = await api('/crypto/transactions?limit=30');

    if (wallets) {
        document.getElementById('wallet-list').innerHTML = wallets.map(w => {
            const cls = (w.risk_flags || '').includes('mixer') ? 'critical' : 'low';
            return `<div class="wallet-row" onclick="document.getElementById('crypto-search-input').value='${w.address}';traceWallet()">
                <span class="wallet-addr">${w.address.slice(0, 20)}...</span>
                <span style="font-size:10px;color:var(--text-dim)">${w.currency}</span>
                <span class="score-badge ${w.balance > 2 ? 'high' : 'low'}">${w.balance.toFixed(3)}</span>
            </div>`;
        }).join('');
    }

    if (txs) {
        document.getElementById('tx-list').innerHTML = txs.map(tx => `
            <div class="tx-row">
                <span class="text-truncate" title="${tx.wallet_from}">${tx.wallet_from.slice(0, 16)}...</span>
                <span class="tx-arrow">→</span>
                <span class="text-truncate" title="${tx.wallet_to}">${tx.wallet_to.slice(0, 16)}...</span>
                <span style="color:${tx.is_mixer ? 'var(--critical)' : 'var(--text-primary)'}">${tx.amount.toFixed(4)}</span>
                <span style="color:var(--text-dim)">${tx.currency}</span>
            </div>
        `).join('');
    }
}

async function traceWallet() {
    const addr = document.getElementById('crypto-search-input').value.trim();
    if (!addr) return;
    const flow = await api(`/crypto/flow/${addr}`);
    if (!flow) return;

    const container = document.getElementById('crypto-flow-graph');
    const nodes = new vis.DataSet(flow.nodes.map(n => ({
        id: n.id,
        label: n.label,
        color: {
            background: n.is_center ? '#00d4aa' : (n.risk_score > 0.6 ? '#ff4757' : '#1a2233'),
            border: n.is_center ? '#00b892' : (n.risk_score > 0.6 ? '#d63447' : '#1e2a3a'),
            highlight: { background: '#00d4aa', border: '#00b892' }
        },
        font: { color: '#e2e8f0', size: 10, face: 'JetBrains Mono' },
        shape: n.is_center ? 'diamond' : 'dot',
        size: n.is_center ? 16 : 8,
    })));

    const edges = new vis.DataSet(flow.edges.map(e => ({
        from: e.from,
        to: e.to,
        color: { color: e.is_mixer ? '#ff4757' : '#1e2a3a', highlight: '#00d4aa' },
        width: Math.max(1, Math.min(e.amount * 2, 5)),
        arrows: 'to',
        label: `${e.amount.toFixed(4)} BTC`,
        font: { color: '#4a5568', size: 8, face: 'JetBrains Mono' },
    })));

    if (state.graphs.crypto) state.graphs.crypto.destroy();
    state.graphs.crypto = new vis.Network(container, { nodes, edges }, {
        physics: { stabilization: { iterations: 100 }, barnesHut: { gravitationalConstant: -2000 } },
        edges: { smooth: { type: 'continuous' } },
    });
}

// ── Evidence ─────────────────────────────────────────────────────────────

async function loadEvidence() {
    const evidence = await api('/evidence');
    const vendors = await api('/vendors');

    if (vendors) {
        const sel = document.getElementById('dossier-vendor-select');
        sel.innerHTML = '<option value="">Select a vendor...</option>' +
            vendors.map(v => `<option value="${v.id}">${esc(v.name)} (${v.risk_score.toFixed(2)})</option>`).join('');
    }

    if (evidence) {
        document.getElementById('evidence-list').innerHTML = evidence.map(e => `
            <div class="evidence-item">
                <span class="severity-badge ${e.artifact_type === 'listing' ? 'info' : 'warning'}">${e.artifact_type}</span>
                <span class="evidence-hash">${e.content_hash.slice(0, 40)}...</span>
                <span style="font-size:11px;color:var(--text-secondary);flex:1">${esc(e.notes || '')}</span>
                <span class="text-mono" style="font-size:10px;color:var(--text-dim)">${timeAgo(e.captured_at)}</span>
            </div>
        `).join('');
    }
}

async function generateDossier() {
    const vid = document.getElementById('dossier-vendor-select').value;
    if (!vid) return;
    const res = await fetch(`/api/evidence/dossier/${vid}`);
    if (!res.ok) return;
    const text = await res.text();
    document.getElementById('dossier-output').textContent = text;
}

async function captureEvidence() {
    const content = document.getElementById('evidence-content').value.trim();
    if (!content) return;
    const res = await api('/evidence/capture', {
        method: 'POST',
        body: JSON.stringify({ content, type: 'manual_capture', source: 'Investigator' })
    });
    if (res) {
        document.getElementById('capture-result').innerHTML =
            `<div>Captured ✓</div><div>SHA-256: ${res.content_hash}</div>`;
        document.getElementById('evidence-content').value = '';
        loadEvidence();
    }
}

// ── Slang Engine ─────────────────────────────────────────────────────────

async function loadSlang() {
    const drift = await api('/slang/drift?limit=20');
    if (drift) {
        document.getElementById('slang-drift-list').innerHTML = drift.map(d => `
            <div class="alert-item">
                <div class="alert-dot ${d.status === 'candidate' ? 'warning' : 'info'}"></div>
                <div class="alert-content">
                    <div class="alert-title" style="font-family:var(--mono)">${esc(d.term)}</div>
                    <div class="alert-message">${esc(d.context_snippet || '')}</div>
                </div>
                <div style="text-align:right">
                    <div class="text-mono" style="font-size:11px">×${d.frequency}</div>
                    <div class="severity-badge ${d.status === 'candidate' ? 'warning' : 'info'}">${d.status}</div>
                </div>
            </div>
        `).join('');
    }

    const lex = await api('/slang/lexicon');
    if (lex) {
        document.getElementById('lexicon-stats').innerHTML = `
            <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:16px">
                <div class="stat-card accent">
                    <div class="stat-label">Slang Terms</div>
                    <div class="stat-value">${lex.term_count}</div>
                </div>
                <div class="stat-card warning">
                    <div class="stat-label">Drug Categories</div>
                    <div class="stat-value">${lex.substances.length}</div>
                </div>
                <div class="stat-card info">
                    <div class="stat-label">Emoji Patterns</div>
                    <div class="stat-value">${lex.emoji_count}</div>
                </div>
                <div class="stat-card accent">
                    <div class="stat-label">Location Regions</div>
                    <div class="stat-value">${lex.location_regions.length}</div>
                </div>
            </div>
            <div style="margin-top:16px;display:flex;flex-wrap:wrap;gap:4px">
                ${lex.substances.map(s => `<span class="slang-tag">${s}</span>`).join('')}
            </div>
        `;
        document.getElementById('sys-slang-count').textContent = lex.term_count + ' terms';
        document.getElementById('sys-emoji-count').textContent = lex.emoji_count + ' patterns';
        document.getElementById('sys-region-count').textContent = lex.location_regions.length + ' regions';
    }
}

async function analyzeSlang() {
    const text = document.getElementById('slang-input').value.trim();
    if (!text) return;

    const result = await api('/slang/analyze', {
        method: 'POST',
        body: JSON.stringify({ text })
    });
    if (!result) return;

    const score = result.combined_score;
    const cls = score > 0.8 ? 'critical' : score > 0.6 ? 'high' : score > 0.4 ? 'medium' : score > 0.2 ? 'low' : 'clean';
    const color = score > 0.8 ? 'var(--critical)' : score > 0.6 ? '#ff6b35' : score > 0.4 ? 'var(--warning)' : score > 0.2 ? 'var(--info)' : 'var(--success)';

    document.getElementById('slang-result').innerHTML = `
        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px">
            <span style="font-weight:600;color:var(--text-primary)">Analysis Result</span>
            <span class="score-badge ${cls}">${score.toFixed(3)} — ${result.confidence_label}</span>
        </div>
        <div class="slang-score-bar">
            <div class="slang-score-fill" style="width:${score * 100}%;background:${color}"></div>
        </div>
        <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;margin:12px 0;font-size:11px">
            <div><span style="color:var(--text-dim)">ML Score:</span> <span class="text-mono">${(result.ml_score || 0).toFixed(3)}</span></div>
            <div><span style="color:var(--text-dim)">Lexicon Score:</span> <span class="text-mono">${(result.lexicon_score || 0).toFixed(3)}</span></div>
            <div><span style="color:var(--text-dim)">Emoji Score:</span> <span class="text-mono">${(result.emoji_score || 0).toFixed(3)}</span></div>
        </div>
        <div style="margin-top:8px;font-size:11px;font-weight:600;color:var(--text-dim)">DETECTED SUBSTANCES</div>
        <div class="slang-tags">
            ${(result.detected_substances || []).map(s => `<span class="slang-tag">${s}</span>`).join('')}
            ${(result.detected_emoji || []).map(e => `<span class="slang-tag emoji">${e.emoji} ${e.substance}</span>`).join('')}
            ${(result.detected_locations || []).map(l => `<span class="slang-tag location">📍 ${l}</span>`).join('')}
            ${(result.detected_quantities || []).map(q => `<span class="slang-tag quantity">⚖ ${q}</span>`).join('')}
        </div>
        ${(result.matched_terms || []).length > 0 ? `
        <div style="margin-top:12px;font-size:11px;font-weight:600;color:var(--text-dim)">MATCHED TERMS</div>
        <div style="margin-top:4px;font-size:11px;color:var(--text-secondary);font-family:var(--mono)">
            ${result.matched_terms.map(m => `<span style="margin-right:10px">${m.term} <span style="color:var(--text-dim)">[${m.substance}, ${m.language}]</span></span>`).join('')}
        </div>` : ''}
        ${(result.slang_drift_candidates || []).length > 0 ? `
        <div style="margin-top:12px;font-size:11px;font-weight:600;color:var(--warning)">⚠ NEW SLANG CANDIDATES</div>
        <div style="margin-top:4px;font-size:11px;color:var(--warning);font-family:var(--mono)">
            ${result.slang_drift_candidates.map(c => `<span style="margin-right:10px;background:var(--warning-dim);padding:1px 6px;border-radius:2px">${c}</span>`).join('')}
        </div>` : ''}
    `;
}

// ── Settings / Watchlist ─────────────────────────────────────────────────

async function loadSettings() {
    const watchlists = await api('/watchlist');
    if (watchlists) {
        document.getElementById('watchlist-items').innerHTML = watchlists.map(w => `
            <div class="watchlist-item">
                <span class="severity-badge ${w.severity}">${w.severity}</span>
                <span class="watchlist-keyword">${esc(w.keyword)}</span>
                <span style="font-size:10px;color:var(--text-dim)">matches: ${w.alert_count}</span>
                <span class="watchlist-delete" onclick="deleteWatchlist(${w.id})">✕</span>
            </div>
        `).join('');
    }
}

async function addWatchlist() {
    const keyword = document.getElementById('watchlist-keyword').value.trim();
    const severity = document.getElementById('watchlist-severity').value;
    if (!keyword) return;
    await api('/watchlist', { method: 'POST', body: JSON.stringify({ keyword, severity }) });
    document.getElementById('watchlist-keyword').value = '';
    loadSettings();
}

async function deleteWatchlist(id) {
    await api(`/watchlist/${id}`, { method: 'DELETE' });
    loadSettings();
}

// ── Utilities ────────────────────────────────────────────────────────────

function esc(str) {
    if (!str) return '';
    return String(str).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}

function parseArr(val) {
    if (!val || val === '[]') return [];
    try {
        if (typeof val === 'string') return JSON.parse(val.replace(/'/g, '"'));
        return Array.isArray(val) ? val : [];
    } catch { return []; }
}

function timeAgo(ts) {
    if (!ts) return '—';
    const now = Date.now();
    const then = new Date(ts).getTime();
    const diff = Math.floor((now - then) / 1000);
    if (diff < 60) return `${diff}s ago`;
    if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
    if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`;
    return `${Math.floor(diff / 86400)}d ago`;
}

function chartOptions(yLabel) {
    return {
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { labels: { color: '#8896a8', font: { size: 10, family: 'Inter' } } } },
        scales: {
            x: { ticks: { color: '#4a5568', font: { size: 10 } }, grid: { color: '#151d2b' } },
            y: { ticks: { color: '#4a5568', font: { size: 10 } }, grid: { color: '#151d2b' },
                 title: { display: true, text: yLabel, color: '#4a5568', font: { size: 10 } } }
        }
    };
}

// ── Real-time Clock ──────────────────────────────────────────────────────

function updateClock() {
    const now = new Date();
    document.getElementById('topbar-time').textContent =
        now.toLocaleString('en-IN', { hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: false }) +
        ' IST';
}

// ── Score filter display ─────────────────────────────────────────────────

document.getElementById('filter-score')?.addEventListener('input', e => {
    document.getElementById('filter-score-val').textContent = (e.target.value / 100).toFixed(2);
});

// ── Init ─────────────────────────────────────────────────────────────────

document.addEventListener('DOMContentLoaded', () => {
    updateClock();
    setInterval(updateClock, 1000);
    navigateTo('dashboard');
});
