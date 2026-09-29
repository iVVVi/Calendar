/* Fjern skog — scene, scroll choreography, booking */
(() => {
'use strict';

const reduce = matchMedia('(prefers-reduced-motion: reduce)').matches;
const $ = (s, r = document) => r.querySelector(s);
const $$ = (s, r = document) => [...r.querySelectorAll(s)];
const clamp = (v, a = 0, b = 1) => Math.min(b, Math.max(a, v));

/* ------------------------------------------------------------------
   Photography — free-to-use Unsplash images (hot-linked).
   Swap any entry for your own file, e.g. house: 'img/house.jpg'.
   Entries that fail to load fall back to a quiet engraved placeholder.
------------------------------------------------------------------- */
const PHOTOS = {
  atmos:    'photo-1448375240586-882707db888b',
  house:    'photo-1513694203232-719a280e022f',
  houseB:   'photo-1481627834876-b7833e8f5570',
  orchard:  'photo-1416879595882-3373a0480b5b',
  orchardB: 'photo-1560806887-1e4cd0b6cbd6',
  bath:     'photo-1552321554-5fefe8c9ef14',
  sauna:    'photo-1540555700478-4be289fbecef',
  saunaB:   'photo-1441974231531-c6227db76b6e',
  fire:     'photo-1543007630-9710e4a00a20',
  books:    'photo-1495446815901-a7297e633e8d',
  ceramics: 'photo-1610701596007-11502861dcfa',
  candles:  'photo-1602523961358-f9f03dd557db',
  paintings:'photo-1541961017774-22349e4a1262',
  wood:     'photo-1541123437800-1bb1317badc2',
  objects:  'photo-1513519245088-0e12902e5a38'
};
const widths = [640, 960, 1400, 2000];
function photoAttrs(ref){
  if (!/^photo-/.test(ref)) return { src: ref };
  const u = w => `https://images.unsplash.com/${ref}?auto=format&fit=crop&w=${w}&q=65`;
  return { src: u(1400), srcset: widths.map(w => `${u(w)} ${w}w`).join(', ') };
}
function loadPhoto(img, key, sizes){
  const ref = PHOTOS[key]; if (!ref) return;
  const fig = img.closest('.plate, .fire__bg');
  const a = photoAttrs(ref);
  img.decoding = 'async'; img.loading = 'lazy';
  img.sizes = sizes;
  img.addEventListener('load', () => { img.classList.add('loaded'); fig && fig.classList.add('is-loaded'); });
  img.addEventListener('error', () => img.removeAttribute('src'));
  if (a.srcset) img.srcset = a.srcset;
  img.src = a.src;
}
$$('[data-photo]').forEach(el => {
  const img = $('img', el); if (!img) return;
  const wide = el.classList.contains('plate--bath') || el.classList.contains('fire__bg');
  loadPhoto(img, el.dataset.photo, wide ? '100vw' : '(min-width:960px) 50vw, 100vw');
});

/* ------------------------------------------------------------------
   Procedural hero scene (SVG): dusk sky, spruce forest, the house with
   lit windows, an overgrown orchard, and layered foreground boughs.
------------------------------------------------------------------- */
function rng(seed){ return () => { seed |= 0; seed = seed + 0x6D2B79F5 | 0; let t = Math.imul(seed ^ seed >>> 15, 1 | seed); t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t; return ((t ^ t >>> 14) >>> 0) / 4294967296; }; }
const f = n => n.toFixed(1);
const svg = (inner, extra = '') => `<svg viewBox="0 0 1600 900" preserveAspectRatio="xMidYMid slice" xmlns="http://www.w3.org/2000/svg" ${extra}>${inner}</svg>`;
const pick = (r, a) => a[Math.floor(r() * a.length)];

function spruce(r, x, base, h, w){
  const n = 6 + Math.floor(r() * 3), R = [], L = [];
  for (let i = 1; i <= n; i++){
    const t = i / n, y = base - h + h * t * .93, wi = w * .5 * (.22 + .78 * t) * (.85 + r() * .3), up = y - h / n * .32;
    R.push(`${f(x + wi)},${f(y)} ${f(x + wi * .34)},${f(up)}`);
    L.unshift(`${f(x - wi)},${f(y)} ${f(x - wi * .34)},${f(up)}`);
  }
  return `<polygon points="${f(x)},${f(base - h)} ${R.join(' ')} ${f(x + w * .03)},${f(base + 4)} ${f(x - w * .03)},${f(base + 4)} ${L.join(' ')}"/>`;
}

function skyLayer(){
  return svg(`
    <defs><filter id="sb" x="-10%" y="-10%" width="120%" height="120%"><feGaussianBlur stdDeviation="46"/></filter></defs>
    <rect width="1600" height="900" fill="#141f22"/>
    <g filter="url(#sb)">
      <rect x="-100" y="-100" width="1800" height="330" fill="#172529"/>
      <rect x="-100" y="220" width="1800" height="160" fill="#26363a"/>
      <rect x="-100" y="360" width="1800" height="120" fill="#4a5049"/>
      <rect x="-100" y="450" width="1800" height="90" fill="#7a6a4e"/>
      <ellipse cx="800" cy="520" rx="520" ry="60" fill="#8c7452" opacity=".55"/>
    </g>
    <rect y="560" width="1600" height="340" fill="#121d19"/>`);
}

function farForest(){
  const r = rng(11); let a = '', b = '';
  for (let x = -40; x < 1680; x += 34 + r() * 34) a += spruce(r, x, 620 + r() * 20, 170 + r() * 150, 80 + r() * 60);
  for (let x = -60; x < 1680; x += 46 + r() * 46) b += spruce(r, x, 660, 220 + r() * 190, 110 + r() * 70);
  return svg(`<g fill="#213230">${a}</g><rect y="600" width="1600" height="300" fill="#1a2926"/><g fill="#15231e">${b}</g><rect y="650" width="1600" height="250" fill="#111c17"/>`);
}

/* house geometry shared by the silhouette and glow layers */
const WIN = [
  // x, y, w, h, lit
  [652,478,34,50,1],[732,478,34,50,0],[834,478,34,50,1],[914,478,34,50,0],
  [652,568,34,58,0],[732,568,34,58,1],[834,568,34,58,1],[914,568,34,58,1],
  [543,566,30,48,1],[1027,566,30,48,0],
  [742,392,26,30,1],[832,392,26,30,0]
];
function houseLayer(){
  const r = rng(5);
  let s = `<defs><filter id="hb"><feGaussianBlur stdDeviation="1.2"/></filter></defs>`;
  s += `<path d="M-50 700 Q400 650 800 664 T1650 690 V900 H-50Z" fill="#0f1a14"/>`;
  // back orchard
  [[380,668,.85],[470,660,.8],[1130,662,.8],[1235,670,.9],[300,676,1]].forEach(([x,b,sc])=>s+=appleTree(r,x,b,sc,'#132018'));
  // wings & main body
  s += `<rect x="500" y="520" width="130" height="146" fill="#27302b"/>
        <polygon points="486,524 520,470 610,470 640,524" fill="#151b18"/>
        <rect x="970" y="540" width="120" height="126" fill="#252d29"/>
        <polygon points="960,544 990,500 1075,500 1100,544" fill="#151b18"/>
        <rect x="620" y="440" width="360" height="226" fill="#2c352f"/>
        <polygon points="592,448 668,352 932,352 1008,448" fill="#151b18"/>
        <polygon points="668,352 932,352 936,358 664,358" fill="#2b332e"/>
        <rect x="686" y="316" width="28" height="50" fill="#1d2420"/><rect x="886" y="316" width="28" height="50" fill="#1d2420"/>
        <polygon points="736,392 764,392 750,368" fill="#151b18" opacity="0"/>
        <rect x="620" y="440" width="360" height="6" fill="#1a211d"/>
        <rect x="620" y="536" width="360" height="4" fill="#1e2621" opacity=".8"/>
        <rect x="620" y="660" width="360" height="10" fill="#1b221e"/>`;
  // dormers
  s += `<polygon points="734,396 766,396 750,372" fill="#1a211d"/><polygon points="824,396 856,396 840,372" fill="#1a211d"/>`;
  // stone texture
  for (let i = 0; i < 90; i++){ const x = 620 + r() * 360, y = 446 + r() * 210; s += `<rect x="${f(x)}" y="${f(y)}" width="${f(8 + r() * 16)}" height="3" fill="#000" opacity="${f(.05 + r() * .09)}"/>`; }
  // windows (unlit + frame)
  WIN.forEach(([x,y,w,h,lit]) => {
    s += `<rect x="${x-3}" y="${y-3}" width="${w+6}" height="${h+6}" fill="#1b221e"/>`;
    s += `<rect x="${x}" y="${y}" width="${w}" height="${h}" fill="${lit ? '#a87d43' : '#1c2a2f'}"/>`;
    s += `<path d="M${x+w/2} ${y}V${y+h}M${x} ${y+h*.42}H${x+w}" stroke="#0d1310" stroke-width="2.4"/>`;
  });
  // door
  s += `<path d="M778 666V606a22 22 0 0 1 44 0V666Z" fill="#171d19"/><path d="M782 666V608a18 18 0 0 1 36 0V666Z" fill="#b98c4e"/><path d="M800 590V666M782 618H818" stroke="#0d1310" stroke-width="2"/>`;
  // ivy creeping up the facade
  for (let i = 0; i < 40; i++){ const x = 620 + r() * 60, y = 460 + r() * 200; s += `<circle cx="${f(x)}" cy="${f(y)}" r="${f(4 + r() * 9)}" fill="#142219" opacity=".8"/>`; }
  for (let i = 0; i < 40; i++){ const x = 930 + r() * 60, y = 480 + r() * 180; s += `<circle cx="${f(x)}" cy="${f(y)}" r="${f(4 + r() * 9)}" fill="#142219" opacity=".8"/>`; }
  // front orchard
  [[590,716,.95],[1010,712,1],[150,740,1.5],[1470,736,1.45],[760,760,.9]].forEach(([x,b,sc],i)=>{ if(i<4) s += appleTree(r,x,b,sc,'#0f1b14'); });
  // fallen fruit
  for (let i = 0; i < 46; i++){ const x = 120 + r() * 1360, y = 730 + r() * 150; s += `<circle cx="${f(x)}" cy="${f(y)}" r="${f(2.2 + r() * 2.4)}" fill="${pick(r,['#6f4526','#7d5a2a','#5a3524'])}" opacity=".85"/>`; }
  return svg(s);
}
function appleTree(r, x, base, sc, col){
  let s = `<g fill="${col}" stroke="${col}">`;
  const th = 120 * sc;
  s += `<path d="M${f(x-9*sc)},${f(base)} C${f(x-6*sc)},${f(base-th*.5)} ${f(x-24*sc)},${f(base-th*.8)} ${f(x-38*sc)},${f(base-th*1.15)} L${f(x-30*sc)},${f(base-th*1.2)} C${f(x-12*sc)},${f(base-th*.95)} ${f(x+4*sc)},${f(base-th*.85)} ${f(x+8*sc)},${f(base-th*.5)} C${f(x+8*sc)},${f(base-th*.3)} ${f(x+12*sc)},${f(base-8*sc)} ${f(x+12*sc)},${f(base)}Z" stroke="none"/>`;
  const n = 11 + Math.floor(r() * 5);
  for (let i = 0; i < n; i++){
    const a = r() * Math.PI * 2, d = r() * 62 * sc, cx = x + Math.cos(a) * d * 1.35, cy = base - th * 1.18 + Math.sin(a) * d * .8, rr = (24 + r() * 32) * sc;
    s += `<circle cx="${f(cx)}" cy="${f(cy)}" r="${f(rr)}" stroke="none" opacity="${f(.9 + r() * .1)}"/>`;
  }
  s += '</g>';
  for (let i = 0; i < 7; i++){ const a = r() * Math.PI * 2, d = 20 + r() * 60; s += `<circle cx="${f(x + Math.cos(a) * d * sc * 1.3)}" cy="${f(base - th * 1.1 + Math.sin(a) * d * sc * .7)}" r="${f(2.2 * sc)}" fill="#7d4a2a" opacity=".7"/>`; }
  return s;
}

function glowLayer(){
  let halo = '', core = '';
  WIN.forEach(([x,y,w,h,lit]) => {
    if (!lit) return;
    halo += `<rect x="${x-14}" y="${y-12}" width="${w+28}" height="${h+26}" fill="#e2a95a"/>`;
    core += `<rect x="${x}" y="${y}" width="${w}" height="${h}" fill="#f1c980"/><path d="M${x+w/2} ${y}V${y+h}M${x} ${y+h*.42}H${x+w}" stroke="#2a1d10" stroke-width="2.4"/>`;
  });
  return svg(`
    <defs><filter id="g1" x="-30%" y="-30%" width="160%" height="160%"><feGaussianBlur stdDeviation="20"/></filter>
    <filter id="g2" x="-30%" y="-30%" width="160%" height="160%"><feGaussianBlur stdDeviation="6"/></filter></defs>
    <ellipse cx="800" cy="676" rx="220" ry="22" fill="#c8975a" opacity=".22" filter="url(#g1)"/>
    <g filter="url(#g1)" opacity=".5">${halo}<ellipse cx="800" cy="630" rx="40" ry="60" fill="#e2a95a"/></g>
    <g filter="url(#g2)" opacity=".6">${halo}</g>
    <g>${core}</g>
    <path d="M782 666V608a18 18 0 0 1 36 0V666Z" fill="#f1c980"/><path d="M800 590V666M782 618H818" stroke="#2a1d10" stroke-width="2"/>`);
}

function trunk(r, x, w, col, top = -20){
  let d = `M${f(x - w/2)},${top}`;
  for (let y = top; y <= 920; y += 60) d += ` L${f(x - w/2 - (y/900) * 6 + (r() - .5) * 6)},${y}`;
  for (let y = 920; y >= top; y -= 60) d += ` L${f(x + w/2 + (y/900) * 6 + (r() - .5) * 6)},${y}`;
  let s = `<path d="${d}Z" fill="${col}"/>`;
  for (let i = 0; i < 26; i++){ const yy = r() * 880, xx = x - w/2 + r() * w; s += `<path d="M${f(xx)} ${f(yy)}v${f(30 + r() * 90)}" stroke="#000" stroke-opacity="${f(.15 + r() * .25)}" stroke-width="${f(1 + r() * 2.2)}"/>`; }
  return s;
}
function midTrees(){
  const r = rng(21);
  let s = `<g opacity=".9">`;
  s += trunk(r, 468, 16, '#0d1611') + trunk(r, 1120, 14, '#0d1611') + trunk(r, 380, 10, '#101a14');
  s += trunk(r, 260, 62, '#09100c') + trunk(r, 1355, 74, '#09100c') + trunk(r, 90, 120, '#070c09') + trunk(r, 1520, 130, '#070c09');
  s += '</g>';
  return svg(s);
}

const LEAF_SYMBOLS = `<svg width="0" height="0" style="position:absolute" aria-hidden="true"><defs>
  <path id="lf0" d="M0,0 C6,-9 20,-11 34,0 C20,11 6,9 0,0Z"/>
  <path id="lf1" d="M0,0 C4,-10 16,-14 26,-2 C30,4 18,12 0,0Z"/>
  <path id="lf2" d="M0,0 C4,-6 8,-12 14,-8 C16,-14 24,-14 26,-8 C32,-8 34,-2 32,2 C34,8 28,12 22,8 C18,14 10,12 10,6 C4,8 0,4 0,0Z"/>
</defs></svg>`;
const LEAF_COLS = ['#060b08','#080f0a','#0b140e','#0e1a11','#12201a','#0a110c','#16241a','#0d150f','#3f3520'];

function boughs(r, cfg){
  const out = { paths: '', leaves: '' };
  const grow = (x, y, ang, len, w, depth) => {
    const segs = 6; let px = x, py = y, a = ang, d = `M${f(px)},${f(py)}`; const pts = [];
    for (let i = 0; i < segs; i++){
      a += (r() - .5) * cfg.wob + cfg.droop;
      px += Math.cos(a) * len / segs; py += Math.sin(a) * len / segs;
      d += ` L${f(px)},${f(py)}`; pts.push([px, py, a]);
      if (depth > 0 && i >= 1 && r() < .65) grow(px, py, a + (r() < .5 ? -1 : 1) * (.4 + r() * .7), len * (.42 + r() * .25), w * .6, depth - 1);
    }
    out.paths += `<path d="${d}" stroke-width="${f(Math.max(1.2, w))}"/>`;
    if (depth <= cfg.leafDepth) pts.forEach(([lx, ly, la]) => {
      const k = cfg.leaves + Math.floor(r() * 3);
      for (let j = 0; j < k; j++){
        const ang2 = la * 57.3 + (r() - .5) * 200, sc = cfg.size * (.6 + r() * .9);
        out.leaves += `<use href="#lf${Math.floor(r() * 3)}" transform="translate(${f(lx + (r() - .5) * 46)} ${f(ly + (r() - .5) * 46)}) rotate(${f(ang2)}) scale(${f(sc)})" fill="${pick(r, LEAF_COLS)}"/>`;
      }
    });
  };
  cfg.roots.forEach(([x, y, a, l, w]) => grow(x, y, a, l, w, cfg.depth));
  return `<g fill="none" stroke="#060a07" stroke-linecap="round" stroke-linejoin="round">${out.paths}</g><g>${out.leaves}</g>`;
}
function fgSide(seed, mirror){
  const r = rng(seed), roots = [];
  for (let i = 0; i < 6; i++) roots.push([20, 40 + i * 140 + r() * 60, -.2 + r() * .4 + (i > 3 ? .12 : 0), 420 + r() * 200, 13 - i * .6]);
  const inner = boughs(r, { roots, depth: 2, wob: .5, droop: .04, leafDepth: 1, leaves: 1, size: 1.05 });
  return svg(mirror ? `<g transform="translate(1600 0) scale(-1 1)">${inner}</g>` : inner);
}
function fgTop(){
  const r = rng(77), roots = [];
  for (let i = 0; i < 8; i++) roots.push([-40 + i * 230 + r() * 90, -110, 1.57 + (r() - .5) * .7, 300 + r() * 200, 12]);
  return svg(boughs(r, { roots, depth: 2, wob: .45, droop: .0, leafDepth: 1, leaves: 1, size: 1.05 }));
}
function fgGrass(){
  const r = rng(91); let s = '';
  for (let i = 0; i < 520; i++){
    const x = -40 + r() * 1680, h = 60 + r() * 240 * (.35 + .65 * Math.abs(Math.sin(x / 210))), lean = (r() - .5) * 90;
    s += `<path d="M${f(x)} 910 Q${f(x + lean * .3)} ${f(910 - h * .6)} ${f(x + lean)} ${f(910 - h)}" stroke="${pick(r, ['#070d09','#0b140e','#121f14','#1a2a1a','#3a3a22','#26301c'])}" stroke-width="${f(1.4 + r() * 2.6)}" fill="none" stroke-linecap="round"/>`;
  }
  for (let i = 0; i < 26; i++){ const x = r() * 1600, h = 100 + r() * 200; s += `<ellipse cx="${f(x)}" cy="${f(910 - h)}" rx="3" ry="9" fill="#2b2a1a" transform="rotate(${f((r()-.5)*30)} ${f(x)} ${f(910-h)})"/>`; }
  return svg(`<rect y="880" width="1600" height="60" fill="#060a07"/>${s}`);
}
function mist(seed, freq, alpha, tone){
  const id = 'm' + seed;
  return svg(`<filter id="${id}" x="0" y="0" width="100%" height="100%"><feTurbulence type="fractalNoise" baseFrequency="${freq}" numOctaves="4" seed="${seed}"/>
    <feColorMatrix type="matrix" values="0 0 0 0 ${tone[0]}  0 0 0 0 ${tone[1]}  0 0 0 0 ${tone[2]}  0 0 0 ${alpha} ${-alpha * .3}"/></filter>
    <rect width="1600" height="900" filter="url(#${id})"/>`, 'preserveAspectRatio="none"').replace('xMidYMid slice', 'none');
}

/* build & mount */
const scene = $('#scene');
const layerDefs = [
  ['sky',    skyLayer(),                       '',            0],
  ['photo',  '<img alt="" decoding="async">',  'layer--photo', 0],
  ['far',    farForest(),                      '',            0],
  ['mistB',  `<div class="mist-drift">${mist(4,'0.0032 0.012',1.7,[.45,.52,.5])}</div>`, 'layer--mist', 0],
  ['house',  houseLayer(),                     '',            0],
  ['shade',  '<div style="position:absolute;inset:0;background:#070d09"></div>', '', 0],
  ['glow',   glowLayer(),                      '',            0],
  ['mid',    midTrees(),                       '',            0],
  ['mistF',  `<div class="mist-drift" style="animation-duration:95s;animation-direction:alternate-reverse">${mist(9,'0.0026 0.009',1.9,[.5,.57,.54])}</div>`, 'layer--mist', 0],
  ['fgL',    fgSide(31, false),                'layer--blur', 0],
  ['fgR',    fgSide(47, true),                 'layer--blur', 0],
  ['fgT',    fgTop(),                          'layer--blur', 0],
  ['fgG',    fgGrass(),                        '',            0]
];
scene.insertAdjacentHTML('beforebegin', LEAF_SYMBOLS);
const L = {};
layerDefs.forEach(([k, html, cls]) => {
  const d = document.createElement('div');
  d.className = 'layer ' + cls; d.innerHTML = html; scene.appendChild(d); L[k] = d;
});
loadPhoto($('img', L.photo), 'atmos', '100vw');
L.shade.style.opacity = 0;

/* ------------------------------------------------------------------
   Scroll choreography
------------------------------------------------------------------- */
const hero = $('#top'), stage = $('#stage'), heroText = $('#heroText'), hCurtain = $('#heroCurtain'), nav = $('#nav');
let vw = innerWidth, vh = innerHeight, heroSpan = 1;
let target = scrollY, cur = scrollY, p = 0, raf = 0;
const plates = new Set();

function measure(){ vw = innerWidth; vh = innerHeight; heroSpan = Math.max(1, hero.offsetHeight - vh); }
const ease = t => t * t * (3 - 2 * t);

function heroFrame(p){
  const e = ease(p), W = vw, H = vh;
  const t = (k, x, y, s = 1) => { L[k].style.transform = `translate3d(${f(x)}px,${f(y)}px,0) scale(${f(s)})`; };
  t('sky', 0, -p * H * .02);
  t('photo', 0, -p * H * .03, 1 + p * .04);
  t('far', 0, -p * H * .05, 1 + p * .05);
  t('house', 0, H * .06 - p * H * .09, 1 + p * .1);
  t('shade', 0, 0); L.shade.style.opacity = f(clamp(e * .62, 0, .62));
  t('glow', 0, H * .06 - p * H * .09, 1 + p * .1);
  t('mid', -0 , -p * H * .16, 1 + p * .2);
  L.mistB.style.opacity = f(.25 + e * .5); t('mistB', 0, H * .06 - p * H * .1);
  L.mistF.style.opacity = f(.12 + e * .6);  t('mistF', 0, H * .12 - p * H * .2);
  // boughs slide in from the edges and cover the house
  t('fgL', -W * .62 * (1 - e), -p * H * .1, 1 + p * .12);
  t('fgR',  W * .62 * (1 - e), -p * H * .1, 1 + p * .12);
  t('fgT', 0, -H * .42 * (1 - e) - p * H * .04, 1 + p * .1);
  t('fgG', 0, H * .2 * (1 - e) - p * H * .1, 1 + p * .06);
  L.fgL.style.transformOrigin = 'left center'; L.fgR.style.transformOrigin = 'right center';
  // copy
  const fade = clamp(1 - p * 2.6);
  heroText.style.opacity = f(fade);
  heroText.style.transform = `translate3d(0,${f(-p * H * .12)}px,0)`;
  heroText.style.pointerEvents = fade < .25 ? 'none' : '';
  hCurtain.style.opacity = f(clamp((p - .86) / .14) ** 1.4);
}

function tick(){
  raf = 0;
  cur += (target - cur) * (reduce ? 1 : .085);
  if (Math.abs(target - cur) < .2) cur = target;
  p = clamp(cur / heroSpan);
  if (!reduce || !tick.once){ heroFrame(reduce ? .38 : p); tick.once = true; }
  // parallax inside photographs
  plates.forEach(el => {
    const b = el.getBoundingClientRect();
    if (b.bottom < -100 || b.top > vh + 100) return;
    const rel = ((b.top + b.height / 2) - vh / 2) / (vh / 2 + b.height / 2);
    const par = $('.plate__par', el);
    if (par && !reduce) par.style.transform = `translate3d(0,${f(-rel * b.height * .075)}px,0)`;
  });
  if (cur !== target) raf = requestAnimationFrame(tick);
}
function kick(){ if (!raf) raf = requestAnimationFrame(tick); }
addEventListener('scroll', () => { target = scrollY; nav.classList.toggle('is-solid', scrollY > 40); kick(); }, { passive: true });
addEventListener('resize', () => { measure(); kick(); });
measure(); nav.classList.toggle('is-solid', scrollY > 40); cur = target = scrollY; tick();

/* reveals + plate tracking */
const io = new IntersectionObserver(es => es.forEach(en => {
  if (en.isIntersecting){ en.target.classList.add('in'); if (!en.target.classList.contains('plate')) io.unobserve(en.target); }
  if (en.target.classList.contains('plate')) en.isIntersecting ? plates.add(en.target) : plates.delete(en.target);
}), { threshold: .12, rootMargin: '0px 0px -6% 0px' });
$$('.reveal, .plate').forEach(el => io.observe(el));
const fireBg = $('.fire__bg'); if (fireBg) { fireBg.classList.add('plate'); new IntersectionObserver(es => es.forEach(en => en.isIntersecting ? plates.add(fireBg) : plates.delete(fireBg))).observe(fireBg); }
requestAnimationFrame(() => document.documentElement.classList.add('ready'));

/* anchor scrolling — slow, cinematic easing */
let anim = 0;
function glideTo(y){
  cancelAnimationFrame(anim);
  if (reduce){ scrollTo(0, y); return; }
  const start = scrollY, dist = y - start, dur = clamp(900 + Math.abs(dist) * .32, 1100, 2800), t0 = performance.now();
  const stop = () => cancelAnimationFrame(anim);
  addEventListener('wheel', stop, { once: true, passive: true }); addEventListener('touchstart', stop, { once: true, passive: true });
  const step = now => { const k = clamp((now - t0) / dur); scrollTo(0, start + dist * (k < .5 ? 4 * k ** 3 : 1 - (-2 * k + 2) ** 3 / 2)); if (k < 1) anim = requestAnimationFrame(step); };
  anim = requestAnimationFrame(step);
}
document.addEventListener('click', e => {
  const a = e.target.closest('a[href^="#"]'); if (!a) return;
  const id = a.getAttribute('href'), el = id === '#top' ? null : $(id);
  if (id !== '#top' && !el) return;
  e.preventDefault();
  closeMenu();
  const y = id === '#top' ? 0 : el.getBoundingClientRect().top + scrollY - (id === '#house' ? 0 : 0);
  setTimeout(() => glideTo(y), document.documentElement.classList.contains('menu-open') ? 0 : 0);
  history.replaceState(null, '', id);
});

/* mobile menu */
const burger = $('#burger'), menu = $('#menu'), root = document.documentElement;
function setMenu(open){
  root.classList.toggle('menu-open', open);
  burger.setAttribute('aria-expanded', open); burger.setAttribute('aria-label', open ? 'Close menu' : 'Open menu');
  menu.setAttribute('aria-hidden', !open);
  if (open) setTimeout(() => $('a', menu).focus({ preventScroll: true }), 300);
}
function closeMenu(){ if (root.classList.contains('menu-open')) setMenu(false); }
burger.addEventListener('click', () => setMenu(!root.classList.contains('menu-open')));
addEventListener('keydown', e => { if (e.key === 'Escape') { closeMenu(); } });
matchMedia('(min-width:980px)').addEventListener('change', e => e.matches && closeMenu());

/* ------------------------------------------------------------------
   Booking
------------------------------------------------------------------- */
const ROOMS = {
  house: { name: 'The Whole House', cap: 6, rate: 540, salt: 1 },
  upper: { name: 'The Upper Rooms', cap: 3, rate: 290, salt: 4 },
  lodge: { name: 'The Orchard Lodge', cap: 2, rate: 210, salt: 7 }
};
const form = $('#book'), arr = $('#arrival'), dep = $('#departure'), gOut = $('#guests');
const av = $('#avail'), avText = $('span', av), useNext = $('#useNext');
const fmt = d => new Intl.DateTimeFormat('en-GB', { weekday: 'short', day: 'numeric', month: 'short', year: 'numeric' }).format(d);
const fmtS = d => new Intl.DateTimeFormat('en-GB', { weekday: 'short', day: 'numeric', month: 'short' }).format(d);
const iso = d => `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`;
const parse = s => { const [y, m, d] = s.split('-').map(Number); return new Date(y, m - 1, d); };
const addDays = (d, n) => { const x = new Date(d); x.setDate(x.getDate() + n); return x; };
const dayIdx = d => Math.floor(Date.UTC(d.getFullYear(), d.getMonth(), d.getDate()) / 864e5);
// Demo availability: deterministic pseudo-bookings. Replace with a real calendar/API.
const blocked = (d, room) => { const k = Math.floor(dayIdx(d) / 4) + ROOMS[room].salt * 97; return ((Math.imul(k, 2654435761) >>> 0) % 10) < 3; };
const free = (a, n, room) => { for (let i = 0; i < n; i++) if (blocked(addDays(a, i), room)) return false; return true; };

let guests = 2, nextRange = null;
const room = () => $('input[name=room]:checked', form).value;
const today = new Date(); today.setHours(0, 0, 0, 0);
arr.min = iso(addDays(today, 1)); dep.min = iso(addDays(today, 3));

function setStatus(state, msg){ av.dataset.state = state; avText.textContent = msg; }
function update(){
  const R = ROOMS[room()];
  guests = clamp(guests, 1, R.cap);
  gOut.textContent = guests; $('#gMinus').disabled = guests <= 1; $('#gPlus').disabled = guests >= R.cap;
  $('#sGuests').textContent = guests; $('#sRoom').textContent = R.name;
  useNext.hidden = true; nextRange = null;
  let a = arr.value && parse(arr.value), d = dep.value && parse(dep.value), nights = 0;
  if (a) dep.min = iso(addDays(a, 2));
  $('#sArr').textContent = a ? fmtS(a) : '—'; $('#sDep').textContent = d ? fmtS(d) : '—';
  if (!a || !d){ setStatus('idle', 'Choose your dates to see availability.'); $('#sNights').textContent = '—'; $('#sTotal').textContent = '—'; return false; }
  nights = Math.round((d - a) / 864e5);
  $('#sNights').textContent = nights > 0 ? nights : '—';
  if (nights <= 0){ setStatus('bad', 'Departure must come after arrival.'); $('#sTotal').textContent = '—'; return false; }
  if (nights < 2){ setStatus('bad', 'We ask for a minimum stay of two nights.'); $('#sTotal').textContent = '—'; return false; }
  $('#sTotal').textContent = '€' + (nights * R.rate).toLocaleString('en-GB');
  if (free(a, nights, room())){ setStatus('ok', `Available — ${R.name} is yours for ${nights} nights.`); return true; }
  for (let i = 1; i <= 240; i++){ const s = addDays(a, i); if (free(s, nights, room())){ nextRange = [s, addDays(s, nights)]; break; } }
  setStatus('no', nextRange ? `Not available for these nights. Nearest opening: ${fmtS(nextRange[0])} – ${fmtS(nextRange[1])}.` : 'Not available for these nights.');
  useNext.hidden = !nextRange;
  return false;
}
useNext.addEventListener('click', () => { if (!nextRange) return; arr.value = iso(nextRange[0]); dep.value = iso(nextRange[1]); update(); });
arr.addEventListener('change', () => { if (arr.value && (!dep.value || parse(dep.value) <= parse(arr.value))) dep.value = iso(addDays(parse(arr.value), 3)); update(); });
[dep, ...$$('input[name=room]', form)].forEach(el => el.addEventListener('change', update));
$('#gMinus').addEventListener('click', () => { guests--; update(); });
$('#gPlus').addEventListener('click', () => { guests++; update(); });

form.addEventListener('submit', e => {
  e.preventDefault();
  const ok = update();
  const bad = [arr, dep, $('#name'), $('#email')].filter(el => !el.value.trim() || (el.type === 'email' && !el.checkValidity()));
  $$('.field.invalid', form).forEach(x => x.classList.remove('invalid'));
  bad.forEach(el => el.closest('.field').classList.add('invalid'));
  if (bad.length){ bad[0].focus(); setStatus(av.dataset.state === 'idle' ? 'bad' : av.dataset.state, bad.some(b => b === arr || b === dep) ? 'Please choose your arrival and departure dates.' : 'Please tell us your name and email so we can reply.'); return; }
  if (!ok){ arr.focus(); return; }
  const R = ROOMS[room()], a = parse(arr.value), d = parse(dep.value), n = Math.round((d - a) / 864e5);
  const body = `Dear Fjern skog,\n\nI would like to request a stay.\n\nArrival: ${fmt(a)}\nDeparture: ${fmt(d)} (${n} nights)\nGuests: ${guests}\nAccommodation: ${R.name}\n\n${$('#note').value.trim()}\n\nWith thanks,\n${$('#name').value.trim()}\n${$('#email').value.trim()}`;
  $('#mailLink').href = `mailto:letters@fjernskog.example?subject=${encodeURIComponent('Stay request — ' + R.name)}&body=${encodeURIComponent(body)}`;
  $('#letterText').textContent = `${R.name}, ${fmtS(a)} to ${fmtS(d)}, for ${guests} ${guests === 1 ? 'guest' : 'guests'}. Send it and we will write back within two days.`;
  form.classList.add('is-sent'); $('#letter').hidden = false; $('#letter').focus({ preventScroll: true });
  glideTo($('#book').getBoundingClientRect().top + scrollY - 120);
});
$('#editReq').addEventListener('click', () => { form.classList.remove('is-sent'); $('#letter').hidden = true; arr.focus(); });
update();
})();
