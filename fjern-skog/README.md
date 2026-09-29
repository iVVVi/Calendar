# Fjern skog

Portfolio case: a website for a secluded antique apartment hidden in a forest, with no phone signal ("fjern skog" is Norwegian for "distant forest").
Plain HTML, CSS and JavaScript — no build step, no dependencies.

## Run

```sh
cd fjern-skog
python3 -m http.server 8000   # or any static server
# open http://localhost:8000
```

## Structure

| Path | What |
|---|---|
| `index.html` | Landing page (hero → the place → how a stay begins → the apartment → the orchard → the bath → your day → night → rules → prices → getting there → guests → FAQ → CTA) |
| `booking.html` | Date-range calendar, packages, live price, validation, confirmation, `.ics` download |
| `css/style.css`, `css/booking.css` | Design tokens and styles |
| `js/main.js` | Signal bars that fade as you scroll, parallax, flashlight in the night section, reveals |
| `js/booking.js` | Booking logic. Prices, rules and demo "booked" dates live in `CONFIG` at the top |
| `assets/illustrations/` | Generated SVG illustrations (`python3 tools/generate-illustrations.py` rebuilds them) |
| `assets/photos/` | Optional stock photos (see below) |
| `fjern-skog.html` | Single-file build of the whole site (`python3 tools/build-single.py`) |

## Stock photos

Every illustrated tile is a placeholder that upgrades itself: if a photo with the matching name exists in `assets/photos/`, it replaces the illustration automatically. Expected names:

`house-wide.jpg`, `parlour.jpg`, `bedroom.jpg`, `hearth.jpg`, `study.jpg`, `exterior.jpg`, `sky.jpg`, `orchard.jpg`, `orchard-apples.jpg`, `orchard-path.jpg`, `bath.jpg`

(Photos sit inside antique-style frames. Wide images ≈ 3:2, tiles ≈ 4:5.) Credit photographers in the page footer if the licence requires it.

## Booking backend

The prototype stores requests in `localStorage` only. To send them somewhere, replace the body of `submitBooking()` in `js/booking.js` with a `fetch()` to your API or a form service.

## Responsive

Desktop (>1024px), tablet (701–1024px, hamburger menu ≤900px) and mobile (≤700px, small phones ≤480px) layouts are handled in `css/style.css`; the hero house is positioned per breakpoint.
