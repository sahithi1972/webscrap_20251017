// ...existing code...
/* Handles login page + dashboard behavior (single script for both pages) */

const API_LOGIN = '/api/login';
const API_AUTH_CHECK = '/api/auth/check';
const API_MOVIES = '/api/movies';
const API_LOGOUT = '/api/logout';
const API_UPDATE = '/update';

function getToken(){ return localStorage.getItem('authToken'); }
function setToken(t){ if(t) localStorage.setItem('authToken', t); else localStorage.removeItem('authToken'); }
function authHeaders(){ const t = getToken(); return t ? { 'Authorization': 'Bearer ' + t } : {}; }

function escapeHtml(s){
  return String(s || '').replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('>','&gt;').replaceAll('"','&quot;');
}

/* ---------- LOGIN PAGE ---------- */
const loginForm = document.getElementById('login-form');
if(loginForm){
  const errorEl = document.getElementById('error');
  loginForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    errorEl.classList.add('hidden'); errorEl.textContent = '';
    const username = document.getElementById('username').value.trim();
    const password = document.getElementById('password').value;
    try{
      const res = await fetch(API_LOGIN, {
        method: 'POST',
        headers: {'Content-Type':'application/json'},
        body: JSON.stringify({username, password})
      });
      const json = await res.json().catch(()=> ({}));
      if(!res.ok){
        throw new Error(json.message || 'Login failed');
      }
      if(json.token){
        setToken(json.token);
        window.location.href = '/';
      } else {
        throw new Error('No token received');
      }
    }catch(err){
      errorEl.textContent = err.message || 'Login failed';
      errorEl.classList.remove('hidden');
    }
  });
}

/* ---------- DASHBOARD PAGE ---------- */
const moviesContainer = document.getElementById('movies-container');
const statusEl = document.getElementById('status');
const refreshBtn = document.getElementById('refresh-btn');
const logoutBtn = document.getElementById('logout-btn');
const emptyEl = document.getElementById('empty');

async function checkAuthOrRedirect(){
  try{
    const res = await fetch(API_AUTH_CHECK, { headers: authHeaders() });
    if(!res.ok) throw new Error('unauthenticated');
    return true;
  }catch(e){
    setToken(null);
    window.location.href = '/login.html';
    return false;
  }
}

function showStatus(msg, short=true){
  if(!statusEl) return;
  statusEl.textContent = msg;
  statusEl.classList.remove('hidden');
  if(short) setTimeout(()=>statusEl.classList.add('hidden'), 3500);
}

function createCard(m){
  const div = document.createElement('div');
  div.className = 'movie-card';
  const title = escapeHtml(m.movie_title || 'Untitled');
  const link = m.link || (m.imdb_id ? `https://www.imdb.com/title/${m.imdb_id}/` : '#');
  div.innerHTML = `
    <div>
      <span class="rank">#${m.place ?? '-'}</span>
    </div>
    <h3 class="title"><a href="${link}" target="_blank" rel="noopener noreferrer">${title}</a></h3>
    <p class="details">⭐ ${m.rating ?? '—'} • (${m.year || '—'})</p>
    <p class="cast">${escapeHtml(m.star_cast || '')}</p>
  `;
  return div;
}

async function fetchAndRender(){
  try{
    const res = await fetch(API_MOVIES, { headers: authHeaders() });
    if(res.status === 401){
      // not authorized
      setToken(null);
      window.location.href = '/login.html';
      return;
    }
    const json = await res.json();
    const movies = (json.movies || []).slice(0, 10);
    moviesContainer.innerHTML = '';
    if(!movies.length){
      emptyEl && emptyEl.classList.remove('hidden');
      moviesContainer.classList.add('hidden');
    } else {
      emptyEl && emptyEl.classList.add('hidden');
      moviesContainer.classList.remove('hidden');
      movies.forEach(m => moviesContainer.appendChild(createCard(m)));
    }
    showStatus(`Loaded top ${movies.length}`, true);
  }catch(e){
    console.error(e);
    showStatus('Failed to load movies', true);
  }
}

if(refreshBtn){
  refreshBtn.addEventListener('click', async () => {
    showStatus('Updating...');
    try{
      await fetch(API_UPDATE, { method: 'GET', headers: authHeaders() });
    }catch(e){}
    await fetchAndRender();
  });
}

if(logoutBtn){
  logoutBtn.addEventListener('click', async () => {
    try{
      await fetch(API_LOGOUT, {
        method: 'POST',
        headers: Object.assign({'Content-Type':'application/json'}, authHeaders()),
        body: JSON.stringify({})
      });
    }catch(e){}
    setToken(null);
    window.location.href = '/login.html';
  });
}

/* initialize dashboard if present */
(async function initDashboard(){
  if(!moviesContainer) return;
  const ok = await checkAuthOrRedirect();
  if(!ok) return;
  await fetchAndRender();
  setInterval(fetchAndRender, 5 * 60 * 1000); // auto refresh every 5 minutes
})();
// ...existing code...