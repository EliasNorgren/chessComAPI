const params = new URLSearchParams(window.location.search);

document.addEventListener('DOMContentLoaded', () => {
    const userFromUrl = params.get('user') || '';
    if (userFromUrl) {
        document.getElementById('user-input').value = userFromUrl;
        loadSets();
    }
});

function getUser() {
    return document.getElementById('user-input').value.trim();
}

function fmtSeconds(s) {
    if (s == null) return '–';
    const m = Math.floor(s / 60);
    const sec = s % 60;
    return `${m}:${String(sec).padStart(2, '0')}`;
}

async function loadSets() {
    const user = getUser();
    if (!user) return;
    history.replaceState(null, '', `?user=${encodeURIComponent(user)}`);

    const list = document.getElementById('sets-list');
    list.innerHTML = '<div style="padding:1em;color:#555;font-size:0.9em;">Loading…</div>';

    const resp = await fetch(`/woodpecker/api/sets?user=${encodeURIComponent(user)}`);
    const sets = await resp.json();

    if (!sets.length) {
        list.innerHTML = '<div style="padding:1.5em 1em;text-align:center;color:#555;font-size:0.9em;">No sets yet — create one above.</div>';
        return;
    }

    list.innerHTML = sets.map(s => {
        const resumeLabel = s.has_active ? 'Resume' : 'Solve';
        const bestTime = fmtSeconds(s.best_seconds);
        const date = s.last_completed ? s.last_completed.substring(0, 10) : '–';
        const activeBadge = s.has_active ? '<span class="badge">In progress</span>' : '';
        return `
        <div class="set-row">
            <div class="set-info">
                <div class="set-name">${escHtml(s.name)}${activeBadge}</div>
                <div class="set-meta">${s.rating_min}–${s.rating_max} · ${s.size} puzzles · created ${s.created_at.substring(0,10)}</div>
            </div>
            <div class="set-stats">
                <div class="stat-chip">
                    <div class="val">${s.completed_count}</div>
                    <div class="lbl">Runs</div>
                </div>
                <div class="stat-chip">
                    <div class="val">${bestTime}</div>
                    <div class="lbl">Best</div>
                </div>
                <div class="stat-chip">
                    <div class="val">${date}</div>
                    <div class="lbl">Last</div>
                </div>
            </div>
            <div class="set-actions">
                <button onclick="solveSet(${s.id})">${resumeLabel}</button>
                <button class="danger" onclick="deleteSet(${s.id}, this)">✕</button>
            </div>
        </div>`;
    }).join('');
}

function solveSet(setId) {
    const user = getUser();
    if (!user) return;
    window.location.href = `/woodpecker/puzzle?set_id=${setId}&user=${encodeURIComponent(user)}`;
}

async function deleteSet(setId, btn) {
    if (!confirm('Delete this set and all its history?')) return;
    btn.disabled = true;
    const user = getUser();
    const resp = await fetch(`/woodpecker/api/set/${setId}`, {
        method: 'DELETE',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ user })
    });
    if (resp.ok) {
        loadSets();
    } else {
        btn.disabled = false;
        alert('Failed to delete set.');
    }
}

async function createSet() {
    const user = getUser();
    if (!user) { alert('Enter a username first.'); return; }

    const name      = document.getElementById('f-name').value.trim();
    const ratingMin = parseInt(document.getElementById('f-min').value);
    const ratingMax = parseInt(document.getElementById('f-max').value);
    const count     = parseInt(document.getElementById('f-count').value);

    if (!name) { alert('Give the set a name.'); return; }
    if (ratingMin >= ratingMax) { alert('Min rating must be less than max rating.'); return; }

    const btn    = document.getElementById('create-btn');
    const status = document.getElementById('create-status');
    btn.disabled = true;
    status.textContent = 'Scanning puzzles… this may take ~15 s';

    const resp = await fetch('/woodpecker/api/create_set', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ user, name, rating_min: ratingMin, rating_max: ratingMax, count })
    });

    btn.disabled = false;

    if (!resp.ok) {
        const err = await resp.json();
        status.textContent = err.error || 'Error creating set.';
        status.style.color = '#fa412d';
        return;
    }

    const data = await resp.json();
    status.textContent = `Created with ${data.count} puzzles.`;
    status.style.color = '#81b64c';
    document.getElementById('f-name').value = '';
    loadSets();
}

function escHtml(str) {
    return str.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}
