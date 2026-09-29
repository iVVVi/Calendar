# Calendar

[Figma](https://www.figma.com/file/0yamrmvdTkix50QIscwOVJ/Fluent-Calendar-by-Alexander-Solonikov?node-id=0%3A6)

## Fjern skog

A static, dependency-free website for “Fjern skog” lives in [`fjern-skog/`](fjern-skog/). Open `fjern-skog/index.html` in a browser.

- The hero is a procedurally generated multi-layer SVG scene with scroll parallax (`fjern-skog/main.js`).
- Photographs are hot-linked from Unsplash and configured in one place — the `PHOTOS` map at the top of `main.js`. Replace any entry with a local path (e.g. `img/house.jpg`) to use your own image. Images that fail to load fall back to a quiet placeholder.
- The booking form is front-end only: availability is demo data and the request opens a pre-filled email (`letters@fjernskog.example` — replace with a real address).
