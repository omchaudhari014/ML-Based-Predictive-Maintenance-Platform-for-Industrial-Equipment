/* auth.js — OPTIONAL, mock authentication.

   Authentication is NOT required for the main demo flow (§ master prompt): a
   visitor can upload → analyse → explore every page without an account. This
   module exists so login/register/history can show a signed-in state, and so
   the wiring is already Firebase-shaped for a later swap.

   Firebase is deliberately NOT connected yet (§ master prompt). The method
   names and shapes below mirror Firebase Auth (signInWithEmailAndPassword,
   createUserWithEmailAndPassword, signOut, onAuthStateChanged) so replacing
   this file with a real firebase/auth wrapper is a like-for-like change with no
   caller edits.

   The "user store" is localStorage, and passwords are NOT securely hashed —
   this is a front-end demo with no backend, and this file must never be treated
   as real credential storage. The moment a backend exists, this whole file is
   replaced. */

const USERS_KEY = 'pdm.auth.users';   // [{ name, email, pwHash }]
const SESSION_KEY = 'pdm.auth.current'; // { name, email }

const listeners = new Set();

function read(key, fallback) {
  try { const v = JSON.parse(localStorage.getItem(key)); return v ?? fallback; }
  catch { return fallback; }
}
function write(key, value) {
  try { localStorage.setItem(key, JSON.stringify(value)); return true; } catch { return false; }
}

/* A deliberately weak, clearly-not-secure obfuscation. Named honestly so no one
   mistakes it for real hashing. */
function weakHash(s) {
  let h = 0;
  for (let i = 0; i < s.length; i++) { h = (h << 5) - h + s.charCodeAt(i); h |= 0; }
  return `demo$${h}`;
}

function notify(user) {
  for (const cb of listeners) { try { cb(user); } catch { /* ignore */ } }
}

/* ── Firebase-shaped surface ─────────────────────────────────────────────── */

export function getCurrentUser() {
  return read(SESSION_KEY, null);
}

export function isSignedIn() {
  return !!getCurrentUser();
}

/* Fires cb(user|null) immediately with the current state and on every change.
   Returns an unsubscribe function, exactly like Firebase's onAuthStateChanged. */
export function onAuthStateChanged(cb) {
  listeners.add(cb);
  try { cb(getCurrentUser()); } catch { /* ignore */ }
  return () => listeners.delete(cb);
}

export async function createUserWithEmailAndPassword(name, email, password) {
  const users = read(USERS_KEY, []);
  const e = String(email).trim().toLowerCase();
  if (!e || !/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(e)) throw new Error('Please enter a valid email address.');
  if (String(password).length < 8) throw new Error('Password must be at least 8 characters.');
  if (users.some((u) => u.email === e)) throw new Error('An account with this email already exists.');

  const user = { name: String(name).trim() || e.split('@')[0], email: e };
  users.push({ ...user, pwHash: weakHash(password) });
  write(USERS_KEY, users);
  write(SESSION_KEY, user);
  notify(user);
  return user;
}

export async function signInWithEmailAndPassword(email, password) {
  const users = read(USERS_KEY, []);
  const e = String(email).trim().toLowerCase();
  const match = users.find((u) => u.email === e);
  if (!match || match.pwHash !== weakHash(password)) {
    throw new Error('Email or password is incorrect.');
  }
  const user = { name: match.name, email: match.email };
  write(SESSION_KEY, user);
  notify(user);
  return user;
}

export async function signOut() {
  try { localStorage.removeItem(SESSION_KEY); } catch { /* ignore */ }
  notify(null);
}

/* Initials for the avatar chip. */
export function initialsFor(user) {
  if (!user) return '';
  const base = user.name || user.email || '';
  const parts = base.replace(/@.*/, '').split(/[.\s_-]+/).filter(Boolean);
  const chars = parts.length >= 2 ? parts[0][0] + parts[1][0] : base.slice(0, 2);
  return chars.toUpperCase();
}
