/* HIMI — Main JavaScript */
document.addEventListener('DOMContentLoaded', () => {

  // Count-up animation for stat values
  document.querySelectorAll('.stat-val[data-target]').forEach(el => {
    const target = parseFloat(el.dataset.target);
    const suffix = el.dataset.suffix || '';
    const isFloat = String(target).includes('.');
    const dur = 1100, start = performance.now();
    const tick = now => {
      const p = Math.min((now - start) / dur, 1);
      const eased = 1 - Math.pow(1 - p, 3);
      el.textContent = (isFloat ? (eased*target).toFixed(1) : Math.floor(eased*target)) + suffix;
      if (p < 1) requestAnimationFrame(tick);
    };
    requestAnimationFrame(tick);
  });

  // Animate progress bars
  document.querySelectorAll('.prog-fill[data-w]').forEach(el => {
    setTimeout(() => { el.style.width = el.dataset.w + '%'; }, 150);
  });

  // Auto-dismiss flash messages
  document.querySelectorAll('.flash-msg').forEach(el => {
    setTimeout(() => {
      el.style.transition = 'opacity 0.5s, transform 0.5s';
      el.style.opacity = '0'; el.style.transform = 'translateY(-10px)';
      setTimeout(() => el.remove(), 500);
    }, 4500);
  });

  // Assignment check click
  document.querySelectorAll('.asgn-check[data-href]').forEach(btn => {
    btn.addEventListener('click', () => {
      btn.innerHTML = '&#10003;'; btn.classList.add('done');
      const title = btn.closest('.asgn-item')?.querySelector('.asgn-title');
      if (title) title.classList.add('done');
      setTimeout(() => window.location.href = btn.dataset.href, 380);
    });
  });

  // Login demo fill
  document.querySelectorAll('.demo-item[data-user]').forEach(el => {
    el.addEventListener('click', () => {
      const u = document.querySelector('input[name=username]');
      const p = document.querySelector('input[name=password]');
      if (u && p) { u.value = el.dataset.user; p.value = el.dataset.pass; }
      el.style.background = 'rgba(30,95,173,0.15)';
      setTimeout(() => el.style.background = '', 300);
    });
  });

  // Role toggle in add-user form
  const roleSelect = document.getElementById('role-select');
  if (roleSelect) {
    const toggle = () => {
      const r = roleSelect.value;
      const fc = document.getElementById('field-class');
      const fs = document.getElementById('field-subject');
      if (fc) fc.style.display = r === 'student' ? '' : 'none';
      if (fs) fs.style.display = r === 'teacher' ? '' : 'none';
    };
    roleSelect.addEventListener('change', toggle); toggle();
  }

  // Stagger card entrance
  document.querySelectorAll('.stat-card, .card, .ann-card, .lesson-card').forEach((el, i) => {
    el.style.opacity = '0'; el.style.transform = 'translateY(18px)';
    el.style.transition = 'opacity 0.38s ease, transform 0.38s ease';
    setTimeout(() => { el.style.opacity = '1'; el.style.transform = 'none'; }, 50 + i * 45);
  });
});
