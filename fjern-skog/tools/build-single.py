#!/usr/bin/env python3
"""Bundles the site into one self-contained file: fjern-skog.html (CSS, JS and SVGs inlined)."""
import base64
import os
import re

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
read = lambda p: open(os.path.join(ROOT, p), encoding="utf-8").read()


def sub_once(text, old, new):
    assert old in text, f"pattern not found: {old[:60]!r}"
    return text.replace(old, new, 1)


def grab(pattern, text):
    m = re.search(pattern, text, re.S)
    assert m, pattern
    return m.group(0)


index, booking = read("index.html"), read("booking.html")
css = read("css/style.css") + "\n" + read("css/booking.css")
main_js, booking_js = read("js/main.js"), read("js/booking.js")

# ---- markup ----
sprite = grab(r'<svg width="0".*?</svg>', index)
sprite = sub_once(sprite, '</defs>', '<symbol id="i-check" viewBox="0 0 24 24"><path d="M5 12.5l4.5 4.5L19 7.5"/></symbol>'
                                     '<symbol id="i-chev" viewBox="0 0 24 24"><path d="M9 5l7 7-7 7"/></symbol></defs>')
skip = grab(r'<a class="skip".*?</a>', index)
header = grab(r'<header class="site-header".*?</header>', index)
home_main = grab(r'<main id="main">.*?</main>', index)
home_footer = grab(r'<footer class="footer">.*?</footer>', index)
book_main = grab(r'<main id="main" class="booking">.*?</main>', booking)
book_footer = grab(r'<footer class="footer footer--slim">.*?</footer>', booking)

book_main = sub_once(book_main, '<main id="main" class="booking">', '<main id="main-booking" class="booking">')
book_main = book_main.replace('href="index.html"', 'href="#/"')
book_footer = book_footer.replace('href="index.html"', 'href="#/"')
home_main = home_main.replace('href="booking.html#details"', 'href="#/booking"').replace('href="booking.html', 'href="#/booking')
header = header.replace('href="booking.html"', 'href="#/booking"')
home_main = re.sub(r' data-photo="[^"]*"', '', home_main)  # no external photos in the single file

body = (f'{sprite}\n{skip}\n{header}\n<div id="view-home">\n{home_main}\n{home_footer}\n</div>\n'
        f'<div id="view-booking" hidden>\n{book_main}\n{book_footer}\n</div>')

# ---- script patches ----
main_js = sub_once(main_js, "header.classList.toggle('is-solid', y > 40);",
                   "const inBooking = document.body.dataset.view === 'booking';\n    header.classList.toggle('is-solid', y > 40 || inBooking);")
main_js = sub_once(main_js, "setSignal(clamp(Math.round(4 * (1 - y / end)), 0, 4));",
                   "setSignal(inBooking ? 0 : clamp(Math.round(4 * (1 - y / end)), 0, 4));")
main_js = sub_once(main_js, "  onScroll();\n\n  /* ---------- Night",
                   "  window.__fjernRefresh = onScroll;\n  onScroll();\n\n  /* ---------- Night")

a = booking_js.index("  /* ---------- Shared: mobile menu ---------- */")
b = booking_js.index("  /* ------------------------------------------------------------------\n     Date helpers")
booking_js = booking_js[:a] + booking_js[b:]
booking_js = sub_once(booking_js, "  const params = new URLSearchParams(window.location.search);\n  setPackage(params.get('package') || 'custom');",
                      "  window.__fjernBooking = { setPackage: (name) => setPackage(name) };\n  setPackage('custom');")

router_js = r"""
(() => {
  'use strict';
  const home = document.getElementById('view-home');
  const booking = document.getElementById('view-booking');
  const TITLE_HOME = document.title;
  let view = null;

  const route = () => {
    const hash = window.location.hash;
    if (hash === '#main') { (booking.hidden ? document.getElementById('main') : document.getElementById('main-booking')).scrollIntoView(); return; }

    if (hash.startsWith('#/booking')) {
      const params = new URLSearchParams(hash.split('?')[1] || '');
      home.hidden = true; booking.hidden = false;
      document.body.dataset.view = 'booking';
      document.title = 'Book your stay — Fjern skog';
      if (view !== 'booking') window.__fjernBooking.setPackage(params.get('package') || 'custom');
      window.scrollTo(0, 0);
      view = 'booking';
    } else {
      const wasBooking = view === 'booking';
      booking.hidden = true; home.hidden = false;
      document.body.dataset.view = 'home';
      document.title = TITLE_HOME;
      view = 'home';
      const id = decodeURIComponent(hash.replace(/^#\/?/, ''));
      const target = id && document.getElementById(id);
      requestAnimationFrame(() => {
        if (target) target.scrollIntoView();
        else if (wasBooking || !view) window.scrollTo(0, 0);
      });
    }
    if (window.__fjernRefresh) window.__fjernRefresh();
  };

  window.addEventListener('hashchange', route);
  route();
})();
"""

# ---- assets: inline SVGs ----
def data_uri(name):
    raw = open(os.path.join(ROOT, "assets", "illustrations", name), "rb").read()
    return "data:image/svg+xml;base64," + base64.b64encode(raw).decode()

css = re.sub(r"\.\./assets/illustrations/([\w-]+\.svg)", lambda m: data_uri(m.group(1)), css)
body = re.sub(r"assets/illustrations/([\w-]+\.svg)", lambda m: data_uri(m.group(1)), body)

head = grab(r"<head>.*?</head>", index)
head = re.sub(r'\s*<link rel="icon".*?>', '', head)
head = re.sub(r'\s*<link rel="stylesheet" href="css/style.css">', '', head)
head = re.sub(r'\s*<script defer src="js/main.js"></script>', '', head)
favicon = "data:image/svg+xml;base64," + base64.b64encode(open(os.path.join(ROOT, "favicon.svg"), "rb").read()).decode()
head = head.replace("</head>", f'  <link rel="icon" href="{favicon}" type="image/svg+xml">\n  <style>\n{css}\n  </style>\n</head>')

html = (f'<!DOCTYPE html>\n<html lang="en">\n{head}\n<body data-view="home">\n{body}\n'
        f'<script>\n{main_js}\n</script>\n<script>\n{booking_js}\n</script>\n<script>{router_js}</script>\n</body>\n</html>\n')
out = os.path.join(ROOT, "fjern-skog.html")
open(out, "w", encoding="utf-8").write(html)
print(f"wrote {os.path.relpath(out)} ({len(html) / 1024:.0f} KB)")
