#!/usr/bin/env python3
"""Generates the SVG illustrations in assets/illustrations (deterministic, no dependencies)."""
import math
import os
import random

OUT = os.path.join(os.path.dirname(__file__), "..", "assets", "illustrations")
os.makedirs(OUT, exist_ok=True)


def save(name, svg):
    with open(os.path.join(OUT, name), "w", encoding="utf-8") as f:
        f.write(svg)


def svg(w, h, body, defs="", par="xMidYMid slice"):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" '
            f'preserveAspectRatio="{par}"><defs>{defs}</defs>{body}</svg>')


def pine(x, base, h, w, fill, tiers=5):
    top = base - h
    right = []
    for i in range(tiers):
        frac = (i + 1) / tiers
        y = top + h * 0.92 * frac
        half = w / 2 * (0.3 + 0.7 * frac)
        right.append((x + half, y))
        if i < tiers - 1:
            right.append((x + half * 0.42, y - h * 0.07))
    pts = [(x, top)] + right + [(x + w * 0.05, top + h * 0.92), (x + w * 0.05, base),
                                (x - w * 0.05, base), (x - w * 0.05, top + h * 0.92)]
    for px, py in reversed(right):
        pts.append((2 * x - px, py))
    d = "M" + " L".join(f"{px:.1f},{py:.1f}" for px, py in pts) + "Z"
    return f'<path d="{d}" fill="{fill}"/>'


def ridge_fn(base, amp, phase):
    return lambda x: base + amp * math.sin(x / 210 + phase) + amp * 0.5 * math.sin(x / 83 + phase * 2)


def layer(seed, ridge, fill, count, hmin, hmax, w=1600, h=600, extra="", gap=None, keep=None):
    rnd = random.Random(seed)
    body = []
    pts = [f"{x},{ridge(x):.1f}" for x in range(0, w + 40, 40)]
    body.append(f'<path d="M0,{h} L{" L".join(pts)} L{w},{h}Z" fill="{fill}"/>')
    xs = sorted(rnd.uniform(-20, w + 20) for _ in range(count))
    for x in xs:
        if keep and not keep(x):
            continue
        th = rnd.uniform(hmin, hmax)
        body.append(pine(x, ridge(x) + 14, th, th * rnd.uniform(0.34, 0.46), fill))
    body.append(extra)
    return "".join(body)


def cabin(x, y, s=1.0, wood="#7a4f34", roof="#22292a", glow="#f2a65a", smoke=True):
    """A small lit cabin whose ground line is at y."""
    g = [f'<g transform="translate({x},{y}) scale({s})">']
    if smoke:
        g.append('<path d="M86,-118 C70,-150 104,-170 88,-205 C80,-225 96,-240 92,-262" '
                 'fill="none" stroke="#dfe5dc" stroke-opacity=".28" stroke-width="9" stroke-linecap="round"/>')
    g.append(f'<rect x="74" y="-128" width="24" height="46" fill="#3a3f3c"/>')
    g.append(f'<rect x="0" y="-84" width="200" height="84" fill="{wood}"/>')
    for i in range(1, 6):
        g.append(f'<rect x="0" y="{-84 + i * 14}" width="200" height="1.6" fill="#000" fill-opacity=".22"/>')
    g.append(f'<polygon points="-16,-80 100,-142 216,-80" fill="{roof}"/>')
    g.append(f'<polygon points="-16,-80 100,-142 100,-136 -8,-80" fill="#fff" fill-opacity=".08"/>')
    g.append(f'<rect x="22" y="-64" width="46" height="34" rx="2" fill="{glow}"/>'
             f'<rect x="44" y="-64" width="2" height="34" fill="#2b1c12"/><rect x="22" y="-48" width="46" height="2" fill="#2b1c12"/>')
    g.append(f'<rect x="138" y="-64" width="40" height="34" rx="2" fill="{glow}"/>'
             f'<rect x="157" y="-64" width="2" height="34" fill="#2b1c12"/>')
    g.append(f'<rect x="96" y="-60" width="30" height="60" fill="#3b2818"/><circle cx="118" cy="-30" r="2" fill="{glow}"/>')
    g.append(f'<rect x="-6" y="-2" width="212" height="6" fill="#1a1f1c"/>')
    g.append("</g>")
    return "".join(g)


def stars(seed, n, w, h, ymax, rmax=1.6):
    rnd = random.Random(seed)
    out = []
    for _ in range(n):
        x, y = rnd.uniform(0, w), rnd.uniform(0, ymax)
        r = rnd.uniform(0.4, rmax)
        o = rnd.uniform(0.35, 1)
        out.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r:.2f}" fill="#fff" fill-opacity="{o:.2f}"/>')
    return "".join(out)


# ---------- hero layers ----------
W, H = 1600, 700
back = layer(1, ridge_fn(330, 26, 0.4), "#3b5546", 70, 70, 140, W, H)
mid_ridge = ridge_fn(430, 22, 1.7)
mid = layer(2, mid_ridge, "#263d31", 48, 120, 230, W, H,
            extra=cabin(1010, mid_ridge(1010) + 6, 0.42), keep=lambda x: not (930 < x < 1130))
front_ridge = ridge_fn(560, 18, 3.1)
front = layer(3, front_ridge, "#16271f", 20, 260, 470, W, H,
              keep=lambda x: x < 380 or x > 1180)
save("hero-back.svg", svg(W, H, back, par="xMidYMax slice"))
save("hero-mid.svg", svg(W, H, mid, par="xMidYMax slice"))
save("hero-front.svg", svg(W, H, front, par="xMidYMax slice"))

sky_defs = ('<linearGradient id="s" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#0c1511"/>'
            '<stop offset=".55" stop-color="#1d372b"/><stop offset="1" stop-color="#8ea592"/></linearGradient>'
            '<radialGradient id="m" cx=".5" cy=".5" r=".5"><stop offset="0" stop-color="#f3efdc" stop-opacity=".55"/>'
            '<stop offset="1" stop-color="#f3efdc" stop-opacity="0"/></radialGradient>')
sky = (f'<rect width="1600" height="900" fill="url(#s)"/>{stars(7, 140, 1600, 900, 460)}'
       '<circle cx="1180" cy="190" r="170" fill="url(#m)"/><circle cx="1180" cy="190" r="46" fill="#f3efdc"/>'
       '<circle cx="1164" cy="178" r="8" fill="#d8d3bd"/><circle cx="1196" cy="206" r="11" fill="#d8d3bd" fill-opacity=".7"/>')
save("hero-sky.svg", svg(1600, 900, sky, sky_defs))

# ---------- cabin (house section) ----------
d = ('<linearGradient id="a" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#2c4a3d"/>'
     '<stop offset="1" stop-color="#c9d3c4"/></linearGradient>')
r1 = ridge_fn(330, 18, 0.8)
b = ['<rect width="900" height="700" fill="url(#a)"/>', stars(3, 40, 900, 260, 200),
     layer(11, r1, "#547563", 22, 90, 170, 900, 700),
     '<rect y="470" width="900" height="230" fill="#1c3026"/>']
b.append(pine(90, 560, 470, 190, "#0f1d16"))
b.append(pine(820, 570, 430, 170, "#0f1d16"))
b.append(pine(30, 600, 300, 120, "#16271f"))
b.append(cabin(270, 560, 2.0, smoke=True))
b.append('<rect y="560" width="900" height="140" fill="#14231c"/>')
b.append('<rect x="210" y="562" width="470" height="12" fill="#0f1a15" fill-opacity=".5"/>')
save("cabin.svg", svg(900, 700, "".join(b), d))

# ---------- gallery tiles (4:5) ----------
TW, TH = 600, 750
tiles = {}

# 1 exterior in morning fog
fog = ('<linearGradient id="a" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#9fb2a4"/>'
       '<stop offset="1" stop-color="#e7ebe2"/></linearGradient>'
       '<linearGradient id="f" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#e7ebe2" stop-opacity="0"/>'
       '<stop offset="1" stop-color="#e7ebe2" stop-opacity=".85"/></linearGradient>')
rr = ridge_fn(470, 14, 1.2)
t = ['<rect width="600" height="750" fill="url(#a)"/>', layer(21, rr, "#7d9684", 14, 110, 190, 600, 750),
     '<rect y="330" width="600" height="230" fill="url(#f)"/>',
     layer(22, ridge_fn(560, 10, 2.2), "#3f5b49", 8, 200, 320, 600, 750),
     cabin(190, 650, 1.35, wood="#7a5238", smoke=True),
     '<rect y="650" width="600" height="100" fill="#22382d"/>']
tiles["tile-exterior.svg"] = svg(TW, TH, "".join(t), fog)

# 2 stove
t = ['<rect width="600" height="750" fill="#3a2a1f"/>']
for i in range(0, 750, 60):
    t.append(f'<rect x="0" y="{i}" width="600" height="2" fill="#000" fill-opacity=".25"/>')
t += ['<rect y="610" width="600" height="140" fill="#26190f"/>',
      '<rect x="250" y="0" width="34" height="330" fill="#1b1b1b"/>',
      '<rect x="160" y="330" width="230" height="290" rx="6" fill="#1e1e1e"/>',
      '<rect x="190" y="380" width="170" height="130" rx="4" fill="#0b0b0b"/>',
      '<path d="M275,500 C240,470 262,440 268,410 C282,432 300,440 292,470 C310,462 316,448 314,436 C338,460 330,492 305,500Z" fill="#f2a65a"/>',
      '<path d="M278,500 C262,482 274,466 280,454 C288,466 300,474 294,490Z" fill="#fbd38d"/>',
      '<rect x="150" y="620" width="250" height="10" fill="#111"/>',
      '<rect x="60" y="560" width="80" height="60" rx="8" fill="#6b4530"/><circle cx="76" cy="590" r="20" fill="#8a5a3b"/>'
      '<rect x="60" y="500" width="80" height="60" rx="8" fill="#7a4f34"/><circle cx="76" cy="530" r="20" fill="#9a683f"/>',
      '<circle cx="275" cy="450" r="150" fill="#f2a65a" fill-opacity=".10"/>']
tiles["tile-stove.svg"] = svg(TW, TH, "".join(t))

# 3 porch morning
d = ('<linearGradient id="a" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#b9c8b8"/>'
     '<stop offset="1" stop-color="#f0e9d4"/></linearGradient>')
t = ['<rect width="600" height="750" fill="url(#a)"/>', layer(31, ridge_fn(400, 16, 0.3), "#6f8c78", 16, 120, 220, 600, 750),
     layer(32, ridge_fn(470, 12, 2.4), "#3c5a48", 10, 200, 320, 600, 750),
     '<rect y="540" width="600" height="210" fill="#5b3d28"/>']
for i in range(0, 600, 75):
    t.append(f'<rect x="{i}" y="540" width="2" height="210" fill="#000" fill-opacity=".28"/>')
t += ['<rect x="0" y="520" width="600" height="14" fill="#2b1e14"/>',
      '<rect x="40" y="0" width="20" height="530" fill="#2b1e14"/><rect x="540" y="0" width="20" height="530" fill="#2b1e14"/>',
      # chairs
      '<g fill="#1d1a17"><rect x="130" y="470" width="110" height="14" rx="3"/><rect x="130" y="400" width="14" height="150" rx="3" transform="rotate(-8 137 475)"/>'
      '<rect x="140" y="484" width="10" height="70"/><rect x="222" y="484" width="10" height="70"/></g>',
      '<g fill="#1d1a17"><rect x="330" y="470" width="110" height="14" rx="3"/><rect x="330" y="400" width="14" height="150" rx="3" transform="rotate(-8 337 475)"/>'
      '<rect x="340" y="484" width="10" height="70"/><rect x="422" y="484" width="10" height="70"/></g>',
      '<rect x="270" y="500" width="34" height="40" rx="4" fill="#f4f1ea"/><path d="M304,510 h10 a8 10 0 0 1 0 20 h-10" fill="none" stroke="#f4f1ea" stroke-width="5"/>',
      '<path d="M280,488 c-8-14 8-16 0-30 M294,488 c-8-14 8-16 0-30" fill="none" stroke="#fff" stroke-opacity=".7" stroke-width="4" stroke-linecap="round"/>']
tiles["tile-porch.svg"] = svg(TW, TH, "".join(t), d)

# 4 library
rnd = random.Random(41)
cols = ["#8c3f2f", "#c58a3d", "#3f6b55", "#2d4a63", "#b8a27a", "#6b3f5a", "#d8d0bd", "#4a5d3a"]
t = ['<rect width="600" height="750" fill="#2a2018"/>']
for shelf in range(4):
    y0 = 40 + shelf * 150
    x = 30
    while x < 570:
        bw, bh = rnd.uniform(16, 34), rnd.uniform(78, 118)
        t.append(f'<rect x="{x:.1f}" y="{y0 + 118 - bh:.1f}" width="{bw:.1f}" height="{bh:.1f}" rx="2" fill="{rnd.choice(cols)}"/>')
        x += bw + rnd.uniform(1, 4)
    t.append(f'<rect x="14" y="{y0 + 118}" width="572" height="14" fill="#4b3626"/>')
t += ['<rect x="0" y="0" width="14" height="750" fill="#4b3626"/><rect x="586" y="0" width="14" height="750" fill="#4b3626"/>',
      '<circle cx="470" cy="380" r="220" fill="#f2a65a" fill-opacity=".10"/>',
      '<rect y="660" width="600" height="90" fill="#1a130d"/>',
      '<path d="M60,700 v-110 a40 40 0 0 1 40-40 h140 a40 40 0 0 1 40 40 v110z" fill="#7b3d2e"/>',
      '<rect x="452" y="470" width="6" height="190" fill="#111"/><path d="M420,470 h70 l-14 -50 h-42z" fill="#f2a65a"/>']
tiles["tile-library.svg"] = svg(TW, TH, "".join(t))

# 5 lake at dawn
d = ('<linearGradient id="a" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#3f5f66"/>'
     '<stop offset=".6" stop-color="#e5b48f"/><stop offset="1" stop-color="#f3e2c3"/></linearGradient>'
     '<linearGradient id="w" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#e2b892"/>'
     '<stop offset="1" stop-color="#3a5058"/></linearGradient>')
t = ['<rect width="600" height="750" fill="url(#a)"/>', stars(5, 22, 600, 220, 220),
     '<circle cx="330" cy="400" r="46" fill="#fdf0cf" fill-opacity=".9"/>',
     layer(51, ridge_fn(420, 12, 0.9), "#405e5c", 22, 60, 120, 600, 750),
     '<rect y="470" width="600" height="280" fill="url(#w)"/>']
r5 = random.Random(52)
for i in range(26):
    y = 490 + i * 10
    x = r5.uniform(20, 480)
    t.append(f'<rect x="{x:.0f}" y="{y}" width="{r5.uniform(40, 120):.0f}" height="2" rx="1" fill="#fff" fill-opacity="{r5.uniform(.12, .35):.2f}"/>')
t += [
      '<rect x="0" y="600" width="230" height="10" fill="#2a1e15"/><rect x="0" y="610" width="6" height="40" fill="#2a1e15"/>'
      '<rect x="70" y="610" width="6" height="40" fill="#2a1e15"/><rect x="150" y="610" width="6" height="40" fill="#2a1e15"/>',
      pine(540, 760, 360, 150, "#0f1d16"), pine(470, 760, 250, 100, "#16271f")]
tiles["tile-lake.svg"] = svg(TW, TH, "".join(t), d)

# 6 night sky
d = ('<linearGradient id="a" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#070d12"/>'
     '<stop offset="1" stop-color="#1c3a36"/></linearGradient>'
     '<linearGradient id="g" x1="0" y1="1" x2="1" y2="0"><stop offset="0" stop-color="#cfe0e8" stop-opacity="0"/>'
     '<stop offset=".5" stop-color="#cfe0e8" stop-opacity=".22"/><stop offset="1" stop-color="#cfe0e8" stop-opacity="0"/></linearGradient>')
t = ['<rect width="600" height="750" fill="url(#a)"/>',
     '<path d="M-60,620 C150,380 380,220 680,60 L700,140 C420,300 200,480 20,720Z" fill="url(#g)"/>',
     stars(6, 260, 600, 750, 600, 1.9),
     layer(61, ridge_fn(660, 10, 1.1), "#0b1512", 6, 130, 220, 600, 750),
     pine(70, 780, 400, 150, "#070f0c"), pine(520, 780, 330, 130, "#070f0c"), pine(430, 780, 210, 90, "#0b1512")]
tiles["tile-sky.svg"] = svg(TW, TH, "".join(t), d)

for name, content in tiles.items():
    save(name, content)

# ---------- map ----------
d = ('<pattern id="c" width="60" height="60" patternUnits="userSpaceOnUse"><path d="M0,30 C15,10 45,50 60,30" fill="none" '
     'stroke="#9fb0a2" stroke-opacity=".35"/></pattern>')
m = ['<rect width="900" height="560" fill="#e6eadf"/><rect width="900" height="560" fill="url(#c)"/>']
for i, (cx, cy, r) in enumerate([(640, 310, 210), (640, 310, 150), (640, 310, 95), (640, 310, 45)]):
    m.append(f'<ellipse cx="{cx}" cy="{cy}" rx="{r * 1.25}" ry="{r}" fill="none" stroke="#8fa494" stroke-opacity=".5" stroke-width="1.5"/>')
m.append('<path d="M60,80 C240,120 320,60 470,190 S560,330 640,310" fill="none" stroke="#f4f1ea" stroke-width="10" stroke-linecap="round"/>')
m.append('<path d="M60,80 C240,120 320,60 470,190 S560,330 640,310" fill="none" stroke="#c4cbbc" stroke-width="2" stroke-linecap="round"/>')
m.append('<path d="M470,190 C520,250 560,310 640,310" fill="none" stroke="#e0782e" stroke-width="4" stroke-dasharray="2 10" stroke-linecap="round"/>')
m.append('<circle cx="60" cy="80" r="9" fill="#17211b"/><circle cx="640" cy="310" r="15" fill="#e0782e"/><circle cx="640" cy="310" r="30" fill="#e0782e" fill-opacity=".2"/>')
for x, y in [(700, 250), (720, 350), (585, 380), (760, 300), (560, 250), (690, 400)]:
    m.append(pine(x, y, 34, 16, "#5d7a58"))
save("map.svg", svg(900, 560, "".join(m), d))
print("done")
