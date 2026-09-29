#!/usr/bin/env python3
"""Generates the SVG illustrations in assets/illustrations (deterministic, no dependencies).

Mood: dusk, dense forest, an old house with candles in the windows, a wild orchard,
antique interiors. Everything is drawn with simple shapes and gradients.
"""
import math
import os
import random

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "assets", "illustrations")
os.makedirs(OUT, exist_ok=True)

# ---------------------------------------------------------------- palette
CANDLE = "#f6c56f"
FLAME = "#ffd98a"
FLAME_CORE = "#fff3cf"
WAX = "#efe3c6"
WOOD = "#5a3a24"
WOOD_DARK = "#2b1c12"
WINE = "#6b2b2f"
MOSS = "#5b6d3c"
STONE = "#6b6558"


class Svg:
    def __init__(self, w, h, par="xMidYMid slice"):
        self.w, self.h, self.par = w, h, par
        self.defs, self.body, self._ids = [], [], {}

    def add(self, *parts):
        self.body.extend(parts)

    def _id(self, key, make):
        if key not in self._ids:
            i = f"d{len(self._ids)}"
            self._ids[key] = i
            self.defs.append(make(i))
        return self._ids[key]

    def rgrad(self, color, a0=0.6, a1=0.0):
        return self._id(("r", color, a0, a1), lambda i: (
            f'<radialGradient id="{i}"><stop offset="0" stop-color="{color}" stop-opacity="{a0}"/>'
            f'<stop offset="1" stop-color="{color}" stop-opacity="{a1}"/></radialGradient>'))

    def rgrad3(self, color, mid_off=0.55, a_mid=0.0, a_end=0.6):
        return self._id(("r3", color, mid_off, a_mid, a_end), lambda i: (
            f'<radialGradient id="{i}"><stop offset="0" stop-color="{color}" stop-opacity="0"/>'
            f'<stop offset="{mid_off}" stop-color="{color}" stop-opacity="{a_mid}"/>'
            f'<stop offset="1" stop-color="{color}" stop-opacity="{a_end}"/></radialGradient>'))

    def lgrad(self, stops, x2=0, y2=1):
        key = ("l", tuple(stops), x2, y2)

        def make(i):
            s = "".join(f'<stop offset="{o}" stop-color="{c}"' + (f' stop-opacity="{a[0]}"' if a else "") + "/>"
                        for o, c, *a in stops)
            return f'<linearGradient id="{i}" x1="0" y1="0" x2="{x2}" y2="{y2}">{s}</linearGradient>'
        return self._id(key, make)

    def clip(self, x, y, w, h, rx=0):
        return self._id(("c", x, y, w, h, rx), lambda i: (
            f'<clipPath id="{i}"><rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}"/></clipPath>'))

    def blur(self, std):
        return self._id(("b", std), lambda i: (
            f'<filter id="{i}" x="-30%" y="-30%" width="160%" height="160%"><feGaussianBlur stdDeviation="{std}"/></filter>'))

    def glow(self, cx, cy, r, color=CANDLE, a=0.55):
        g = self.rgrad(color, a, 0)
        self.add(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{r:.1f}" fill="url(#{g})"/>')

    def render(self):
        return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {self.w} {self.h}" '
                f'preserveAspectRatio="{self.par}"><defs>{"".join(self.defs)}</defs>{"".join(self.body)}</svg>')

    def save(self, name):
        with open(os.path.join(OUT, name), "w", encoding="utf-8") as f:
            f.write(self.render())


# ---------------------------------------------------------------- primitives
def pine_path(x, base, h, w, tiers=5):
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
    return "M" + " L".join(f"{px:.1f},{py:.1f}" for px, py in pts) + "Z"


def pine(S, x, base, h, w, fill, tiers=5):
    S.add(f'<path d="{pine_path(x, base, h, w, tiers)}" fill="{fill}"/>')


def ridge_fn(base, amp, phase):
    return lambda x: base + amp * math.sin(x / 210 + phase) + amp * 0.5 * math.sin(x / 83 + phase * 2)


def forest_layer(S, seed, ridge, fill, count, hmin, hmax, w, h, keep=None, round_trees=0):
    rnd = random.Random(seed)
    pts = [f"{x},{ridge(x):.1f}" for x in range(0, w + 40, 40)]
    S.add(f'<path d="M0,{h} L{" L".join(pts)} L{w},{h}Z" fill="{fill}"/>')
    for x in sorted(rnd.uniform(-20, w + 20) for _ in range(count)):
        if keep and not keep(x):
            continue
        th = rnd.uniform(hmin, hmax)
        pine(S, x, ridge(x) + 14, th, th * rnd.uniform(0.34, 0.46), fill)
    for _ in range(round_trees):
        x = rnd.uniform(0, w)
        if keep and not keep(x):
            continue
        cr = rnd.uniform(hmin * 0.35, hmax * 0.45)
        cy = ridge(x) - cr * 0.5
        for _ in range(9):
            S.add(f'<circle cx="{x + rnd.uniform(-cr, cr) * .8:.1f}" cy="{cy + rnd.uniform(-cr, cr) * .5:.1f}" '
                  f'r="{rnd.uniform(cr * .35, cr * .6):.1f}" fill="{fill}"/>')


def grass(S, x0, x1, base, hmin, hmax, colors, step=5, seed=0, lean=12, heads=0.0, head_color="#c9b48a", hfn=None):
    r = random.Random(seed)
    x = x0
    while x < x1:
        hi = hmax if hfn is None else min(hmax, hfn(x))
        h = r.uniform(min(hmin, hi), hi)
        dx = r.uniform(-lean, lean)
        w = r.uniform(2, 4.5)
        S.add(f'<path d="M{x:.1f},{base} Q{x + dx * .3:.1f},{base - h * .6:.1f} {x + dx:.1f},{base - h:.1f} '
              f'Q{x + dx * .3 + w:.1f},{base - h * .55:.1f} {x + w:.1f},{base}Z" fill="{r.choice(colors)}"/>')
        if heads and r.random() < heads:
            S.add(f'<ellipse cx="{x + dx:.1f}" cy="{base - h - 3:.1f}" rx="1.6" ry="4.5" fill="{head_color}" fill-opacity=".75"/>')
        x += r.uniform(step * .5, step * 1.4)


def apple(S, x, y, r, color="#b5432e", shadow=True):
    if shadow:
        S.add(f'<ellipse cx="{x:.1f}" cy="{y + r * .82:.1f}" rx="{r * 1.05:.1f}" ry="{r * .32:.1f}" fill="#000" fill-opacity=".38"/>')
    S.add(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r:.1f}" fill="{color}"/>'
          f'<circle cx="{x - r * .3:.1f}" cy="{y - r * .32:.1f}" r="{r * .38:.1f}" fill="#fff" fill-opacity=".16"/>'
          f'<path d="M{x:.1f},{y - r * .85:.1f} q{r * .1:.1f},{-r * .55:.1f} {r * .35:.1f},{-r * .7:.1f}" stroke="#2a1c10" stroke-width="{max(1, r * .12):.1f}" fill="none"/>')


APPLE_COLORS = ["#b5432e", "#c9892f", "#9c3428", "#c05a30", "#d1a445"]


def fruit_tree(S, x, base, h, cr, seed, leaf=("#2b3a22", "#34472a", "#223019"), trunk="#241a12",
               apples=True, hi="#4b5f34", lean=0.0):
    r = random.Random(seed)
    tw = h * 0.085
    top = base - h * 0.72
    S.add(f'<path d="M{x - tw:.1f},{base} C{x - tw * .7:.1f},{base - h * .3:.1f} {x - tw * 1.2:.1f},{base - h * .5:.1f} '
          f'{x - tw * .45 + lean:.1f},{top:.1f} L{x + tw * .5 + lean:.1f},{top:.1f} '
          f'C{x + tw * 1.3:.1f},{base - h * .45:.1f} {x + tw * .6:.1f},{base - h * .25:.1f} {x + tw * 1.15:.1f},{base}Z" fill="{trunk}"/>')
    for dx, dy in [(-.75, -.24), (.7, -.27), (.05, -.34), (-.35, -.12), (.4, -.14)]:
        S.add(f'<path d="M{x + lean:.1f},{top + 6:.1f} Q{x + lean + cr * dx * .3:.1f},{top + h * dy * .5:.1f} '
              f'{x + lean + cr * dx:.1f},{top + h * dy:.1f}" stroke="{trunk}" stroke-width="{tw * .55:.1f}" '
              f'fill="none" stroke-linecap="round"/>')
    cy = base - h * 0.92
    n = int(cr / 5) + 12
    for _ in range(n):
        a = r.uniform(0, math.tau)
        d = r.uniform(0, cr * .8)
        bx, by = x + lean + math.cos(a) * d * 1.15, cy + math.sin(a) * d * .6
        S.add(f'<circle cx="{bx:.1f}" cy="{by:.1f}" r="{r.uniform(cr * .22, cr * .42):.1f}" fill="{r.choice(leaf)}"/>')
    for _ in range(int(n / 3)):
        a = r.uniform(math.pi, math.tau)
        d = r.uniform(cr * .2, cr * .75)
        S.add(f'<circle cx="{x + lean + math.cos(a) * d:.1f}" cy="{cy + math.sin(a) * d * .55:.1f}" '
              f'r="{r.uniform(cr * .1, cr * .2):.1f}" fill="{hi}" fill-opacity=".35"/>')
    if apples:
        for _ in range(int(cr / 9) + 3):
            a = r.uniform(0, math.tau)
            d = r.uniform(cr * .15, cr * .8)
            S.add(f'<circle cx="{x + lean + math.cos(a) * d * 1.1:.1f}" cy="{cy + math.sin(a) * d * .6:.1f}" '
                  f'r="{r.uniform(2.6, 4.2):.1f}" fill="{r.choice(APPLE_COLORS)}"/>')


def candle(S, x, y, h=30, w=8, glow_r=60, glow_a=.5, lit=True, color=WAX):
    """A candle whose base sits at (x, y)."""
    top = y - h
    if lit:
        S.glow(x, top - 6, glow_r, CANDLE, glow_a)
    S.add(f'<rect x="{x - w / 2:.1f}" y="{top:.1f}" width="{w}" height="{h}" rx="1.5" fill="{color}"/>'
          f'<rect x="{x + w * .12:.1f}" y="{top:.1f}" width="{w * .38:.1f}" height="{h}" fill="#000" fill-opacity=".12"/>'
          f'<rect x="{x - .6:.1f}" y="{top - 4:.1f}" width="1.2" height="4" fill="#2a1c10"/>')
    if lit:
        S.add(f'<path d="M{x:.1f},{top - 17:.1f} C{x + w * .6:.1f},{top - 10:.1f} {x + w * .5:.1f},{top - 3:.1f} {x:.1f},{top - 2:.1f} '
              f'C{x - w * .5:.1f},{top - 3:.1f} {x - w * .6:.1f},{top - 10:.1f} {x:.1f},{top - 17:.1f}Z" fill="{FLAME}"/>'
              f'<path d="M{x:.1f},{top - 11:.1f} C{x + w * .25:.1f},{top - 8:.1f} {x + w * .2:.1f},{top - 4:.1f} {x:.1f},{top - 3:.1f} '
              f'C{x - w * .2:.1f},{top - 4:.1f} {x - w * .25:.1f},{top - 8:.1f} {x:.1f},{top - 11:.1f}Z" fill="{FLAME_CORE}"/>')


def arch_window(S, x, y, w, h, candles=((.3, 1), (.7, .8)), frame=WOOD_DARK, curtain="#5a2323", lit=True):
    r = w / 2
    d = f'M{x},{y + h} L{x},{y + r} A{r},{r} 0 0 1 {x + w},{y + r} L{x + w},{y + h}Z'
    fill = S.lgrad([(0, "#ffdc90"), (1, "#dc8636")]) if lit else S.lgrad([(0, "#243040"), (1, "#101820")])
    S.add(f'<path d="{d}" fill="url(#{fill})"/>')
    if lit:
        for fx, fs in candles:
            candle(S, x + w * fx, y + h - 3, h=h * .3 * fs, w=max(4, w * .12), glow_r=w * .5, glow_a=.55)
    sw = max(2, w * .07)
    S.add(f'<path d="M{x + w / 2},{y + 2} V{y + h} M{x},{y + h * .5} H{x + w}" stroke="{frame}" stroke-width="{sw * .7:.1f}"/>'
          f'<path d="{d}" fill="none" stroke="{frame}" stroke-width="{sw:.1f}"/>')
    S.add(f'<path d="M{x},{y + r} Q{x + w * .2},{y + h * .5} {x + w * .06},{y + h} L{x},{y + h}Z" fill="{curtain}"/>'
          f'<path d="M{x + w},{y + r} Q{x + w * .8},{y + h * .5} {x + w * .94},{y + h} L{x + w},{y + h}Z" fill="{curtain}"/>')
    S.add(f'<rect x="{x - 5}" y="{y + h}" width="{w + 10}" height="5" fill="#8b8576"/>')


# ---------------------------------------------------------------- the old house
def house(S, x, gy, s=1.0, smoke=True):
    """An old cottage: stone base, weathered boards, mossy roof, candles in every window.
    Local coordinates: width 0..320, ground line y=0, drawn at (x, gy) scaled by s."""
    r = random.Random(4)
    S.glow(x + 160 * s, gy - 90 * s, 300 * s, CANDLE, .16)
    S.add(f'<g transform="translate({x:.1f},{gy:.1f}) scale({s})">')
    S.add('<ellipse cx="160" cy="4" rx="200" ry="14" fill="#000" fill-opacity=".5"/>')
    # stone base
    S.add('<rect x="0" y="-46" width="320" height="46" fill="#4f4b41"/>')
    for row in range(3):
        xx = -10 + (row % 2) * 14
        while xx < 320:
            w = r.uniform(24, 46)
            S.add(f'<rect x="{max(0, xx):.1f}" y="{-46 + row * 15.3:.1f}" width="{min(w, 320 - max(0, xx)):.1f}" height="14.3" rx="3" '
                  f'fill="{r.choice(["#6b6558", "#5a5549", "#77705f", "#4f4b41", "#67614f"])}" stroke="#2d2a24" stroke-width=".8"/>')
            xx += w + 1.5
    # boards
    xx = 0
    while xx < 320:
        S.add(f'<rect x="{xx}" y="-118" width="10" height="72" fill="{r.choice(["#6b4a31", "#5d4029", "#734f35", "#644430"])}"/>'
              f'<rect x="{xx + 9.2}" y="-118" width="0.9" height="72" fill="#1c120a" fill-opacity=".6"/>')
        xx += 10
    S.add('<rect x="0" y="-118" width="320" height="72" fill="#000" fill-opacity=".14"/>')
    # roof
    S.add('<polygon points="-24,-112 34,-192 286,-192 344,-112" fill="#2c352a"/>')
    for i in range(1, 7):
        y = -112 - i * 12.5
        inset = (i / 6.4) * 58
        S.add(f'<path d="M{-24 + inset:.1f},{y:.1f} L{344 - inset:.1f},{y:.1f}" stroke="#000" stroke-opacity=".28" stroke-width="1.4"/>')
    for _ in range(26):
        mx, my = r.uniform(-6, 330), r.uniform(-192, -116)
        S.add(f'<ellipse cx="{mx:.1f}" cy="{my:.1f}" rx="{r.uniform(7, 22):.1f}" ry="{r.uniform(3, 7):.1f}" fill="{MOSS}" fill-opacity="{r.uniform(.45, .85):.2f}"/>')
    S.add('<rect x="-26" y="-116" width="372" height="6" fill="#1c1510"/>')
    S.add('<polygon points="-24,-112 34,-192 40,-190 -14,-112" fill="#fff" fill-opacity=".05"/>')
    # chimney
    S.add('<rect x="234" y="-238" width="34" height="56" fill="#514c42"/>'
          '<rect x="230" y="-242" width="42" height="9" fill="#3a362f"/>')
    for k in range(4):
        S.add(f'<rect x="{236 + k * 1}" y="{-232 + k * 12}" width="{r.uniform(12, 20):.1f}" height="8" rx="2" fill="#6a6558" fill-opacity=".6"/>')
    if smoke:
        S.add('<path d="M251,-246 C232,-278 272,-300 250,-336 C238,-358 262,-374 254,-406" fill="none" stroke="#e6dcc6" '
              'stroke-opacity=".22" stroke-width="12" stroke-linecap="round"/>')
    # dormer
    S.add('<rect x="141" y="-208" width="38" height="34" fill="#5d4029"/>'
          '<polygon points="134,-206 160,-232 186,-206" fill="#221a12"/>')
    arch_window(S, 148, -204, 24, 30, candles=((.5, 1),), frame="#1c120a", curtain="#5a2323")
    # windows
    S.glow(58, -74, 78, CANDLE, .4)
    S.glow(262, -74, 78, CANDLE, .4)
    arch_window(S, 36, -104, 46, 62, candles=((.28, 1.1), (.5, 1.5), (.74, .9)))
    arch_window(S, 238, -104, 46, 62, candles=((.32, 1.3), (.7, 1)))
    # door
    S.add('<path d="M134,0 L134,-58 A26,26 0 0 1 186,-58 L186,0Z" fill="#3a2517"/>')
    for k in range(1, 5):
        S.add(f'<path d="M{134 + k * 10.4:.1f},-84 V0" stroke="#160d07" stroke-opacity=".7" stroke-width="1.2"/>')
    S.add('<path d="M134,0 L134,-58 A26,26 0 0 1 186,-58 L186,0Z" fill="none" stroke="#1c120a" stroke-width="3"/>'
          '<path d="M134,-30 h52 M134,-56 h52" stroke="#1c120a" stroke-width="2.4"/>'
          '<circle cx="176" cy="-34" r="2.6" fill="#b58a3c"/>'
          '<rect x="122" y="-4" width="76" height="6" rx="2" fill="#8b8576"/>')
    arch_window(S, 150, -78, 20, 22, candles=((.5, .8),), frame="#1c120a", curtain="#000", lit=True)
    # lantern by the door
    S.glow(112, -78, 42, CANDLE, .55)
    S.add('<path d="M112,-96 v6" stroke="#1c120a" stroke-width="1.6"/>'
          '<rect x="106" y="-90" width="12" height="16" rx="2" fill="#f6c56f" stroke="#1c120a" stroke-width="2"/>')
    # ivy on the left
    for _ in range(30):
        S.add(f'<circle cx="{r.uniform(-4, 30):.1f}" cy="{r.uniform(-124, -4):.1f}" r="{r.uniform(4, 9):.1f}" '
              f'fill="{r.choice(["#2f4526", "#3d5730", "#27391f"])}"/>')
    # firewood
    for row, n in enumerate([5, 4, 3]):
        for i in range(n):
            cx, cy = 284 + i * 13 + row * 6.5 - 4, -8 - row * 12
            S.add(f'<circle cx="{cx}" cy="{cy}" r="6.4" fill="#6a4a2f" stroke="#2f1f12" stroke-width="1.4"/>'
                  f'<circle cx="{cx}" cy="{cy}" r="2.6" fill="none" stroke="#3b2716" stroke-width=".8"/>')
    S.add('</g>')
    # spill of light on the ground
    g = S.rgrad(CANDLE, .38, 0)
    S.add(f'<ellipse cx="{x + 60 * s:.1f}" cy="{gy + 4 * s:.1f}" rx="{90 * s:.1f}" ry="{18 * s:.1f}" fill="url(#{g})"/>'
          f'<ellipse cx="{x + 160 * s:.1f}" cy="{gy + 6 * s:.1f}" rx="{70 * s:.1f}" ry="{16 * s:.1f}" fill="url(#{g})"/>'
          f'<ellipse cx="{x + 262 * s:.1f}" cy="{gy + 4 * s:.1f}" rx="{90 * s:.1f}" ry="{18 * s:.1f}" fill="url(#{g})"/>')


def dusk_sky(S, w, h, ystop=1.0, n_stars=90, moon=None, seed=7):
    g = S.lgrad([(0, "#101426"), (.42, "#232a44"), (.7, "#4f4358"), (.88, "#9a6a55"), (1, "#d0925a")])
    S.add(f'<rect width="{w}" height="{h}" fill="url(#{g})"/>')
    r = random.Random(seed)
    for _ in range(n_stars):
        y = r.uniform(0, h * .5)
        S.add(f'<circle cx="{r.uniform(0, w):.1f}" cy="{y:.1f}" r="{r.uniform(.4, 1.5):.2f}" fill="#fff" fill-opacity="{r.uniform(.25, .9) * (1 - y / (h * .55)):.2f}"/>')
    if moon:
        mx, my = moon
        S.glow(mx, my, 170, "#f0e6c8", .32)
        S.add(f'<circle cx="{mx}" cy="{my}" r="30" fill="#efe5c6"/><circle cx="{mx - 9}" cy="{my - 6}" r="6" fill="#d8ccab" fill-opacity=".7"/>')
        for i in range(3):
            S.add(f'<ellipse cx="{mx + (i - 1) * 120}" cy="{my + 10 + i * 18}" rx="{130 - i * 20}" ry="5" fill="#101426" fill-opacity=".35"/>')


# ---------------------------------------------------------------- HERO LAYERS
def build_hero():
    W, H = 1600, 900
    S = Svg(W, H)
    dusk_sky(S, W, H, moon=(1240, 190), n_stars=110)
    S.save("hero-sky.svg")

    W, H = 1600, 700
    S = Svg(W, H, "xMidYMax slice")
    forest_layer(S, 1, ridge_fn(340, 24, .4), "#2b3b3a", 120, 80, 190, W, H)
    S.save("hero-back.svg")

    S = Svg(W, H, "xMidYMax slice")
    forest_layer(S, 2, ridge_fn(440, 20, 1.7), "#1a2a24", 80, 130, 270, W, H, round_trees=6)
    S.save("hero-mid.svg")

    # house + wild orchard (positioned separately in CSS so it can move per breakpoint)
    W, H = 1100, 600
    S = Svg(W, H, "xMidYMax meet")
    S.glow(550, 420, 420, CANDLE, .12)
    fruit_tree(S, 330, 500, 200, 100, 11, leaf=("#1d2a1f", "#243425", "#19241b"), trunk="#161009", hi="#3a4b2c")
    fruit_tree(S, 800, 498, 210, 104, 12, leaf=("#1d2a1f", "#243425", "#19241b"), trunk="#161009", hi="#3a4b2c")
    fruit_tree(S, 118, 548, 330, 160, 13)
    fruit_tree(S, 985, 552, 300, 150, 14, lean=-6)
    kn = S.lgrad([(0, "#1f3022"), (1, "#0f1a13")])
    S.add(f'<path d="M0,600 L0,506 C150,484 330,498 550,492 C770,486 940,480 1100,504 L1100,600Z" fill="url(#{kn})"/>')
    house(S, 390, 512, 1.08)
    grass(S, 0, 1100, 560, 20, 70, ["#16261a", "#223421", "#2b3f24", "#1c2d1c"], step=5, seed=3, lean=9, heads=.14,
          hfn=lambda x: 26 if 380 < x < 750 else 80)
    grass(S, 0, 1100, 600, 30, 90, ["#101c13", "#182819"], step=6, seed=5, lean=10)
    r = random.Random(21)
    for _ in range(14):
        apple(S, r.choice([r.uniform(60, 260), r.uniform(830, 1060)]), r.uniform(548, 590), r.uniform(5, 7.5), r.choice(APPLE_COLORS))
    S.save("hero-house.svg")

    # foreground: gnarled trunks at the edges, tall grass, fallen apples
    W, H = 1600, 700
    S = Svg(W, H, "xMidYMax slice")
    dark, darker = "#0c130f", "#080d0a"
    S.add(f'<path d="M-20,700 C10,520 -10,340 40,180 C60,110 40,40 60,-20 L150,-20 C130,60 150,120 128,200 C110,340 150,540 140,700Z" fill="{dark}"/>')
    S.add(f'<path d="M1620,700 C1590,540 1610,330 1560,170 C1540,100 1560,30 1540,-20 L1450,-20 C1470,50 1450,120 1470,200 C1490,350 1450,540 1460,700Z" fill="{dark}"/>')
    r = random.Random(31)
    for side, x0 in [(0, 60), (1, 1540)]:
        for _ in range(30):
            S.add(f'<circle cx="{x0 + r.uniform(-90, 190) * (1 if side == 0 else -1):.1f}" cy="{r.uniform(-30, 200):.1f}" r="{r.uniform(30, 70):.1f}" fill="{r.choice([dark, darker, "#0f1a13"])}"/>')
        for dx, dy in [(140, -40), (220, -90), (90, -130)]:
            s = 1 if side == 0 else -1
            S.add(f'<path d="M{x0},{240} Q{x0 + s * dx * .5},{240 + dy * .5} {x0 + s * dx},{240 + dy}" stroke="{dark}" stroke-width="16" fill="none" stroke-linecap="round"/>')
    grass(S, 0, 1600, 705, 60, 190, [dark, darker, "#0f1a13", "#122016"], step=4.5, seed=8, lean=16, heads=.09, head_color="#7c7156")
    for _ in range(9):
        apple(S, r.uniform(120, 1480), r.uniform(668, 696), r.uniform(7, 11), r.choice(["#5a2a20", "#6b4a1f", "#4b1f19"]), shadow=False)
    S.save("hero-front.svg")


# ---------------------------------------------------------------- house at dusk (wide + tile)
def dusk_house_scene(name, w, h, hs, hx, gy, seed):
    S = Svg(w, h)
    dusk_sky(S, w, h, n_stars=50, seed=seed)
    ridge = ridge_fn(gy - 150, 16, seed)
    forest_layer(S, seed, ridge, "#2b3b3a", int(w / 12), 70, 150, w, h)
    forest_layer(S, seed + 1, ridge_fn(gy - 80, 12, seed + 2), "#1a2a24", int(w / 20), 120, 230, w, h)
    S.add(f'<rect y="{gy - 20}" width="{w}" height="{h - gy + 20}" fill="#16241a"/>')
    fruit_tree(S, hx - 90 * hs, gy + 24, 250 * hs, 120 * hs, seed + 3)
    fruit_tree(S, hx + 410 * hs, gy + 28, 230 * hs, 110 * hs, seed + 4, lean=-4)
    house(S, hx, gy, hs)
    grass(S, 0, w, gy + 40, 20, 90, ["#16261a", "#223421", "#2b3f24"], step=5, seed=seed, lean=9, heads=.12,
          hfn=lambda x: 22 if hx < x < hx + 320 * hs else 90)
    grass(S, 0, w, h + 4, 40, 110, ["#101c13", "#182819"], step=6, seed=seed + 5)
    S.save(name)


# ---------------------------------------------------------------- interiors
def painting(S, x, y, w, h, kind="forest", seed=1):
    fw = max(7, w * .07)
    g = S.lgrad([(0, "#7a5632"), (.5, "#3a2413"), (1, "#68452a")], 1, 1)
    S.add(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="2" fill="url(#{g})"/>'
          f'<rect x="{x + fw * .45:.1f}" y="{y + fw * .45:.1f}" width="{w - fw * .9:.1f}" height="{h - fw * .9:.1f}" fill="none" stroke="#c99a4b" stroke-opacity=".7" stroke-width="1.4"/>')
    ix, iy, iw, ih = x + fw, y + fw, w - 2 * fw, h - 2 * fw
    if kind == "portrait":
        S.add(f'<rect x="{ix}" y="{iy}" width="{iw}" height="{ih}" fill="#241a12"/>')
        cx = ix + iw / 2
        S.add(f'<path d="M{ix + iw * .12},{iy + ih} C{ix + iw * .15},{iy + ih * .68} {cx - iw * .2},{iy + ih * .62} {cx},{iy + ih * .62} '
              f'C{cx + iw * .2},{iy + ih * .62} {ix + iw * .85},{iy + ih * .68} {ix + iw * .88},{iy + ih}Z" fill="#3b2b26"/>'
              f'<ellipse cx="{cx}" cy="{iy + ih * .4}" rx="{iw * .16}" ry="{ih * .17}" fill="#b89572"/>'
              f'<path d="M{cx - iw * .18},{iy + ih * .36} C{cx - iw * .14},{iy + ih * .16} {cx + iw * .14},{iy + ih * .16} {cx + iw * .18},{iy + ih * .36} '
              f'C{cx + iw * .1},{iy + ih * .26} {cx - iw * .1},{iy + ih * .26} {cx - iw * .18},{iy + ih * .36}Z" fill="#2a1d15"/>'
              f'<rect x="{ix}" y="{iy}" width="{iw}" height="{ih}" fill="#000" fill-opacity=".22"/>')
        return
    cid = S.clip(ix, iy, iw, ih)
    sky = S.lgrad([(0, "#3d4a5a"), (.6, "#9c7b62"), (1, "#d4a06a")])
    S.add(f'<g clip-path="url(#{cid})"><rect x="{ix}" y="{iy}" width="{iw}" height="{ih}" fill="url(#{sky})"/>')
    if kind == "lake":
        wt = S.lgrad([(0, "#d4a06a"), (1, "#2c3a44")])
        S.add(f'<rect x="{ix}" y="{iy + ih * .6}" width="{iw}" height="{ih * .4}" fill="url(#{wt})"/>')
        S.add(f'<path d="M{ix},{iy + ih * .6} q{iw * .25},-{ih * .16} {iw * .5},-{ih * .04} t{iw * .5},0 V{iy + ih * .62}Z" fill="#3a4a42"/>')
    else:
        S.add(f'<path d="M{ix},{iy + ih * .7} C{ix + iw * .3},{iy + ih * .5} {ix + iw * .6},{iy + ih * .62} {ix + iw},{iy + ih * .48} V{iy + ih}H{ix}Z" fill="#3a4a3a"/>')
        S.add(f'<rect x="{ix}" y="{iy + ih * .8}" width="{iw}" height="{ih * .2}" fill="#243020"/>')
        r = random.Random(seed)
        for _ in range(6):
            px = ix + r.uniform(.05, .95) * iw
            pine(S, px, iy + ih * .82, ih * r.uniform(.25, .45), ih * .14, "#1a2a20", 4)
    S.add(f'<rect x="{ix}" y="{iy}" width="{iw}" height="{ih}" fill="#000" fill-opacity=".16"/></g>')


def vignette(S, w, h, a=.62):
    g = S.rgrad3("#000", .5, 0, a)
    S.add(f'<rect width="{w}" height="{h}" fill="url(#{g})"/>')


def floor_planks(S, y, w, h, colors=("#3a2716", "#1c120a")):
    g = S.lgrad([(0, colors[0]), (1, colors[1])])
    S.add(f'<rect y="{y}" width="{w}" height="{h - y}" fill="url(#{g})"/>')
    r = random.Random(3)
    for i in range(0, w + 60, 62):
        S.add(f'<path d="M{i + (y % 7)},{y} L{i - 40},{h}" stroke="#000" stroke-opacity=".35" stroke-width="1.6"/>')
    for k in range(1, 5):
        yy = y + (h - y) * k / 5
        S.add(f'<rect y="{yy:.1f}" width="{w}" height="1.2" fill="#000" fill-opacity=".22"/>')


def candelabra(S, x, y, s=1.0):
    S.add(f'<g transform="translate({x},{y}) scale({s})">')
    S.add('<path d="M-34,-64 Q-34,-40 0,-40 Q34,-40 34,-64" stroke="#b58a3c" stroke-width="3.4" fill="none"/>'
          '<path d="M0,0 V-40" stroke="#b58a3c" stroke-width="4"/>'
          '<ellipse cx="0" cy="0" rx="20" ry="5" fill="#b58a3c"/><ellipse cx="0" cy="-3" rx="9" ry="3" fill="#d8ad56"/>')
    S.add('</g>')
    for dx, hh in [(-34, 24), (0, 30), (34, 24)]:
        candle(S, x + dx * s, y - 62 * s if dx else y - 66 * s, h=hh * s, w=7 * s, glow_r=90 * s, glow_a=.6)


def tile_parlour():
    W, H = 600, 750
    S = Svg(W, H)
    g = S.lgrad([(0, "#37291d"), (1, "#22180f")])
    S.add(f'<rect width="{W}" height="{H}" fill="url(#{g})"/>')
    for x in range(0, W, 30):
        S.add(f'<rect x="{x}" width="14" height="560" fill="#fff" fill-opacity=".025"/>')
    S.add('<rect y="520" width="600" height="110" fill="#2b1f15"/>')
    for x in range(20, 600, 90):
        S.add(f'<rect x="{x}" y="534" width="70" height="80" fill="none" stroke="#000" stroke-opacity=".4" stroke-width="2"/>'
              f'<rect x="{x + 4}" y="538" width="62" height="72" fill="none" stroke="#fff" stroke-opacity=".05"/>')
    S.add('<rect y="514" width="600" height="8" fill="#4a3220"/><rect y="622" width="600" height="10" fill="#1a110a"/>')
    floor_planks(S, 632, W, H)
    S.add('<ellipse cx="300" cy="700" rx="270" ry="42" fill="#5b2a25"/><ellipse cx="300" cy="700" rx="240" ry="34" fill="none" stroke="#c48a3a" stroke-width="3"/>'
          '<ellipse cx="300" cy="700" rx="200" ry="26" fill="none" stroke="#c48a3a" stroke-opacity=".5" stroke-width="1.5" stroke-dasharray="6 6"/>')
    painting(S, 60, 110, 210, 160, "forest", 2)
    painting(S, 330, 80, 104, 150, "portrait")
    painting(S, 480, 210, 90, 70, "lake", 5)
    # armchair
    S.add('<ellipse cx="200" cy="642" rx="130" ry="12" fill="#000" fill-opacity=".45"/>')
    a = S.lgrad([(0, "#7c3238"), (1, "#4d1c22")])
    S.add(f'<path d="M96,560 V440 Q96,392 148,392 H252 Q304,392 304,440 V560Z" fill="url(#{a})"/>'
          f'<path d="M80,570 Q76,510 106,506 Q134,506 136,570Z M264,570 Q266,506 294,506 Q324,510 320,570Z" fill="url(#{a})"/>'
          f'<rect x="108" y="520" width="184" height="60" rx="14" fill="#8c3b41"/>'
          f'<rect x="108" y="520" width="184" height="16" rx="8" fill="#fff" fill-opacity=".1"/>'
          '<path d="M96,586 h208" stroke="#c48a3a" stroke-width="3"/>'
          '<path d="M100,590 l-8,40 M300,590 l8,40 M130,590 l-4,42 M270,590 l4,42" stroke="#241409" stroke-width="9" stroke-linecap="round"/>')
    for bx in (150, 200, 250):
        for by in (430, 466):
            S.add(f'<circle cx="{bx}" cy="{by}" r="3.4" fill="#2b0f13"/>')
    # side table + candelabra
    S.add('<ellipse cx="440" cy="632" rx="60" ry="8" fill="#000" fill-opacity=".45"/>'
          '<path d="M440,526 V628 M418,630 h44" stroke="#3e2818" stroke-width="10" stroke-linecap="round"/>'
          '<ellipse cx="440" cy="524" rx="64" ry="12" fill="#5a3a24"/><ellipse cx="440" cy="521" rx="64" ry="10" fill="#7a5233"/>')
    S.add('<rect x="480" y="500" width="38" height="20" fill="#3b4a5a"/><rect x="484" y="484" width="34" height="16" fill="#7a3b2e"/>')
    S.glow(430, 420, 300, CANDLE, .55)
    candelabra(S, 424, 520, 1.05)
    vignette(S, W, H)
    S.save("tile-parlour.svg")


def tile_bedroom():
    W, H = 600, 750
    S = Svg(W, H)
    g = S.lgrad([(0, "#2c3728"), (1, "#1a2218")])
    S.add(f'<rect width="{W}" height="{H}" fill="url(#{g})"/>')
    for x in range(0, W, 46):
        S.add(f'<rect x="{x}" width="3" height="600" fill="#fff" fill-opacity=".05"/>')
        for y in range(20, 600, 60):
            S.add(f'<circle cx="{x + 23}" cy="{y}" r="2.5" fill="#c9b48a" fill-opacity=".12"/>')
    S.add('<rect y="600" width="600" height="10" fill="#3a2716"/>')
    floor_planks(S, 610, W, H)
    S.add('<ellipse cx="300" cy="700" rx="280" ry="40" fill="#8a5a2f" fill-opacity=".85"/><ellipse cx="300" cy="700" rx="240" ry="30" fill="none" stroke="#e6cf9a" stroke-width="2.5"/>')
    S.add('<ellipse cx="330" cy="624" rx="230" ry="12" fill="#000" fill-opacity=".45"/>')
    h = S.lgrad([(0, "#5a3a22"), (1, "#3a2213")])
    # headboard
    S.add(f'<path d="M120,610 V250 Q120,190 190,190 H430 Q500,190 500,250 V610Z" fill="url(#{h})"/>'
          '<path d="M150,600 V262 Q150,224 196,224 H424 Q470,224 470,262 V600Z" fill="none" stroke="#000" stroke-opacity=".35" stroke-width="3"/>'
          '<circle cx="125" cy="192" r="12" fill="#6a4529"/><circle cx="495" cy="192" r="12" fill="#6a4529"/>')
    # oval mirror above
    S.add('<ellipse cx="310" cy="112" rx="66" ry="84" fill="#5a3a22"/><ellipse cx="310" cy="112" rx="56" ry="74" fill="#3d4a4a"/>'
          '<path d="M270,150 Q300,60 350,70" stroke="#fff" stroke-opacity=".14" stroke-width="10" fill="none"/>'
          '<ellipse cx="310" cy="112" rx="56" ry="74" fill="none" stroke="#c99a4b" stroke-opacity=".7" stroke-width="2"/>')
    # mattress + quilt
    S.add('<rect x="130" y="380" width="360" height="230" rx="10" fill="#d8c9a5"/>')
    for i, c in enumerate(["#b98a3f", "#7c3238", "#b98a3f", "#3f5a3f", "#b98a3f"]):
        S.add(f'<rect x="130" y="{440 + i * 34}" width="360" height="18" fill="{c}" fill-opacity=".85"/>')
    S.add('<rect x="130" y="380" width="360" height="52" rx="10" fill="#efe3c6"/><rect x="130" y="424" width="360" height="9" fill="#000" fill-opacity=".14"/>')
    S.add('<ellipse cx="225" cy="372" rx="80" ry="34" fill="#f2e8d0"/><ellipse cx="395" cy="372" rx="80" ry="34" fill="#efe3c6"/>'
          '<ellipse cx="225" cy="384" rx="80" ry="14" fill="#000" fill-opacity=".1"/>')
    S.add(f'<rect x="110" y="560" width="400" height="70" rx="6" fill="url(#{h})"/><circle cx="118" cy="552" r="11" fill="#6a4529"/><circle cx="502" cy="552" r="11" fill="#6a4529"/>')
    # nightstand + candle
    S.add('<rect x="516" y="500" width="76" height="120" fill="#3c2618"/><rect x="510" y="494" width="88" height="10" fill="#5a3a24"/>'
          '<rect x="526" y="520" width="56" height="34" fill="none" stroke="#000" stroke-opacity=".4" stroke-width="2"/><circle cx="554" cy="537" r="3" fill="#b58a3c"/>')
    S.glow(552, 440, 260, CANDLE, .6)
    candle(S, 552, 494, h=32, w=9, glow_r=120, glow_a=.7)
    S.add('<rect x="524" y="482" width="56" height="12" rx="3" fill="#b58a3c" fill-opacity=".9"/>')
    vignette(S, W, H, .68)
    S.save("tile-bedroom.svg")


def tile_hearth():
    W, H = 600, 750
    S = Svg(W, H)
    r = random.Random(9)
    S.add(f'<rect width="{W}" height="{H}" fill="#3f3b34"/>')
    for row in range(0, 12):
        xx = -30 + (row % 2) * 36
        while xx < W:
            w = r.uniform(60, 110)
            S.add(f'<rect x="{xx:.1f}" y="{row * 64}" width="{w:.1f}" height="62" rx="6" fill="{r.choice(["#5a554a", "#4d4940", "#665f52", "#48443b"])}" stroke="#1f1c17" stroke-width="2"/>')
            xx += w + 2
    S.add('<rect y="640" width="600" height="110" fill="#2a251f"/><rect y="636" width="600" height="8" fill="#5b5548"/>')
    S.add('<ellipse cx="300" cy="700" rx="230" ry="34" fill="#e2d5b8"/><path d="M110,700 q40,-20 80,-8 t80,0 t80,4 t80,-6" stroke="#b9a984" stroke-width="3" fill="none"/>')
    # arch opening
    S.add('<path d="M170,640 V400 A130,130 0 0 1 430,400 V640Z" fill="#0a0705"/>')
    S.glow(300, 560, 230, "#ff9a3c", .55)
    for i in range(4):
        S.add(f'<rect x="{200 + i * 8}" y="{610 - i * 12}" width="{200 - i * 16}" height="22" rx="10" fill="{["#3a2413", "#4a2f1b", "#3a2413", "#54351f"][i]}"/>')
    S.add('<path d="M300,470 C250,540 262,580 250,610 L350,610 C340,570 356,530 300,470Z" fill="#e0752a"/>'
          '<path d="M300,510 C270,560 276,590 268,610 L332,610 C326,585 336,555 300,510Z" fill="#f6b04a"/>'
          '<path d="M300,552 C288,580 288,600 284,610 L316,610 C312,596 312,578 300,552Z" fill="#ffe08a"/>')
    S.add('<path d="M170,640 V400 A130,130 0 0 1 430,400 V640" fill="none" stroke="#7a7466" stroke-width="30" stroke-dasharray="40 4"/>'
          '<path d="M170,640 V400 A130,130 0 0 1 430,400 V640" fill="none" stroke="#000" stroke-opacity=".3" stroke-width="30" stroke-dasharray="1 43"/>')
    # mantel
    m = S.lgrad([(0, "#6a4529"), (1, "#3c2413")])
    S.add(f'<rect x="110" y="220" width="380" height="30" rx="3" fill="url(#{m})"/><rect x="130" y="250" width="340" height="12" fill="#2b1a0e"/>')
    painting(S, 232, 70, 136, 108, "forest", 6)
    S.glow(300, 200, 260, CANDLE, .4)
    candle(S, 150, 220, h=44, w=11, glow_r=100, glow_a=.6)
    candle(S, 182, 220, h=28, w=9, glow_r=90, glow_a=.55)
    candle(S, 448, 220, h=38, w=10, glow_r=100, glow_a=.6)
    # clock
    S.add('<circle cx="404" cy="180" r="30" fill="#c99a4b"/><circle cx="404" cy="180" r="25" fill="#efe3c6"/>'
          '<path d="M404,180 V162 M404,180 l12,8" stroke="#2b1c12" stroke-width="2.4" stroke-linecap="round"/><rect x="384" y="210" width="40" height="10" fill="#8a6a2f"/>')
    # tools + log basket
    S.add('<path d="M470,650 L500,470" stroke="#1a1a1a" stroke-width="5"/><path d="M482,650 L518,480" stroke="#1a1a1a" stroke-width="5"/>'
          '<path d="M498,470 q10,-6 20,6" stroke="#1a1a1a" stroke-width="5" fill="none"/>')
    S.add('<rect x="30" y="560" width="110" height="86" rx="10" fill="#7a5a33"/>')
    for i in range(8):
        S.add(f'<path d="M{34 + i * 14},562 l12,82" stroke="#4a3419" stroke-width="2"/>')
    for i in range(3):
        S.add(f'<ellipse cx="{56 + i * 26}" cy="558" rx="15" ry="10" fill="#5a3a24" stroke="#2f1f12" stroke-width="2"/>')
    vignette(S, W, H, .6)
    S.save("tile-hearth.svg")


def tile_study():
    W, H = 600, 750
    S = Svg(W, H)
    S.add(f'<rect width="{W}" height="{H}" fill="#2a1e14"/>')
    r = random.Random(41)
    cols = ["#8c3f2f", "#c58a3d", "#3f6b55", "#2d4a63", "#b8a27a", "#6b3f5a", "#d8d0bd", "#4a5d3a"]
    for shelf in range(3):
        y0 = 30 + shelf * 130
        x = 24
        while x < 300:
            bw, bh = r.uniform(14, 30), r.uniform(70, 104)
            S.add(f'<rect x="{x:.1f}" y="{y0 + 104 - bh:.1f}" width="{bw:.1f}" height="{bh:.1f}" rx="2" fill="{r.choice(cols)}"/>')
            x += bw + r.uniform(1, 4)
        S.add(f'<rect x="10" y="{y0 + 104}" width="300" height="12" fill="#4b3626"/>')
    S.add('<rect x="0" y="0" width="12" height="430" fill="#4b3626"/><rect x="308" y="0" width="12" height="430" fill="#4b3626"/>')
    # arched night window
    arch_window(S, 372, 60, 190, 320, candles=(), frame="#1c120a", curtain="#3a1c20", lit=False)
    S.add('<circle cx="500" cy="150" r="16" fill="#efe5c6" fill-opacity=".9"/>')
    for i in range(7):
        pine(S, 385 + i * 27, 372, 90 + (i % 3) * 30, 34, "#0b1410", 4)
    S.add('<rect x="366" y="380" width="202" height="10" fill="#8b8576"/>')
    # wall behind desk
    S.add('<rect y="430" width="600" height="170" fill="#33251a"/>')
    floor_planks(S, 600, W, H, ("#33210f", "#170e07"))
    # desk
    d = S.lgrad([(0, "#5d3d24"), (1, "#3a2413")])
    S.add(f'<rect x="40" y="520" width="520" height="34" rx="4" fill="url(#{d})"/><rect x="40" y="520" width="520" height="8" fill="#2e4a3a"/>'
          f'<rect x="60" y="554" width="26" height="150" fill="url(#{d})"/><rect x="514" y="554" width="26" height="150" fill="url(#{d})"/>'
          f'<rect x="86" y="560" width="120" height="70" fill="none" stroke="#000" stroke-opacity=".35" stroke-width="3"/>')
    S.glow(300, 440, 300, CANDLE, .55)
    # open book, ink, quill
    S.add('<path d="M240,520 L300,508 L360,520 L360,530 L300,518 L240,530Z" fill="#efe3c6"/><path d="M300,508 V518" stroke="#8a7a5a" stroke-width="2"/>'
          '<path d="M250,522 l40,-8 M310,514 l42,8" stroke="#8a7a5a" stroke-width="1.2"/>')
    S.add('<rect x="414" y="500" width="22" height="20" rx="4" fill="#1c2a34"/><path d="M425,500 L470,440" stroke="#efe3c6" stroke-width="3"/>')
    # brass candlestick with two candles
    S.add('<rect x="130" y="508" width="30" height="12" rx="3" fill="#b58a3c"/><rect x="141" y="470" width="8" height="40" fill="#b58a3c"/>')
    candle(S, 145, 472, h=42, w=10, glow_r=130, glow_a=.7)
    candle(S, 195, 520, h=26, w=9, glow_r=90, glow_a=.55)
    # chair
    S.add('<path d="M270,640 V560 Q270,520 300,520" stroke="#2a1a0e" stroke-width="12" fill="none"/><rect x="250" y="600" width="140" height="18" rx="6" fill="#5a3a24"/>')
    vignette(S, W, H, .62)
    S.save("tile-study.svg")


def tile_sky():
    W, H = 600, 750
    S = Svg(W, H)
    g = S.lgrad([(0, "#070b12"), (1, "#1b2a30")])
    S.add(f'<rect width="{W}" height="{H}" fill="url(#{g})"/>')
    mw = S.lgrad([(0, "#cfe0e8", 0), (.5, "#cfe0e8", .22), (1, "#cfe0e8", 0)], 1, -1)
    S.add(f'<path d="M-60,620 C150,380 380,220 680,60 L700,140 C420,300 200,480 20,720Z" fill="url(#{mw})"/>')
    r = random.Random(6)
    for _ in range(260):
        S.add(f'<circle cx="{r.uniform(0, W):.1f}" cy="{r.uniform(0, 600):.1f}" r="{r.uniform(.4, 1.9):.2f}" fill="#fff" fill-opacity="{r.uniform(.35, 1):.2f}"/>')
    forest_layer(S, 61, ridge_fn(660, 10, 1.1), "#0b1512", 6, 130, 220, W, H)
    pine(S, 70, 780, 400, 150, "#070f0c")
    pine(S, 520, 780, 330, 130, "#070f0c")
    pine(S, 430, 780, 210, 90, "#0b1512")
    S.add('<circle cx="330" cy="690" r="2.5" fill="#f6c56f"/>')
    S.glow(330, 690, 22, CANDLE, .7)
    S.save("tile-sky.svg")


# ---------------------------------------------------------------- ORCHARD
def orchard_ground(S, w, h, y0):
    g = S.lgrad([(0, "#27341f"), (1, "#0f180f")])
    S.add(f'<rect y="{y0}" width="{w}" height="{h - y0}" fill="url(#{g})"/>')


def moss_stone(S, x, y, w, h, seed=0):
    r = random.Random(seed)
    S.add(f'<ellipse cx="{x + w / 2:.1f}" cy="{y + h * .9:.1f}" rx="{w * .6:.1f}" ry="{h * .18:.1f}" fill="#000" fill-opacity=".35"/>'
          f'<path d="M{x},{y + h} Q{x - w * .05:.1f},{y + h * .3:.1f} {x + w * .35:.1f},{y + h * .08:.1f} Q{x + w * .8:.1f},{y:.1f} {x + w},{y + h * .55:.1f} L{x + w * .96:.1f},{y + h}Z" fill="#6b6a60"/>'
          f'<path d="M{x + w * .04:.1f},{y + h * .5:.1f} Q{x + w * .3:.1f},{y - h * .04:.1f} {x + w * .7:.1f},{y + h * .1:.1f} Q{x + w * .95:.1f},{y + h * .3:.1f} {x + w * .98:.1f},{y + h * .5:.1f} '
          f'Q{x + w * .7:.1f},{y + h * .36:.1f} {x + w * .4:.1f},{y + h * .44:.1f} Q{x + w * .2:.1f},{y + h * .5:.1f} {x + w * .04:.1f},{y + h * .5:.1f}Z" fill="{MOSS}"/>')
    for _ in range(6):
        S.add(f'<circle cx="{x + r.uniform(.1, .9) * w:.1f}" cy="{y + r.uniform(.05, .35) * h:.1f}" r="{r.uniform(2, 5):.1f}" fill="#78904a" fill-opacity=".8"/>')


def tile_orchard():
    W, H = 1200, 800
    S = Svg(W, H)
    g = S.lgrad([(0, "#2a3a44"), (.45, "#7a6a58"), (.62, "#d4a565")])
    S.add(f'<rect width="{W}" height="{H}" fill="url(#{g})"/>')
    S.glow(640, 380, 420, "#ffd89a", .55)
    forest_layer(S, 71, ridge_fn(330, 14, .3), "#4d5c52", 60, 50, 110, W, H)
    forest_layer(S, 72, ridge_fn(372, 10, 1.2), "#2e3f36", 45, 70, 150, W, H)
    orchard_ground(S, W, H, 400)
    # light rays
    ray = S.lgrad([(0, "#ffe2a8", .18), (1, "#ffe2a8", 0)])
    for x0, x1 in [(470, 300), (610, 610), (760, 980)]:
        S.add(f'<polygon points="{x0 - 20},380 {x0 + 30},380 {x1 + 90},800 {x1 - 40},800" fill="url(#{ray})"/>')
    # path receding into the mist
    p = S.lgrad([(0, "#8a7a55"), (1, "#3a3520")])
    S.add(f'<path d="M560,400 C570,470 470,560 400,640 C350,700 330,760 300,800 L720,800 C700,740 690,690 670,640 C640,560 650,470 640,400Z" fill="url(#{p})" fill-opacity=".85"/>')
    fog = S.lgrad([(0, "#e6d3b0", .95), (1, "#e6d3b0", 0)])
    S.add(f'<rect y="360" width="{W}" height="120" fill="url(#{fog})"/>')
    # middle trees along the path
    for x, b, h_, cr, sd in [(330, 470, 130, 70, 21), (860, 468, 136, 72, 22), (200, 500, 170, 90, 23), (1010, 500, 176, 92, 24)]:
        fruit_tree(S, x, b, h_, cr, sd, leaf=("#2a3a26", "#33462d", "#222f1d"), trunk="#1c130b", hi="#5b7040")
    S.add(f'<rect y="440" width="{W}" height="90" fill="url(#{S.lgrad([(0, "#e6d3b0", .45), (1, "#e6d3b0", 0)])})"/>')
    # big foreground trees
    fruit_tree(S, 110, 810, 640, 300, 31, lean=20)
    fruit_tree(S, 1120, 820, 620, 290, 32, lean=-26)
    # grass, flowers, stones, windfalls
    grass(S, 0, W, 800, 40, 190, ["#1c2b16", "#28401e", "#33502a", "#14200f"], step=4.5, seed=41, lean=14, heads=.06,
          hfn=lambda x: 60 if 380 < x < 800 else 190)
    moss_stone(S, 250, 690, 120, 70, 1)
    moss_stone(S, 880, 700, 150, 84, 2)
    moss_stone(S, 690, 620, 60, 34, 3)
    r = random.Random(42)
    for _ in range(22):
        x = r.uniform(140, 1080)
        if 470 < x < 720:
            continue
        apple(S, x, r.uniform(700, 780), r.uniform(9, 15), r.choice(APPLE_COLORS))
    for _ in range(46):
        x, y = r.uniform(0, W), r.uniform(560, 780)
        S.add(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r.uniform(1.5, 3):.1f}" fill="#f1e8d2" fill-opacity=".8"/>')
    vignette(S, W, H, .5)
    S.save("tile-orchard.svg")


def tile_orchard_apples():
    W, H = 600, 750
    S = Svg(W, H)
    g = S.lgrad([(0, "#1a2418"), (1, "#0b120b")])
    S.add(f'<rect width="{W}" height="{H}" fill="url(#{g})"/>')
    S.glow(300, 280, 380, "#ffd89a", .32)
    forest_layer(S, 81, ridge_fn(300, 10, .4), "#1d2c24", 30, 60, 120, W, H)
    S.add('<path d="M0,520 Q150,440 320,480 T600,470 V750H0Z" fill="#2a3a20"/>')
    S.add('<path d="M40,640 Q180,590 330,620 T580,610 V750H40Z" fill="#33481f"/>')
    grass(S, 0, W, 560, 30, 110, ["#243519", "#33502a", "#1c2b16"], step=5, seed=51, lean=10)
    moss_stone(S, 330, 610, 220, 110, 7)
    r = random.Random(52)
    for x, y, rr, c in [(160, 640, 58, "#b5432e"), (280, 690, 48, "#c9892f"), (90, 715, 40, "#9c3428"), (230, 610, 34, "#c05a30"),
                        (430, 700, 52, "#b5432e"), (520, 640, 36, "#d1a445")]:
        apple(S, x, y, rr, c)
    # leaves
    for _ in range(9):
        lx, ly = r.uniform(30, 570), r.uniform(600, 730)
        S.add(f'<path d="M{lx:.1f},{ly:.1f} q14,-16 34,-6 q-12,18 -34,6Z" fill="#6b7a2e" fill-opacity=".85"/>')
    grass(S, 0, W, 760, 60, 170, ["#0f1a0c", "#182714", "#14200f"], step=6, seed=53, lean=14, heads=.1, head_color="#8a7d5a")
    vignette(S, W, H, .55)
    S.save("tile-orchard-apples.svg")


def tile_orchard_path():
    W, H = 600, 750
    S = Svg(W, H)
    g = S.lgrad([(0, "#2a3a44"), (.5, "#8a7660"), (.62, "#e0b070")])
    S.add(f'<rect width="{W}" height="{H}" fill="url(#{g})"/>')
    S.glow(300, 400, 260, "#ffe0a0", .6)
    forest_layer(S, 91, ridge_fn(395, 8, .6), "#56645a", 26, 40, 90, W, H)
    orchard_ground(S, W, H, 420)
    pth = S.lgrad([(0, "#9a8860"), (1, "#3c3620")])
    S.add(f'<path d="M290,420 L310,420 C330,520 420,640 560,750 L40,750 C180,640 270,520 290,420Z" fill="url(#{pth})"/>')
    fog = S.lgrad([(0, "#eed9b2", 1), (1, "#eed9b2", 0)])
    S.add(f'<rect y="360" width="{W}" height="130" fill="url(#{fog})"/>')
    # receding trunks
    for i, (xl, xr, base, hh, cr) in enumerate([(232, 372, 452, 64, 38), (170, 436, 490, 110, 56), (80, 522, 560, 190, 90)]):
        fruit_tree(S, xl, base, hh, cr, 100 + i, leaf=("#2a3a26", "#33462d", "#222f1d"), trunk="#1c130b", hi="#5b7040")
        fruit_tree(S, xr, base + 2, hh, cr, 110 + i, leaf=("#2a3a26", "#33462d", "#222f1d"), trunk="#1c130b", hi="#5b7040")
    fruit_tree(S, -20, 790, 560, 250, 121, lean=30)
    fruit_tree(S, 640, 790, 540, 240, 122, lean=-30)
    grass(S, 0, W, 750, 30, 130, ["#1c2b16", "#28401e", "#33502a"], step=5, seed=131, lean=12, heads=.06,
          hfn=lambda x: 24 if 150 < x < 450 else 130)
    r = random.Random(132)
    for _ in range(9):
        x = r.choice([r.uniform(60, 180), r.uniform(420, 540)])
        apple(S, x, r.uniform(690, 740), r.uniform(8, 13), r.choice(APPLE_COLORS))
    moss_stone(S, 90, 660, 90, 50, 5)
    vignette(S, W, H, .55)
    S.save("tile-orchard-path.svg")


# ---------------------------------------------------------------- BATH
def tile_bath():
    W, H = 1200, 800
    S = Svg(W, H)
    r = random.Random(5)
    S.add(f'<rect width="{W}" height="{H}" fill="#2c2721"/>')
    for row in range(0, 14):
        xx = -30 + (row % 2) * 40
        while xx < W:
            w = r.uniform(70, 130)
            S.add(f'<rect x="{xx:.1f}" y="{row * 60}" width="{w:.1f}" height="58" rx="5" fill="{r.choice(["#3b352d", "#332e27", "#413a31", "#2f2a24"])}" stroke="#191612" stroke-width="2"/>')
            xx += w + 2
    # beam
    S.add('<rect width="1200" height="52" fill="#3c2614"/><rect y="46" width="1200" height="8" fill="#1a0f07"/>')
    # window with a view over the treetops
    wx, wy, ww, wh = 270, 70, 660, 500
    ar = ww / 2
    win = f'M{wx},{wy + wh} L{wx},{wy + ar} A{ar},{ar} 0 0 1 {wx + ww},{wy + ar} L{wx + ww},{wy + wh}Z'
    sky = S.lgrad([(0, "#141830"), (.35, "#2e3252"), (.6, "#7a5a68"), (.85, "#d29a68"), (1, "#f0c088")])
    cid = S._id(("cp", win), lambda i: f'<clipPath id="{i}"><path d="{win}"/></clipPath>')
    S.add(f'<g clip-path="url(#{cid})"><rect x="{wx}" y="{wy}" width="{ww}" height="{wh}" fill="url(#{sky})"/>')
    for _ in range(70):
        y = r.uniform(wy, wy + 220)
        S.add(f'<circle cx="{r.uniform(wx, wx + ww):.1f}" cy="{y:.1f}" r="{r.uniform(.5, 1.6):.2f}" fill="#fff" fill-opacity="{r.uniform(.3, .9):.2f}"/>')
    S.glow(700, 190, 200, "#f0e6c8", .35)
    S.add('<circle cx="700" cy="190" r="34" fill="#efe5c6"/><circle cx="690" cy="182" r="7" fill="#d8ccab" fill-opacity=".7"/>')
    # treetops, far to near
    for seed, top_min, top_max, color, cnt in [(201, 400, 450, "#5f6a66", 40), (202, 370, 440, "#34433f", 34), (203, 320, 420, "#182a25", 24)]:
        rr = random.Random(seed)
        for _ in range(cnt):
            th = wy + wh - rr.uniform(top_min, top_max)
            pine(S, rr.uniform(wx - 20, wx + ww + 20), wy + wh, th, th * .42, color, 5)
    mist = S.lgrad([(0, "#f0d8b0", .0), (.5, "#f0d8b0", .5), (1, "#f0d8b0", 0)])
    S.add(f'<rect x="{wx}" y="{wy + 340}" width="{ww}" height="90" fill="url(#{mist})"/>')
    S.add(f'<rect x="{wx}" y="{wy + 440}" width="{ww}" height="70" fill="#101c17"/></g>')
    # muntins + stone reveal
    S.add(f'<path d="{win}" fill="none" stroke="#5a5347" stroke-width="26"/><path d="{win}" fill="none" stroke="#1a1712" stroke-width="3"/>')
    for x in (wx + ww * .25, wx + ww * .5, wx + ww * .75):
        S.add(f'<path d="M{x:.1f},{wy + 6} V{wy + wh}" stroke="#1c120a" stroke-width="7"/>')
    for y in (wy + 230, wy + 370):
        S.add(f'<path d="M{wx},{y} H{wx + ww}" stroke="#1c120a" stroke-width="7"/>')
    # sill
    S.add(f'<rect x="{wx - 40}" y="{wy + wh}" width="{ww + 80}" height="30" fill="#6f695b"/><rect x="{wx - 40}" y="{wy + wh}" width="{ww + 80}" height="7" fill="#8b8576"/>'
          f'<rect x="{wx - 40}" y="{wy + wh + 30}" width="{ww + 80}" height="10" fill="#000" fill-opacity=".35"/>')
    sill_y = wy + wh
    S.glow(600, sill_y - 20, 460, CANDLE, .32)
    for x, hh, w in [(330, 44, 12), (390, 28, 9), (470, 60, 14), (760, 36, 10), (830, 52, 12), (880, 26, 9)]:
        candle(S, x, sill_y, h=hh, w=w, glow_r=110, glow_a=.55)
    S.add(f'<path d="M560,{sill_y} q-10,-70 6,-120 M566,{sill_y - 70} q30,-26 54,-44 M568,{sill_y - 100} q-22,-26 -20,-44" stroke="#4a3520" stroke-width="3" fill="none"/>')
    # painting on the left wall
    painting(S, 70, 190, 130, 170, "portrait")
    # floor
    floor_planks(S, 660, W, H, ("#3a2412", "#170d06"))
    S.add('<rect y="652" width="1200" height="10" fill="#1a110a"/>')
    # steam (blurred, behind & in front of the tub)
    bl = S.blur(7)
    S.add(f'<g filter="url(#{bl})" fill="none" stroke="#fff" stroke-linecap="round">')
    for x, o, wd, dy in [(470, .32, 18, 0), (560, .26, 22, 30), (650, .34, 20, 0), (740, .26, 16, 40), (820, .3, 20, 10), (610, .2, 26, 60)]:
        S.add(f'<path d="M{x},640 C{x - 40},{560 - dy} {x + 40},{500 - dy} {x - 10},{420 - dy} S{x + 30},{330 - dy} {x - 5},{260 - dy}" stroke-opacity="{o}" stroke-width="{wd}"/>')
    S.add('</g>')
    # the bath
    S.add('<ellipse cx="600" cy="752" rx="380" ry="26" fill="#000" fill-opacity=".5"/>')
    body = S.lgrad([(0, "#f2e8d0"), (.5, "#d9c9a3"), (1, "#a58f68")])
    S.add(f'<path d="M290,628 C290,724 400,770 600,770 C800,770 910,724 910,628Z" fill="url(#{body})"/>'
          '<path d="M300,650 C320,730 420,760 600,762" stroke="#fff" stroke-opacity=".28" stroke-width="10" fill="none"/>'
          '<ellipse cx="600" cy="628" rx="312" ry="48" fill="#efe3c6"/>')
    water = S.lgrad([(0, "#3a4a52"), (.5, "#a9906a"), (1, "#f0c88a")])
    S.add(f'<ellipse cx="600" cy="630" rx="286" ry="35" fill="url(#{water})"/>'
          '<path d="M360,624 q80,-14 160,0 M640,632 q90,-12 170,2" stroke="#fff" stroke-opacity=".3" stroke-width="3" fill="none"/>'
          '<ellipse cx="600" cy="630" rx="286" ry="35" fill="none" stroke="#b8a37a" stroke-width="3"/>')
    for x in (380, 820):
        S.add(f'<path d="M{x},760 q-18,10 -22,30 M{x},760 q14,10 30,26" stroke="#b58a3c" stroke-width="9" fill="none" stroke-linecap="round"/>'
              f'<circle cx="{x}" cy="752" r="14" fill="#c99a4b"/>')
    # standing tap
    S.add('<path d="M978,780 V600 Q978,566 940,566 H880" stroke="#b58a3c" stroke-width="12" fill="none" stroke-linecap="round"/>'
          '<path d="M978,780 V600" stroke="#e6c27a" stroke-width="3" fill="none" stroke-opacity=".6"/>'
          '<rect x="960" y="770" width="36" height="12" rx="4" fill="#b58a3c"/><circle cx="978" cy="640" r="7" fill="#c99a4b"/>'
          '<path d="M968,640 h-24 M988,640 h24" stroke="#b58a3c" stroke-width="6" stroke-linecap="round"/>')
    # candles around
    S.glow(160, 700, 260, CANDLE, .55)
    S.add('<rect x="120" y="738" width="90" height="16" rx="6" fill="#3a2413"/>')
    for x, hh, w in [(140, 78, 26), (180, 44, 16), (206, 30, 12)]:
        candle(S, x, 740, h=hh, w=w, glow_r=140, glow_a=.55)
    # stool with towels
    S.add('<rect x="1030" y="670" width="90" height="16" rx="5" fill="#5a3a24"/><path d="M1040,686 l-10,90 M1110,686 l10,90" stroke="#3a2413" stroke-width="10" stroke-linecap="round"/>'
          '<rect x="1040" y="620" width="70" height="50" rx="6" fill="#e8dcc0"/><rect x="1040" y="640" width="70" height="8" fill="#b98a3f" fill-opacity=".8"/>')
    candle(S, 1075, 620, h=30, w=10, glow_r=120, glow_a=.5)
    vignette(S, W, H, .6)
    S.save("tile-bath.svg")


# ---------------------------------------------------------------- MAP
def build_map():
    W, H = 900, 560
    S = Svg(W, H)
    S.add(f'<rect width="{W}" height="{H}" fill="#e3d6b8"/>')
    for i, (rx, ry) in enumerate([(262, 210), (188, 150), (120, 95), (56, 45)]):
        S.add(f'<ellipse cx="640" cy="310" rx="{rx}" ry="{ry}" fill="none" stroke="#a08a5c" stroke-opacity=".45" stroke-width="1.4"/>')
    for x in range(0, W, 60):
        S.add(f'<path d="M{x},0 C{x + 20},140 {x - 20},420 {x + 10},{H}" stroke="#a08a5c" stroke-opacity=".12" fill="none"/>')
    S.add('<path d="M60,80 C240,120 320,60 470,190 S560,330 640,310" fill="none" stroke="#f4ecd6" stroke-width="10" stroke-linecap="round"/>'
          '<path d="M60,80 C240,120 320,60 470,190 S560,330 640,310" fill="none" stroke="#b9a578" stroke-width="2" stroke-linecap="round"/>'
          '<path d="M470,190 C520,250 560,310 640,310" fill="none" stroke="#c0762a" stroke-width="4" stroke-dasharray="2 10" stroke-linecap="round"/>'
          '<circle cx="60" cy="80" r="9" fill="#2a1e14"/><circle cx="640" cy="310" r="15" fill="#d28a3c"/><circle cx="640" cy="310" r="32" fill="#d28a3c" fill-opacity=".22"/>')
    for x, y in [(700, 250), (720, 350), (585, 380), (760, 300), (560, 250), (690, 400), (520, 330), (780, 380)]:
        pine(S, x, y, 36, 17, "#5f7048")
    S.save("map.svg")


if __name__ == "__main__":
    build_hero()
    dusk_house_scene("house-dusk.svg", 900, 700, 1.25, 250, 540, 11)
    dusk_house_scene("tile-exterior.svg", 600, 750, 1.05, 140, 620, 21)
    tile_parlour()
    tile_bedroom()
    tile_hearth()
    tile_study()
    tile_sky()
    tile_orchard()
    tile_orchard_apples()
    tile_orchard_path()
    tile_bath()
    build_map()
    print("done")
