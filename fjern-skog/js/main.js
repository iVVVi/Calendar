/* Fjern skog — landing page behaviour */
(() => {
  'use strict';

  const $ = (sel, root = document) => root.querySelector(sel);
  const $$ = (sel, root = document) => [...root.querySelectorAll(sel)];
  const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  const coarse = window.matchMedia('(pointer: coarse)').matches;
  const clamp = (v, a, b) => Math.min(b, Math.max(a, v));

  const header = $('#header');
  const nav = $('#nav');
  const menuBtn = $('#menu-btn');

  /* ---------- Mobile menu ---------- */
  const setMenu = (open) => {
    menuBtn.setAttribute('aria-expanded', String(open));
    nav.classList.toggle('is-open', open);
  };
  menuBtn.addEventListener('click', () => setMenu(menuBtn.getAttribute('aria-expanded') !== 'true'));
  nav.addEventListener('click', (e) => { if (e.target.closest('a')) setMenu(false); });
  document.addEventListener('keydown', (e) => { if (e.key === 'Escape') setMenu(false); });

  /* ---------- Reveal on scroll ---------- */
  const revealEls = $$('.reveal');
  if ('IntersectionObserver' in window) {
    // Stagger siblings that enter together.
    revealEls.forEach((el) => {
      const siblings = [...el.parentElement.children].filter((c) => c.classList.contains('reveal'));
      el.style.setProperty('--d', `${Math.min(siblings.indexOf(el), 5) * 0.09}s`);
    });
    const io = new IntersectionObserver((entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) { entry.target.classList.add('is-in'); io.unobserve(entry.target); }
      });
    }, { threshold: 0.12, rootMargin: '0px 0px -6% 0px' });
    revealEls.forEach((el) => io.observe(el));
  } else {
    revealEls.forEach((el) => el.classList.add('is-in'));
  }

  /* ---------- Scroll: header, parallax, signal bars ---------- */
  const hero = $('#top');
  const layers = $$('.hero__scene .layer').map((el) => ({ el, speed: parseFloat(el.dataset.speed || '0') }));
  layers.forEach(({ el, speed }) => el.style.setProperty('--speed', speed));

  const signal = $('#signal');
  const signalBars = $$('.signal__bars i', signal);
  const signalLabel = $('#signal-label');
  const rules = $('#rules');
  let lastBars = -1;

  const setSignal = (bars) => {
    if (bars === lastBars) return;
    lastBars = bars;
    signalBars.forEach((bar, i) => bar.classList.toggle('is-off', i >= bars));
    signal.classList.toggle('is-off', bars === 0);
    signalLabel.textContent = bars === 0 ? 'No signal' : 'Signal';
    signal.setAttribute('aria-label', bars === 0 ? 'No signal' : `Signal strength: ${bars} of 4`);
  };

  let ticking = false;
  const onScroll = () => {
    const y = window.scrollY;
    header.classList.toggle('is-solid', y > 40);

    if (!reduceMotion && y < hero.offsetHeight * 1.1) {
      hero.style.setProperty('--p', y);
      layers.forEach(({ el }) => el.style.setProperty('--p', y));
    }

    // Signal drops to zero by the time the rules section arrives.
    const end = Math.max(1, rules.offsetTop - window.innerHeight * 0.55);
    setSignal(clamp(Math.round(4 * (1 - y / end)), 0, 4));
    ticking = false;
  };
  window.addEventListener('scroll', () => {
    if (!ticking) { ticking = true; requestAnimationFrame(onScroll); }
  }, { passive: true });
  window.addEventListener('resize', onScroll);
  onScroll();

  /* ---------- Night: flashlight ---------- */
  const night = $('#night');
  const hint = $('#night-hint');
  if (night) {
    if (reduceMotion) {
      night.classList.add('is-static');
    } else {
      let tx = 0.5, ty = 0.45, cx = 0.5, cy = 0.45; // target/current, in 0..1
      let visible = false, raf = 0, t0 = performance.now();

      const paint = () => {
        cx += (tx - cx) * 0.14;
        cy += (ty - cy) * 0.14;
        night.style.setProperty('--x', `${(cx * 100).toFixed(2)}%`);
        night.style.setProperty('--y', `${(cy * 100).toFixed(2)}%`);
      };
      const loop = (now) => {
        if (coarse) {
          // No cursor on touch screens: let the light wander on its own.
          const t = (now - t0) / 1000;
          tx = 0.5 + 0.34 * Math.sin(t * 0.55);
          ty = 0.45 + 0.22 * Math.sin(t * 0.83 + 1);
        }
        paint();
        raf = visible ? requestAnimationFrame(loop) : 0;
      };
      const start = () => { if (!raf) raf = requestAnimationFrame(loop); };

      new IntersectionObserver(([entry]) => {
        visible = entry.isIntersecting;
        if (visible) start();
      }, { threshold: 0.05 }).observe(night);

      night.addEventListener('pointermove', (e) => {
        const r = night.getBoundingClientRect();
        tx = clamp((e.clientX - r.left) / r.width, 0, 1);
        ty = clamp((e.clientY - r.top) / r.height, 0, 1);
        if (!coarse && hint) hint.style.opacity = '0';
      });
      if (coarse && hint) hint.textContent = 'Follow the flame.';
    }
  }

  /* ---------- Stock photos: swap in if the file exists ---------- */
  $$('[data-photo]').forEach((fig) => {
    const img = $('img', fig);
    const probe = new Image();
    probe.onload = () => { img.src = probe.src; };
    probe.src = fig.dataset.photo; // silently ignored when the file is missing
  });
})();
