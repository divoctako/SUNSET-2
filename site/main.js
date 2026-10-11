(() => {
  'use strict';

  const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)');
  const mobileMQ = window.matchMedia('(max-width: 767px)');
  const finePointer = window.matchMedia('(hover: hover) and (pointer: fine)');

  /* ---------- Reveal on scroll ---------- */
  const revealEls = document.querySelectorAll('[data-reveal]');
  if (reduceMotion.matches || !('IntersectionObserver' in window)) {
    revealEls.forEach(el => el.classList.add('in'));
  } else {
    const io = new IntersectionObserver(entries => {
      entries.forEach(e => {
        if (e.isIntersecting) {
          e.target.classList.add('in');
          io.unobserve(e.target);
        }
      });
    }, { threshold: 0.18, rootMargin: '0px 0px -4% 0px' });
    revealEls.forEach(el => io.observe(el));
    // Safety net: anything already on screen shows even if observer callbacks are delayed.
    setTimeout(() => {
      revealEls.forEach(el => {
        const r = el.getBoundingClientRect();
        if (r.top < window.innerHeight && r.bottom > 0) el.classList.add('in');
      });
    }, 400);
  }

  /* ---------- Mobile menu ---------- */
  const toggle = document.querySelector('.nav-toggle');
  const nav = document.getElementById('site-nav');
  const setMenu = open => {
    toggle.setAttribute('aria-expanded', String(open));
    nav.classList.toggle('open', open);
  };
  toggle.addEventListener('click', () => setMenu(toggle.getAttribute('aria-expanded') !== 'true'));
  nav.addEventListener('click', e => { if (e.target.closest('a')) setMenu(false); });
  document.addEventListener('keydown', e => {
    if (e.key === 'Escape' && nav.classList.contains('open')) {
      setMenu(false);
      toggle.focus();
    }
  });

  /* ---------- Active section in menu ---------- */
  const navLinks = [...nav.querySelectorAll('a')];
  const sections = navLinks.map(a => document.querySelector(a.getAttribute('href')));
  const markActive = () => {
    const line = window.innerHeight * 0.35;
    let current = null;
    sections.forEach((s, i) => { if (s.getBoundingClientRect().top <= line) current = i; });
    navLinks.forEach((a, i) => {
      if (i === current) a.setAttribute('aria-current', 'true');
      else a.removeAttribute('aria-current');
    });
  };

  /* ---------- Lightbox ---------- */
  const lb = document.getElementById('lightbox');
  const lbImg = lb.querySelector('.lb-img');
  let lastTrigger = null;
  document.querySelectorAll('.zoom').forEach(btn => {
    btn.addEventListener('click', () => {
      const img = btn.querySelector('img');
      lastTrigger = btn;
      lbImg.src = btn.dataset.full;
      lbImg.width = btn.dataset.w;
      lbImg.height = btn.dataset.h;
      lbImg.alt = img ? img.alt : '';
      document.body.classList.add('lb-open');
      lb.showModal();
    });
  });
  lb.querySelector('.lb-close').addEventListener('click', () => lb.close());
  lb.addEventListener('click', e => { if (e.target === lb) lb.close(); });
  lb.addEventListener('close', () => {
    document.body.classList.remove('lb-open');
    lbImg.removeAttribute('src');
    if (lastTrigger) lastTrigger.focus();
  });

  /* ---------- Package card tilt ---------- */
  document.querySelectorAll('.pkg-card').forEach(card => {
    const tilt = card.querySelector('.tilt');
    card.addEventListener('pointermove', e => {
      if (!finePointer.matches || reduceMotion.matches || e.pointerType !== 'mouse') return;
      const r = card.getBoundingClientRect();
      const x = (e.clientX - r.left) / r.width - 0.5;
      const y = (e.clientY - r.top) / r.height - 0.5;
      card.classList.add('tilting');
      tilt.style.setProperty('--ry', (x * 10).toFixed(2) + 'deg');
      tilt.style.setProperty('--rx', (-y * 8).toFixed(2) + 'deg');
    });
    card.addEventListener('pointerleave', () => {
      card.classList.remove('tilting');
      tilt.style.setProperty('--ry', '0deg');
      tilt.style.setProperty('--rx', '0deg');
    });
  });

  /* ---------- Falling ice cream ---------- */
  const layer = document.querySelector('.ic-layer');
  const ic = document.getElementById('icecream');
  const body = ic.querySelector('.ic-body');
  const path = layer.querySelector('.ic-path');
  const zoneEls = [...document.querySelectorAll('[data-zone]')];

  let zones = [];   // [{top, bottom}] in document coordinates (centre lane)
  let startY = 0;   // top of ice cream at the start of the path
  let endY = 0;     // top of ice cream at the landing spot
  let size = 0;     // rendered height of the ice cream
  let lastY = null;
  let lastDripY = 0;
  let landedArmed = true;
  let ticking = false;

  const docTop = el => el.getBoundingClientRect().top + window.scrollY;

  function measure() {
    size = ic.offsetHeight;
    zones = zoneEls.map(z => {
      const top = docTop(z);
      return { top, bottom: top + z.offsetHeight };
    });
    const first = zones[0];
    const last = zones[zones.length - 1];
    startY = (first.top + first.bottom) / 2 - size / 2;
    endY = last.bottom - size;
    path.style.top = (startY + size * 0.9) + 'px';
    path.style.height = Math.max(0, endY - startY) + 'px';
    lastY = null;
    update();
  }

  function spawnDrip(y) {
    const d = document.createElement('span');
    d.className = Math.random() < 0.5 ? 'drip' : 'drip o';
    d.style.left = `calc(50% + ${(Math.random() * 16 - 8).toFixed(1)}px)`;
    d.style.top = (y + size * 0.88) + 'px';
    d.addEventListener('animationend', () => d.remove());
    layer.appendChild(d);
  }

  const SPRINKLE_COLORS = ['#F6861A', '#FFFFFF', '#FFB566', '#A94700', '#FFD3A6'];
  function burst(y) {
    ic.classList.remove('landed');
    void ic.offsetWidth;
    ic.classList.add('landed');
    const n = 22;
    for (let i = 0; i < n; i++) {
      const s = document.createElement('span');
      s.className = 'sprinkle';
      const angle = Math.PI + (Math.PI * i) / (n - 1) + (Math.random() - 0.5) * 0.25;
      const dist = 50 + Math.random() * 70;
      s.style.left = '50%';
      s.style.top = (y + size * 0.55) + 'px';
      s.style.setProperty('--x', (Math.cos(angle) * dist).toFixed(1) + 'px');
      s.style.setProperty('--y', (Math.sin(angle) * dist * 0.8).toFixed(1) + 'px');
      s.style.setProperty('--r', Math.round(Math.random() * 540 - 270) + 'deg');
      s.style.setProperty('--c', SPRINKLE_COLORS[i % SPRINKLE_COLORS.length]);
      s.style.animationDelay = Math.round(Math.random() * 80) + 'ms';
      s.addEventListener('animationend', () => s.remove());
      layer.appendChild(s);
    }
  }

  function update() {
    ticking = false;
    const still = reduceMotion.matches;
    const vh = window.innerHeight;
    let y;
    let visible = true;

    if (still) {
      // Static: show in the hero until the landing spot is on screen, then sit there.
      y = window.scrollY + vh > endY + size ? endY : startY;
    } else {
      y = Math.min(endY, Math.max(startY, window.scrollY + vh * 0.42 - size / 2));
    }

    if (mobileMQ.matches) {
      // No centre lane on phones: only show inside the decorative gaps between blocks.
      visible = zones.some(z => y >= z.top - 4 && y + size <= z.bottom + 4);
    }

    const t = endY > startY ? (y - startY) / (endY - startY) : 0;
    const rot = still || y >= endY ? 0 : Math.sin(t * Math.PI * 9) * 8;
    ic.style.transform = `translate3d(0, ${y.toFixed(1)}px, 0)`;
    body.style.rotate = rot.toFixed(2) + 'deg';
    ic.style.opacity = visible ? '1' : '0';

    if (!still && lastY !== null) {
      if (y > lastY && y < endY && visible && y - lastDripY > 80) {
        spawnDrip(y);
        lastDripY = y;
      }
      if (y < lastDripY) lastDripY = y;
      if (y >= endY && lastY < endY && landedArmed) {
        burst(y);
        landedArmed = false;
      }
      if (y < endY - 60) landedArmed = true;
    }
    lastY = y;
  }

  const requestUpdate = () => {
    if (!ticking) {
      ticking = true;
      requestAnimationFrame(() => { update(); markActive(); });
    }
  };

  window.addEventListener('scroll', requestUpdate, { passive: true });
  window.addEventListener('resize', measure);
  [reduceMotion, mobileMQ].forEach(mq => mq.addEventListener('change', measure));
  if ('ResizeObserver' in window) {
    let rafId = 0;
    new ResizeObserver(() => {
      cancelAnimationFrame(rafId);
      rafId = requestAnimationFrame(measure);
    }).observe(document.querySelector('main'));
  }
  window.addEventListener('load', measure);
  if (document.fonts && document.fonts.ready) document.fonts.ready.then(measure);
  measure();
  markActive();
})();
