// ── Chart defaults (dark theme) ───────────────────────────────────────────────
Chart.defaults.color          = '#666';
Chart.defaults.borderColor    = '#2e2c29';
Chart.defaults.font.family    = "'Inter', 'Segoe UI', Arial, sans-serif";
Chart.defaults.font.size      = 11;

const WIN_COLOR  = '#81b64c';
const LOSS_COLOR = '#fa412d';
const DRAW_COLOR = '#555555';

const charts = {};

function destroyChart(id) {
    if (charts[id]) { charts[id].destroy(); delete charts[id]; }
}

// ── State ─────────────────────────────────────────────────────────────────────
let activeTimeClass = 'all';

document.addEventListener('DOMContentLoaded', () => {
    // Restore user from cookie
    const cookieUser = document.cookie.match(/(?:^|; )chess_user=([^;]*)/)?.[1];
    if (cookieUser) document.getElementById('user-input').value = decodeURIComponent(cookieUser);

    // Tab group
    document.getElementById('tc-tabs').addEventListener('click', e => {
        const btn = e.target.closest('button[data-tc]');
        if (!btn) return;
        document.querySelectorAll('#tc-tabs button').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        activeTimeClass = btn.dataset.tc;
    });

    // Auto-load if user is set
    if (document.getElementById('user-input').value) loadStats();
});

async function loadStats() {
    const user = document.getElementById('user-input').value.trim();
    if (!user) return;

    document.getElementById('loading').textContent  = 'Loading…';
    document.getElementById('loading').style.display = '';
    document.getElementById('content').style.display = 'none';
    document.getElementById('error-msg').style.display = 'none';

    const resp = await fetch(`/stats/data?user=${encodeURIComponent(user)}&time_class=${activeTimeClass}`);
    if (!resp.ok) {
        showError((await resp.json()).error || 'Failed to load stats.');
        return;
    }
    const data = await resp.json();

    document.getElementById('loading').style.display  = 'none';
    document.getElementById('content').style.display  = '';

    renderOverview(data.overview);
    renderResultsChart(data.overview);
    renderDayChart(data.by_day);
    renderOpenings(data.openings);
    renderOpponents(data.opponents);
    renderTimeChart(data.per_day);
}

// ── Overview chips ────────────────────────────────────────────────────────────
function renderOverview(ov) {
    if (!ov) return;
    const s = ov.stats || {};
    const chips = [
        { val: s.no_games ?? '–',                      lbl: 'Games' },
        { val: pct(s.win),   lbl: 'Win %',   color: WIN_COLOR },
        { val: pct(s.loss),  lbl: 'Loss %',  color: LOSS_COLOR },
        { val: ov.accuracy != null ? ov.accuracy + '%' : '–', lbl: 'Accuracy' },
    ];
    document.getElementById('overview-grid').innerHTML = chips.map(c => `
        <div class="chip">
            <div class="chip-val" style="${c.color ? `color:${c.color}` : ''}">${c.val}</div>
            <div class="chip-lbl">${c.lbl}</div>
        </div>`).join('');
}

// ── Results donut ─────────────────────────────────────────────────────────────
function renderResultsChart(ov) {
    destroyChart('results');
    if (!ov) return;
    const s = ov.stats || {};
    const total = s.no_games || 1;
    const wins  = Math.round((s.win  || 0) / 100 * total);
    const losses = Math.round((s.loss || 0) / 100 * total);
    const draws  = total - wins - losses;
    charts['results'] = new Chart(document.getElementById('chart-results'), {
        type: 'doughnut',
        data: {
            labels: ['Win', 'Loss', 'Draw'],
            datasets: [{ data: [wins, losses, draws],
                backgroundColor: [WIN_COLOR, LOSS_COLOR, DRAW_COLOR],
                borderWidth: 0, hoverOffset: 6 }]
        },
        options: {
            plugins: { legend: { position: 'bottom', labels: { padding: 16, boxWidth: 12 } } },
            cutout: '65%'
        }
    });
}

// ── Day of week bar ───────────────────────────────────────────────────────────
function renderDayChart(byDay) {
    destroyChart('day');
    if (!byDay) return;
    const days = ['mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun'];
    const labels = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];
    charts['day'] = new Chart(document.getElementById('chart-day'), {
        type: 'bar',
        data: {
            labels,
            datasets: [
                { label: 'Win',  data: days.map(d => byDay[d]?.win  || 0), backgroundColor: WIN_COLOR  },
                { label: 'Loss', data: days.map(d => byDay[d]?.loss || 0), backgroundColor: LOSS_COLOR },
                { label: 'Draw', data: days.map(d => byDay[d]?.draw || 0), backgroundColor: DRAW_COLOR },
            ]
        },
        options: {
            plugins: { legend: { position: 'bottom', labels: { padding: 12, boxWidth: 10 } } },
            scales: {
                x: { stacked: true, grid: { display: false } },
                y: { stacked: true, ticks: { precision: 0 } }
            }
        }
    });
}

// ── Performance over time ─────────────────────────────────────────────────────
function renderTimeChart(perDay) {
    destroyChart('time');
    if (!perDay) return;
    const dates  = Object.keys(perDay).sort();
    const wins   = dates.map(d => perDay[d].win  || 0);
    const losses = dates.map(d => perDay[d].loss || 0);
    const draws  = dates.map(d => perDay[d].draw || 0);
    charts['time'] = new Chart(document.getElementById('chart-time'), {
        type: 'bar',
        data: {
            labels: dates,
            datasets: [
                { label: 'Win',  data: wins,   backgroundColor: WIN_COLOR,  stack: 's' },
                { label: 'Loss', data: losses, backgroundColor: LOSS_COLOR, stack: 's' },
                { label: 'Draw', data: draws,  backgroundColor: DRAW_COLOR, stack: 's' },
            ]
        },
        options: {
            plugins: { legend: { display: false } },
            scales: {
                x: { stacked: true, ticks: { maxTicksLimit: 12, maxRotation: 0 }, grid: { display: false } },
                y: { stacked: true, ticks: { precision: 0 } }
            }
        }
    });
}

// ── Openings table ────────────────────────────────────────────────────────────
function renderOpenings(openings) {
    const el = document.getElementById('openings-body');
    if (!openings?.length) { el.innerHTML = '<div style="color:#555;font-size:0.85em">No data</div>'; return; }
    const rows = openings.map(o => {
        const w = o.winpercentage || 0, l = o.lossPercentage || 0, d = o.drawpercentage || 0;
        return `<tr>
            <td style="font-weight:600;color:#e8e6e3">${o.ECO || '–'}</td>
            <td>${o.games}</td>
            <td style="color:${WIN_COLOR}">${w}%</td>
            <td style="color:${LOSS_COLOR}">${l}%</td>
            <td>
                <div class="wld-bar">
                    <div class="wld-w" style="width:${w}%"></div>
                    <div class="wld-l" style="width:${l}%"></div>
                    <div class="wld-d" style="width:${d}%"></div>
                </div>
            </td>
        </tr>`;
    }).join('');
    el.innerHTML = `<table>
        <thead><tr><th>ECO</th><th>Games</th><th>Win</th><th>Loss</th><th></th></tr></thead>
        <tbody>${rows}</tbody>
    </table>`;
}

// ── Opponents list ────────────────────────────────────────────────────────────
function renderOpponents(opponents) {
    const el = document.getElementById('opponents-body');
    if (!opponents?.length) { el.innerHTML = '<div style="color:#555;font-size:0.85em">No data</div>'; return; }
    el.innerHTML = opponents.map(o => `
        <div class="opp-row">
            <span class="opp-name">${escHtml(o.opponent)}</span>
            <span class="opp-count">${o.count} games</span>
        </div>`).join('');
}

// ── Helpers ───────────────────────────────────────────────────────────────────
function pct(v) { return v != null ? v + '%' : '–'; }
function showError(msg) {
    document.getElementById('loading').style.display  = 'none';
    document.getElementById('error-msg').textContent  = msg;
    document.getElementById('error-msg').style.display = '';
}
function escHtml(s) {
    return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
}
