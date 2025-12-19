import { initializeApp } from 'https://www.gstatic.com/firebasejs/10.12.4/firebase-app.js';
import { getAuth, GoogleAuthProvider, signInWithPopup, signOut, onAuthStateChanged } from 'https://www.gstatic.com/firebasejs/10.12.4/firebase-auth.js';

const firebaseConfig = {
  apiKey: 'YOUR_API_KEY',
  authDomain: 'project-777341514008.firebaseapp.com',
  projectId: 'project-777341514008',
  storageBucket: 'project-777341514008.appspot.com',
  messagingSenderId: 'YOUR_MESSAGING_SENDER_ID',
  appId: 'YOUR_APP_ID',
  measurementId: 'YOUR_MEASUREMENT_ID'
};

const app = initializeApp(firebaseConfig);
const auth = getAuth(app);
const provider = new GoogleAuthProvider();

const entries = [
  {
    title: 'Celestial Portfolio',
    url: 'https://example.com/celestial-portfolio',
    category: 'Best UI / Visual Design',
    stack: 'Next.js · Tailwind · Vercel',
    description: 'A cinematic portfolio with parallax storytelling for a concept artist.'
  },
  {
    title: 'Nebula Labs',
    url: 'https://example.com/nebula-labs',
    category: 'Best Performance & Optimization',
    stack: 'SvelteKit · Cloudflare Pages',
    description: 'Ultra-fast product landing page with motion-friendly accessibility.'
  },
  {
    title: 'Aurora Festival',
    url: 'https://example.com/aurora-festival',
    category: 'Best UX / Usability',
    stack: 'Remix · Headless CMS',
    description: 'Ticketing experience with clear CTAs, mobile-first flows, and live schedule updates.'
  }
];

const entryGrid = document.getElementById('entryGrid');
const signInBtn = document.getElementById('googleSignIn');
const authStatus = document.getElementById('authStatus');

function renderEntries() {
  if (!entryGrid) return;
  entryGrid.innerHTML = entries
    .map(
      (entry) => `
        <article class="entry-card">
          <div class="entry-card__meta">
            <span class="chip">${entry.category}</span>
            <span class="stack">${entry.stack}</span>
          </div>
          <h3>${entry.title}</h3>
          <p>${entry.description}</p>
          <a class="entry-card__link" href="${entry.url}" target="_blank" rel="noopener noreferrer">Visit Website</a>
        </article>
      `
    )
    .join('');
}

async function toggleAuth() {
  if (!auth || !signInBtn) return;
  if (auth.currentUser) {
    await signOut(auth);
  } else {
    await signInWithPopup(auth, provider);
  }
}

function updateAuthUI(user) {
  if (!signInBtn || !authStatus) return;
  if (user) {
    signInBtn.textContent = 'Sign out';
    authStatus.textContent = `Signed in as ${user.displayName || user.email}`;
  } else {
    signInBtn.textContent = 'Sign in with Google';
    authStatus.textContent = 'Sign in to save entries and track judging status.';
  }
}

if (signInBtn) {
  signInBtn.addEventListener('click', () => toggleAuth().catch(console.error));
}

onAuthStateChanged(auth, updateAuthUI);
renderEntries();
