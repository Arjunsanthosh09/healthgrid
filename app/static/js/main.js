// ---------- Scroll reveal ----------
document.addEventListener('DOMContentLoaded', () => {
  const revealEls = document.querySelectorAll('[data-reveal]');
  if ('IntersectionObserver' in window && revealEls.length){
    const io = new IntersectionObserver((entries) => {
      entries.forEach((entry, i) => {
        if (entry.isIntersecting){
          setTimeout(() => entry.target.classList.add('is-visible'), (entry.target.dataset.delay || 0));
          io.unobserve(entry.target);
        }
      });
    }, { threshold: 0.12 });
    revealEls.forEach(el => io.observe(el));
  } else {
    revealEls.forEach(el => el.classList.add('is-visible'));
  }

  // ---------- Password visibility toggle ----------
  document.querySelectorAll('[data-pw-toggle]').forEach(btn => {
    btn.addEventListener('click', () => {
      const input = document.querySelector(btn.dataset.pwToggle);
      if (!input) return;
      const isPw = input.type === 'password';
      input.type = isPw ? 'text' : 'password';
      btn.textContent = isPw ? 'Hide' : 'Show';
    });
  });

  // ---------- Fake-submit forms (static demo) ----------
  document.querySelectorAll('form[data-demo-form]').forEach(form => {
    form.addEventListener('submit', (e) => {
      e.preventDefault();
      const btn = form.querySelector('button[type="submit"]');
      if (!btn) return;
      const original = btn.textContent;
      btn.disabled = true;
      btn.textContent = 'Please wait…';
      setTimeout(() => {
        btn.textContent = '✓ Success — check your email';
        btn.style.background = 'linear-gradient(180deg, #17a06c, #0a4d36)';
        setTimeout(() => {
          btn.disabled = false;
          btn.textContent = original;
        }, 2200);
      }, 900);
    });
  });

  // ---------- Mobile nav toggle ----------
  const navToggle = document.querySelector('.nav-toggle');
  const navLinks = document.querySelector('.nav-links');
  if (navToggle && navLinks){
    navToggle.addEventListener('click', () => {
      navLinks.classList.toggle('open');
    });
  }
});
