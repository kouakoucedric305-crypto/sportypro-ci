// SportyPro CI — main.js
// Crédité par Kouakou Cedric

function toggleMenu() {
  const nav = document.getElementById('mobileNav');
  nav.classList.toggle('open');
}

// Fermer le menu mobile au clic extérieur
document.addEventListener('click', (e) => {
  const nav = document.getElementById('mobileNav');
  const btn = document.querySelector('.mobile-menu-btn');
  if (nav && !nav.contains(e.target) && e.target !== btn) {
    nav.classList.remove('open');
  }
});

// Animation apparition des cartes
document.addEventListener('DOMContentLoaded', () => {
  const cards = document.querySelectorAll('.match-card, .prono-row, .feature-card');
  const observer = new IntersectionObserver((entries) => {
    entries.forEach((entry, i) => {
      if (entry.isIntersecting) {
        setTimeout(() => {
          entry.target.style.opacity = '1';
          entry.target.style.transform = 'translateY(0)';
        }, i * 40);
        observer.unobserve(entry.target);
      }
    });
  }, { threshold: 0.05 });

  cards.forEach(card => {
    card.style.opacity = '0';
    card.style.transform = 'translateY(16px)';
    card.style.transition = 'opacity .4s ease, transform .4s ease';
    observer.observe(card);
  });
});

// Mise à jour du timestamp live
function updateLiveClock() {
  const el = document.querySelector('.live-badge');
  if (el) {
    const now = new Date();
    const time = now.toLocaleTimeString('fr-FR', {hour:'2-digit', minute:'2-digit'});
    el.innerHTML = `<span class="pulse"></span> LIVE ${time}`;
  }
}
setInterval(updateLiveClock, 30000);
