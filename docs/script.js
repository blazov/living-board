// Mobile nav toggle
const navToggle = document.querySelector('.nav-toggle');
const navLinks = document.querySelector('.nav-links');

navToggle.addEventListener('click', () => {
  navLinks.classList.toggle('active');
});

// Close mobile nav when clicking a link
navLinks.querySelectorAll('a').forEach(link => {
  link.addEventListener('click', () => {
    navLinks.classList.remove('active');
  });
});

// Portfolio card expand/collapse
function togglePortfolioCard(header) {
  const card = header.closest('.portfolio-card');
  const wasOpen = card.classList.contains('open');

  // Close all cards
  document.querySelectorAll('.portfolio-card').forEach(c => {
    c.classList.remove('open');
    c.querySelector('.portfolio-header').setAttribute('aria-expanded', 'false');
  });

  // Toggle clicked card
  if (!wasOpen) {
    card.classList.add('open');
    header.setAttribute('aria-expanded', 'true');
  }
}

document.querySelectorAll('.portfolio-header').forEach(header => {
  header.addEventListener('click', () => togglePortfolioCard(header));
  header.addEventListener('keydown', e => {
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault();
      togglePortfolioCard(header);
    }
  });
});

// Open first portfolio card by default
const firstCard = document.querySelector('.portfolio-card');
if (firstCard) firstCard.classList.add('open');

// Smooth scroll offset for fixed nav
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
  anchor.addEventListener('click', e => {
    e.preventDefault();
    const target = document.querySelector(anchor.getAttribute('href'));
    if (target) {
      const offset = 80;
      const pos = target.getBoundingClientRect().top + window.scrollY - offset;
      window.scrollTo({ top: pos, behavior: 'smooth' });
    }
  });
});
