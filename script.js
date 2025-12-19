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

renderEntries();
