// Firebase imports
import { initializeApp } from 'https://www.gstatic.com/firebasejs/10.12.4/firebase-app.js';
import { getAuth, createUserWithEmailAndPassword, signInWithEmailAndPassword, signOut, onAuthStateChanged, updateProfile } from 'https://www.gstatic.com/firebasejs/10.12.4/firebase-auth.js';
import { getFirestore, collection, addDoc, getDocs, query, orderBy, serverTimestamp } from 'https://www.gstatic.com/firebasejs/10.12.4/firebase-firestore.js';

// Firebase configuration
const firebaseConfig = {
  apiKey: 'AIzaSyDViEZzWLLucc1UoxdxNaIag1ZLLEPZ9wQ',
  authDomain: 'darkstarawards.firebaseapp.com',
  projectId: 'darkstarawards',
  storageBucket: 'darkstarawards.firebasestorage.app',
  messagingSenderId: '777341514008',
  appId: '1:777341514008:web:15b6e46490d19f4fbd2e6d',
  measurementId: 'G-86C8YX6VQM'
};

// Initialize Firebase
const app = initializeApp(firebaseConfig);
const auth = getAuth(app);
const db = getFirestore(app);

// Default entries (fallback)
const defaultEntries = [
  {
    title: '[DPRK] Tribes Rivals Team',
    url: 'https://t24085.github.io/TeamDPRK/',
    category: 'Best Overall Website ⭐',
    stack: 'HTML · CSS · JavaScript',
    description: 'A fast, disciplined roster website built to showcase team stats, player performance, and tournament results with interactive charts and animations.'
  },
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

// Render entries as player cards with scores
function renderEntries(entriesToRender = []) {
  const entryGrid = document.getElementById('entryGrid');
  if (!entryGrid) return;
  
  const entries = entriesToRender.length > 0 ? entriesToRender : defaultEntries;
  
  entryGrid.innerHTML = entries
    .map(
      (entry) => {
        const avgScore = entry.scores ? calculateAverageScore(entry.scores) : null;
        const totalScore = entry.scores ? Object.values(entry.scores).reduce((a, b) => a + b, 0) : null;
        
        const entryId = entry.id || entry.title.replace(/\s+/g, '-').toLowerCase();
        
        return `
        <article class="player-card">
          <div class="player-card__header">
            <div class="player-card__meta">
              <span class="chip">${entry.category}</span>
              <span class="stack">${entry.stack}</span>
            </div>
            ${avgScore !== null ? `<div class="player-card__score">${avgScore.toFixed(1)}/100</div>` : ''}
          </div>
          <h3>${entry.title}</h3>
          <p>${entry.description}</p>
          
          <div class="player-card__actions">
            <button class="button button--small" onclick="togglePreview('${entryId}')" id="previewBtn-${entryId}">
              <span class="preview-icon">👁️</span> Show Preview
            </button>
            <a class="button button--small button--ghost" href="${entry.url}" target="_blank" rel="noopener noreferrer">
              Visit Website →
            </a>
          </div>
          
          <div class="player-card__preview" id="preview-${entryId}" style="display: none;">
            <div class="preview-header">
              <span class="preview-label">Live Preview</span>
              <button class="preview-close" onclick="togglePreview('${entryId}')">&times;</button>
            </div>
            <iframe 
              src="${entry.url}" 
              class="preview-iframe"
              frameborder="0"
              allow="fullscreen"
              loading="lazy"
              title="Preview of ${entry.title}">
            </iframe>
          </div>
          
          ${entry.scores ? `
            <div class="player-card__scores-section">
              <h4 class="scores-title">Judging Scores</h4>
              <div class="player-card__stats">
                <div class="stat">
                  <span class="stat__label">Design & Visual Appeal</span>
                  <span class="stat__value">${entry.scores.design || 0}/25</span>
                </div>
                <div class="stat">
                  <span class="stat__label">User Experience (UX)</span>
                  <span class="stat__value">${entry.scores.ux || 0}/25</span>
                </div>
                <div class="stat">
                  <span class="stat__label">Technical Execution</span>
                  <span class="stat__value">${entry.scores.technical || 0}/20</span>
                </div>
                <div class="stat">
                  <span class="stat__label">Creativity & Innovation</span>
                  <span class="stat__value">${entry.scores.creativity || 0}/15</span>
                </div>
                <div class="stat">
                  <span class="stat__label">Accessibility & Best Practices</span>
                  <span class="stat__value">${entry.scores.accessibility || 0}/10</span>
                </div>
                <div class="stat">
                  <span class="stat__label">Content & Messaging</span>
                  <span class="stat__value">${entry.scores.content || 0}/5</span>
                </div>
              </div>
              ${totalScore !== null ? `
                <div class="total-score">
                  <span class="total-score__label">Total Score</span>
                  <span class="total-score__value">${totalScore}/100</span>
                </div>
              ` : ''}
            </div>
          ` : '<div class="player-card__scores-section"><p class="no-scores">Scores pending judge review</p></div>'}
        </article>
      `;
      }
    )
    .join('');
}

function calculateAverageScore(scores) {
  const values = Object.values(scores).filter(v => v !== null && v !== undefined);
  if (values.length === 0) return 0;
  return values.reduce((a, b) => a + b, 0) / values.length;
}

// Toggle website preview
function togglePreview(entryId) {
  const preview = document.getElementById(`preview-${entryId}`);
  const btn = document.getElementById(`previewBtn-${entryId}`);
  
  if (preview.style.display === 'none') {
    preview.style.display = 'block';
    btn.innerHTML = '<span class="preview-icon">👁️</span> Hide Preview';
  } else {
    preview.style.display = 'none';
    btn.innerHTML = '<span class="preview-icon">👁️</span> Show Preview';
  }
}

// Make togglePreview available globally
window.togglePreview = togglePreview;

// Authentication functions
let isSignUpMode = false;

async function handleAuth(e) {
  e.preventDefault();
  const email = document.getElementById('email').value;
  const password = document.getElementById('password').value;
  const displayName = document.getElementById('displayName').value;
  const errorEl = document.getElementById('authError');
  const submitBtn = document.getElementById('authSubmit');
  
  errorEl.textContent = '';
  submitBtn.disabled = true;
  submitBtn.textContent = 'Loading...';
  
  try {
    if (isSignUpMode) {
      const userCredential = await createUserWithEmailAndPassword(auth, email, password);
      if (displayName) {
        await updateProfile(userCredential.user, { displayName });
      }
      closeAuthModal();
    } else {
      await signInWithEmailAndPassword(auth, email, password);
      closeAuthModal();
    }
  } catch (error) {
    errorEl.textContent = error.message.replace('Firebase: ', '').replace('auth/', '');
  } finally {
    submitBtn.disabled = false;
    submitBtn.textContent = isSignUpMode ? 'Sign Up' : 'Sign In';
  }
}

async function handleLogout() {
  try {
    await signOut(auth);
  } catch (error) {
    console.error('Logout error:', error);
  }
}

function toggleAuthMode() {
  isSignUpMode = !isSignUpMode;
  const title = document.getElementById('authModalTitle');
  const submitBtn = document.getElementById('authSubmit');
  const switchText = document.getElementById('authSwitchText');
  const switchBtn = document.getElementById('toggleAuthMode');
  const nameField = document.getElementById('nameField');
  
  if (isSignUpMode) {
    title.textContent = 'Sign Up';
    submitBtn.textContent = 'Sign Up';
    switchText.textContent = 'Already have an account?';
    switchBtn.textContent = 'Sign In';
    nameField.style.display = 'block';
  } else {
    title.textContent = 'Sign In';
    submitBtn.textContent = 'Sign In';
    switchText.textContent = "Don't have an account?";
    switchBtn.textContent = 'Sign Up';
    nameField.style.display = 'none';
  }
  document.getElementById('authError').textContent = '';
  document.getElementById('authForm').reset();
}

function openAuthModal() {
  document.getElementById('authModal').style.display = 'flex';
}

function closeAuthModal() {
  document.getElementById('authModal').style.display = 'none';
  document.getElementById('authForm').reset();
  document.getElementById('authError').textContent = '';
  isSignUpMode = false;
  toggleAuthMode();
}

function openSubmitModal() {
  document.getElementById('submitModal').style.display = 'flex';
}

function closeSubmitModal() {
  document.getElementById('submitModal').style.display = 'none';
  document.getElementById('submitEntryForm').reset();
  document.getElementById('submitError').textContent = '';
  document.getElementById('submitSuccess').textContent = '';
}

// Firestore functions
async function loadEntries() {
  try {
    const q = query(collection(db, 'entries'), orderBy('createdAt', 'desc'));
    const querySnapshot = await getDocs(q);
    const entries = [];
    querySnapshot.forEach((doc) => {
      entries.push({ id: doc.id, ...doc.data() });
    });
    return entries;
  } catch (error) {
    console.error('Error loading entries:', error);
    return defaultEntries;
  }
}

async function saveEntry(entryData) {
  try {
    const entry = {
      ...entryData,
      submitterId: auth.currentUser.uid,
      submitterName: auth.currentUser.displayName || auth.currentUser.email,
      createdAt: serverTimestamp(),
      scores: {
        design: 0,
        ux: 0,
        technical: 0,
        creativity: 0,
        accessibility: 0,
        content: 0
      }
    };
    await addDoc(collection(db, 'entries'), entry);
    return true;
  } catch (error) {
    console.error('Error saving entry:', error);
    throw error;
  }
}

async function handleSubmitEntry(e) {
  e.preventDefault();
  const errorEl = document.getElementById('submitError');
  const successEl = document.getElementById('submitSuccess');
  const submitBtn = e.target.querySelector('button[type="submit"]');
  
  errorEl.textContent = '';
  successEl.textContent = '';
  submitBtn.disabled = true;
  submitBtn.textContent = 'Submitting...';
  
  try {
    const entryData = {
      title: document.getElementById('entryTitle').value,
      url: document.getElementById('entryUrl').value,
      category: document.getElementById('entryCategory').value,
      stack: document.getElementById('entryStack').value,
      description: document.getElementById('entryDescription').value
    };
    
    await saveEntry(entryData);
    successEl.textContent = 'Entry submitted successfully!';
    setTimeout(() => {
      closeSubmitModal();
      loadAndRenderEntries();
    }, 1500);
  } catch (error) {
    errorEl.textContent = error.message || 'Failed to submit entry. Please try again.';
  } finally {
    submitBtn.disabled = false;
    submitBtn.textContent = 'Submit Entry';
  }
}

async function loadAndRenderEntries() {
  const entries = await loadEntries();
  renderEntries(entries);
}

// Slow down background video playback speed and skip the last 2 seconds
document.addEventListener('DOMContentLoaded', () => {
  // Load entries from Firestore
  loadAndRenderEntries();
  
  // Auth event listeners
  document.getElementById('authButton').addEventListener('click', openAuthModal);
  document.getElementById('closeAuthModal').addEventListener('click', closeAuthModal);
  document.getElementById('toggleAuthMode').addEventListener('click', toggleAuthMode);
  document.getElementById('authForm').addEventListener('submit', handleAuth);
  
  // Submit entry event listeners
  document.getElementById('showSubmitForm').addEventListener('click', openSubmitModal);
  document.getElementById('closeSubmitModal').addEventListener('click', closeSubmitModal);
  document.getElementById('submitEntryForm').addEventListener('submit', handleSubmitEntry);
  
  // Close modals on outside click
  document.getElementById('authModal').addEventListener('click', (e) => {
    if (e.target.id === 'authModal') closeAuthModal();
  });
  document.getElementById('submitModal').addEventListener('click', (e) => {
    if (e.target.id === 'submitModal') closeSubmitModal();
  });
  
  // Auth state observer
  onAuthStateChanged(auth, (user) => {
    const authButton = document.getElementById('authButton');
    const authStatus = document.getElementById('authStatus');
    const submitSection = document.getElementById('submitEntrySection');
    
    if (user) {
      authButton.textContent = 'Sign Out';
      authButton.onclick = handleLogout;
      authStatus.textContent = `Signed in as ${user.displayName || user.email}`;
      submitSection.style.display = 'block';
    } else {
      authButton.textContent = 'Sign In';
      authButton.onclick = openAuthModal;
      authStatus.textContent = '';
      submitSection.style.display = 'none';
    }
  });
  
  const videos = document.querySelectorAll('.site-background');
  videos.forEach(video => {
    video.playbackRate = 0.25; // Set to 25% speed (very slow)
    
    // Skip the last 2 seconds of the video (for a 6 second video, loop at 4 seconds)
    const skipLastSeconds = 2;
    let loopEndTime = 4; // Default to 4 seconds for a 6 second video
    
    video.addEventListener('loadedmetadata', () => {
      // Calculate loop end time, but ensure it's at least 4 seconds for a 6 second video
      loopEndTime = Math.max(4, video.duration - skipLastSeconds);
    });
    
    // Aggressive checking using requestAnimationFrame for smooth looping
    function checkVideoTime() {
      if (video.readyState >= 2) { // Check if video has loaded metadata
        if (video.currentTime >= loopEndTime) {
          video.currentTime = 0; // Loop back to the beginning
        }
      }
      requestAnimationFrame(checkVideoTime);
    }
    checkVideoTime();
    
    // Backup check on timeupdate
    video.addEventListener('timeupdate', () => {
      if (video.currentTime >= loopEndTime) {
        video.currentTime = 0;
      }
    });
  });
});
