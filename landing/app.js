/* NeuroKids landing — behaviour: cast mount, reveal, eye tracking, cheer, nav, form. */
(() => {
  'use strict';

  const reduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  const finePointer = window.matchMedia('(pointer: fine)').matches;

  /* ---------- illustrations ---------- */
  NKCast.mount();
  document.querySelectorAll('[data-spark]').forEach((p) => {
    const [x, y, s] = p.dataset.spark.split(' ').map(Number);
    p.setAttribute('d', NKCast.spark(x, y, s));
  });

  /* ---------- scroll reveal (once) ---------- */
  const revealIO = new IntersectionObserver((entries) => {
    entries.forEach((e) => {
      if (!e.isIntersecting) return;
      e.target.classList.add('is-in');
      revealIO.unobserve(e.target);
    });
  }, { threshold: 0.15, rootMargin: '0px 0px -40px 0px' });
  document.querySelectorAll('.reveal, [data-reveal], .pop').forEach((el) => revealIO.observe(el));

  /* ---------- pause idle loops off-screen ---------- */
  const visible = new Set();
  const offIO = new IntersectionObserver((entries) => {
    entries.forEach((e) => {
      e.target.classList.toggle('is-off', !e.isIntersecting);
      e.isIntersecting ? visible.add(e.target) : visible.delete(e.target);
    });
  }, { rootMargin: '120px 0px' });
  document.querySelectorAll('[data-section]').forEach((s) => offIO.observe(s));

  /* ---------- eyes follow the pointer ---------- */
  if (finePointer && !reduced) {
    let px = 0, py = 0, queued = false;
    const update = () => {
      queued = false;
      visible.forEach((section) => {
        section.querySelectorAll('.ch-eyes').forEach((eyes) => {
          const look = eyes.firstElementChild;
          const r = eyes.getBoundingClientRect();
          const dx = px - (r.left + r.width / 2);
          const dy = py - (r.top + r.height / 2);
          const d = Math.hypot(dx, dy) || 1;
          const k = Math.min(1, d / 260);
          look.style.transform = `translate(${((dx / d) * 3.2 * k).toFixed(2)}px, ${((dy / d) * 2.6 * k).toFixed(2)}px)`;
        });
      });
    };
    window.addEventListener('pointermove', (e) => {
      px = e.clientX; py = e.clientY;
      if (!queued) { queued = true; requestAnimationFrame(update); }
    }, { passive: true });
  }

  /* ---------- click a character → it cheers ---------- */
  const BURST = ['saffron-400', 'red-400', 'blue-500', 'grass-500', 'aqua-400', 'orange-400'];
  function cheer(el) {
    if (!el || el.classList.contains('is-cheer')) return;
    el.classList.add('is-cheer');
    setTimeout(() => el.classList.remove('is-cheer'), 900);
    if (reduced) return;
    const host = el.offsetParent || document.body;
    const er = el.getBoundingClientRect(), hr = host.getBoundingClientRect();
    for (let i = 0; i < 6; i++) {
      const b = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
      b.setAttribute('viewBox', '-12 -12 24 24');
      b.classList.add('burst');
      const p = document.createElementNS('http://www.w3.org/2000/svg', 'path');
      p.setAttribute('d', i % 2 ? NKCast.heart(0, 0, 10) : NKCast.spark(0, 0, 11));
      p.style.fill = `var(--nk-${BURST[i % BURST.length]})`;
      b.appendChild(p);
      const a = (-90 + (i - 2.5) * 28) * (Math.PI / 180);
      const dist = 60 + Math.random() * 40;
      b.style.left = `${er.left - hr.left + er.width / 2 - 11}px`;
      b.style.top = `${er.top - hr.top + er.height * 0.25}px`;
      b.style.setProperty('--bx', `${Math.cos(a) * dist}px`);
      b.style.setProperty('--by', `${Math.sin(a) * dist}px`);
      b.style.setProperty('--br', `${(Math.random() - 0.5) * 90}deg`);
      host.appendChild(b);
      setTimeout(() => b.remove(), 1150);
    }
  }
  document.addEventListener('click', (e) => {
    const el = e.target.closest('[data-cheer]');
    if (el) cheer(el);
  });

  /* ---------- nav: hairline on scroll + mobile sheet ---------- */
  const nav = document.getElementById('nav');
  const onScroll = () => nav.classList.toggle('is-scrolled', window.scrollY > 8);
  window.addEventListener('scroll', onScroll, { passive: true });
  onScroll();

  const toggle = document.querySelector('.nav-toggle');
  const sheet = document.getElementById('sheet');
  const setSheet = (open) => {
    sheet.classList.toggle('is-open', open);
    toggle.setAttribute('aria-expanded', String(open));
    toggle.setAttribute('aria-label', open ? 'Закрыть меню' : 'Открыть меню');
    toggle.querySelector('use').setAttribute('href', open ? '#i-close' : '#i-menu');
    document.body.style.overflow = open ? 'hidden' : '';
  };
  toggle.addEventListener('click', () => setSheet(!sheet.classList.contains('is-open')));
  sheet.addEventListener('click', (e) => { if (e.target.closest('a')) setSheet(false); });
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && sheet.classList.contains('is-open')) { setSheet(false); toggle.focus(); }
  });
  window.matchMedia('(min-width: 1128px)').addEventListener('change', (m) => { if (m.matches) setSheet(false); });

  /* ---------- signup form (prototype: nothing is sent) ---------- */
  const form = document.getElementById('signup-form');
  const err = document.getElementById('form-error');
  const band = document.getElementById('signup-band');
  form.addEventListener('submit', (e) => {
    e.preventDefault();
    const fields = [...form.querySelectorAll('[required]')];
    let firstBad = null;
    fields.forEach((f) => {
      const ok = f.name === 'phone' ? f.value.replace(/\D/g, '').length >= 10 : f.value.trim() !== '';
      f.setAttribute('aria-invalid', String(!ok));
      if (!ok && !firstBad) firstBad = f;
    });
    if (firstBad) {
      err.textContent = firstBad.name === 'phone'
        ? 'Проверьте номер телефона: нужно минимум 10 цифр.'
        : 'Заполните все поля — так куратор подберёт удобное время.';
      firstBad.focus();
      return;
    }
    err.textContent = '';
    band.classList.add('is-done');
    document.getElementById('thanks').focus({ preventScroll: true });
    cheer(document.querySelector('.peeker'));
  });
  form.addEventListener('input', (e) => {
    if (e.target.getAttribute('aria-invalid') === 'true') e.target.removeAttribute('aria-invalid');
  });
})();
