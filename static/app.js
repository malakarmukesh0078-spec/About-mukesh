(function () {
  const $ = (s, r = document) => r.querySelector(s);
  const $$ = (s, r = document) => [...r.querySelectorAll(s)];
  const reduce = matchMedia('(prefers-reduced-motion: reduce)').matches;

  /* ---------- soft floating particles ---------- */
  const cv = $('#particles');
  if (cv && !reduce) {
    const ctx = cv.getContext('2d');
    let W, H;
    const color = getComputedStyle(document.documentElement).getPropertyValue('--primary').trim() || '#f5b83d';
    const resize = () => { W = cv.width = innerWidth; H = cv.height = innerHeight; };
    resize(); addEventListener('resize', resize);
    const pts = Array.from({ length: 38 }, () => ({ x: Math.random() * innerWidth, y: Math.random() * innerHeight, r: Math.random() * 1.6 + .4, vx: (Math.random() - .5) * .25, vy: -Math.random() * .35 - .08 }));
    (function loop() {
      ctx.clearRect(0, 0, W, H);
      ctx.fillStyle = color; ctx.globalAlpha = .45;
      for (const p of pts) {
        p.x += p.vx; p.y += p.vy;
        if (p.y < -4) { p.y = H + 4; p.x = Math.random() * W; }
        if (p.x < 0) p.x = W; if (p.x > W) p.x = 0;
        ctx.beginPath(); ctx.arc(p.x, p.y, p.r, 0, 6.283); ctx.fill();
      }
      requestAnimationFrame(loop);
    })();
  }

  /* ---------- typing roles ---------- */
  const typed = $('#typed');
  if (typed && !reduce) {
    const roles = (typed.dataset.roles || '').split('|').filter(Boolean);
    if (roles.length > 1) {
      let r = 0, c = 0, del = false;
      (function tick() {
        const w = roles[r];
        typed.textContent = w.slice(0, c);
        let wait = del ? 35 : 80;
        if (!del && c < w.length) c++;
        else if (!del) { del = true; wait = 1500; }
        else if (c > 0) c--;
        else { del = false; r = (r + 1) % roles.length; wait = 300; }
        setTimeout(tick, wait);
      })();
    }
  }

  /* ---------- count-up stats ---------- */
  $$('.count').forEach(el => {
    const m = el.dataset.val.match(/^(\d+)(.*)$/);
    if (!m || reduce) return;
    const end = +m[1], suf = m[2];
    const o = new IntersectionObserver(es => {
      if (!es[0].isIntersecting) return; o.disconnect();
      let n = 0; const step = Math.max(1, Math.ceil(end / 40));
      const t = setInterval(() => { n = Math.min(end, n + step); el.textContent = n + suf; if (n >= end) clearInterval(t); }, 30);
    }); o.observe(el);
  });

  /* ---------- portfolio filter ---------- */
  $$('.chip').forEach(b => b.addEventListener('click', () => {
    $$('.chip').forEach(x => x.classList.remove('active')); b.classList.add('active');
    $$('#pgrid .card').forEach(c => c.classList.toggle('hide', b.dataset.f !== 'all' && c.dataset.cat !== b.dataset.f));
  }));

  /* ---------- lightbox ---------- */
  const lb = $('#lb');
  if (lb) {
    const open = m => {
      $('img', lb).src = m.dataset.lightbox;
      $('figcaption b', lb).textContent = m.dataset.title || '';
      $('figcaption span', lb).textContent = m.dataset.desc || '';
      lb.classList.add('on');
    };
    const close = () => lb.classList.remove('on');
    $$('[data-lightbox]').forEach(m => {
      m.addEventListener('click', () => open(m));
      m.addEventListener('keydown', e => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); open(m); } });
    });
    lb.addEventListener('click', e => { if (e.target === lb || e.target.classList.contains('lb-close')) close(); });
    addEventListener('keydown', e => { if (e.key === 'Escape') close(); });
  }

  /* ---------- admin tabs ---------- */
  const tabs = $$('.tab');
  if (tabs.length) {
    const show = id => { tabs.forEach(t => t.classList.toggle('active', t.dataset.t === id)); $$('.pane').forEach(p => p.classList.toggle('active', p.id === id)); };
    tabs.forEach(t => t.addEventListener('click', () => { show(t.dataset.t); history.replaceState(null, '', '#' + t.dataset.t); }));
    const h = location.hash.slice(1); if (h && $('#' + h)) show(h);
  }

  /* ---------- Chhattisgarh map (illustrative, built from lon/lat) ---------- */
  const map = $('#cgmap');
  if (map) {
    const P = ([lo, la]) => [(lo - 80.0) * 95 + 20, (24.3 - la) * 72 + 22];
    const f = n => n.toFixed(1);
    const state = [[81.65,23.85],[82.1,24.05],[82.7,24.1],[83.3,24.05],[83.85,23.7],[84.25,23.2],[84.1,22.6],[83.95,22.0],[83.7,21.55],[83.35,21.15],[82.95,20.8],[82.55,20.35],[82.4,19.8],[82.3,19.2],[81.9,18.6],[81.5,18.1],[81.1,17.8],[80.7,18.0],[80.35,18.5],[80.3,19.3],[80.65,19.95],[80.95,20.6],[80.8,21.3],[80.85,21.95],[81.2,22.35],[81.45,22.95],[81.25,23.5]];
    const raigarh = [[83.0,22.35],[83.4,22.5],[83.75,22.25],[83.7,21.8],[83.35,21.5],[83.0,21.7]];
    const path = pts => 'M' + pts.map(p => P(p).map(f).join(',')).join('L') + 'Z';
    const NS = 'http://www.w3.org/2000/svg';
    const mk = (tag, attrs, text) => { const e = document.createElementNS(NS, tag); for (const k in attrs) e.setAttribute(k, attrs[k]); if (text) e.textContent = text; map.appendChild(e); return e; };

    mk('path', { class: 'state', d: path(state) });
    mk('path', { class: 'dist', d: path(raigarh) });

    const rg = P([83.4, 21.95]);
    const cities = [['Raipur', [81.63, 21.25], 12, 6], ['Bilaspur', [82.15, 22.08], -62, -8], ['Jagdalpur', [82.03, 19.07], 12, 4]];
    cities.forEach(([name, ll, dx, dy], i) => {
      const [x, y] = P(ll);
      const mx = (x + rg[0]) / 2, my = (y + rg[1]) / 2 - 22 - i * 6;
      mk('path', { class: 'route', d: `M${f(rg[0])},${f(rg[1])}Q${f(mx)},${f(my)} ${f(x)},${f(y)}` });
      mk('circle', { class: 'city', cx: f(x), cy: f(y), r: 3.2 });
      mk('text', { class: 'lbl', x: f(x + dx), y: f(y + dy) }, name);
    });

    mk('circle', { class: 'ring', cx: f(rg[0]), cy: f(rg[1]), r: 12 });
    mk('circle', { class: 'ring r2', cx: f(rg[0]), cy: f(rg[1]), r: 12 });
    mk('circle', { cx: f(rg[0]), cy: f(rg[1]), r: 5, fill: '#fff' });
    mk('text', { class: 'lbl main', x: f(rg[0] - 26), y: f(rg[1] + 50) }, 'Raigarh');
    mk('text', { class: 'head', x: 28, y: 44 }, 'Chhattisgarh');
  }
})();
