/* Fjern skog — booking page: date-range calendar, pricing, validation, confirmation */
(() => {
  'use strict';

  /* ------------------------------------------------------------------
     Config — change prices / rules here
     ------------------------------------------------------------------ */
  const CONFIG = {
    nightly: 130,
    minNights: 2,
    maxNights: 14,
    maxGuests: 4,
    monthsAhead: 12,
    packages: {
      weekend: { label: 'Weekend', nights: 2, price: 260, includes: [] },
      two: { label: 'For two', nights: 3, price: 420, includes: ['sauna', 'dinner'] },
      week: { label: 'Week', nights: 7, price: 790, includes: ['sauna'] },
      custom: { label: 'Your own stay', nights: null, price: null, includes: [] },
    },
    extras: {
      sauna: { label: 'Sauna evening', price: 40 },
      dinner: { label: 'Dinner cooked by your hosts', price: 60 },
      pickup: { label: 'Station pick-up & drive', price: 25 },
    },
    // Nights that are already taken, as [startOffset, endOffset] days from today (demo data).
    bookedOffsets: [[5, 8], [15, 18], [26, 30], [39, 41], [54, 61], [69, 72], [88, 92], [110, 116], [140, 143], [170, 176], [220, 224], [260, 264]],
  };

  const $ = (sel, root = document) => root.querySelector(sel);
  const $$ = (sel, root = document) => [...root.querySelectorAll(sel)];
  const eur = (n) => `€${n.toLocaleString('en-GB')}`;

  /* ---------- Shared: mobile menu ---------- */
  const nav = $('#nav');
  const menuBtn = $('#menu-btn');
  const setMenu = (open) => {
    menuBtn.setAttribute('aria-expanded', String(open));
    nav.classList.toggle('is-open', open);
  };
  menuBtn.addEventListener('click', () => setMenu(menuBtn.getAttribute('aria-expanded') !== 'true'));
  nav.addEventListener('click', (e) => { if (e.target.closest('a')) setMenu(false); });
  document.addEventListener('keydown', (e) => { if (e.key === 'Escape') setMenu(false); });

  /* ------------------------------------------------------------------
     Date helpers (all dates at local noon → immune to DST shifts)
     ------------------------------------------------------------------ */
  const at = (y, m, d) => new Date(y, m, d, 12);
  const addDays = (date, n) => at(date.getFullYear(), date.getMonth(), date.getDate() + n);
  const key = (date) => `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')}`;
  const diffDays = (a, b) => Math.round((b - a) / 86400000);
  const sameDay = (a, b) => !!a && !!b && key(a) === key(b);
  const fmtLong = new Intl.DateTimeFormat('en-GB', { weekday: 'short', day: 'numeric', month: 'short', year: 'numeric' });
  const fmtShort = new Intl.DateTimeFormat('en-GB', { weekday: 'short', day: 'numeric', month: 'short' });
  const fmtMonth = new Intl.DateTimeFormat('en-GB', { month: 'long', year: 'numeric' });

  const now = new Date();
  const today = at(now.getFullYear(), now.getMonth(), now.getDate());
  const firstBookable = addDays(today, 1);
  const lastBookable = addDays(today, 365);

  const bookedNights = new Set();
  CONFIG.bookedOffsets.forEach(([from, to]) => {
    for (let i = from; i <= to; i++) bookedNights.add(key(addDays(today, i)));
  });

  const isNightFree = (date) => date >= firstBookable && date <= lastBookable && !bookedNights.has(key(date));
  const nightsFree = (from, to) => { // every night in [from, to) is free
    for (let d = from; d < to; d = addDays(d, 1)) if (!isNightFree(d)) return false;
    return true;
  };

  /* ------------------------------------------------------------------
     State
     ------------------------------------------------------------------ */
  const state = {
    pkg: 'custom',
    checkIn: null,
    checkOut: null,
    hover: null,
    guests: 2,
    view: at(today.getFullYear(), today.getMonth(), 1),
  };

  const els = {
    months: $('#cal-months'),
    prev: $('#cal-prev'),
    next: $('#cal-next'),
    hint: $('#cal-hint'),
    errDates: $('#err-dates'),
    packages: $('#packages'),
    form: $('#booking-form'),
    guestsVal: $('#guests-val'),
    guestsMinus: $('#guests-minus'),
    guestsPlus: $('#guests-plus'),
    sIn: $('#s-in'), sOut: $('#s-out'), sNights: $('#s-nights'), sGuests: $('#s-guests'),
    sLines: $('#s-lines'), sTotal: $('#s-total'), sTip: $('#s-tip'),
    submit: $('#submit'),
    flow: $('#booking-flow'),
    confirm: $('#confirm'),
  };

  const extraInputs = {
    sauna: $('#x-sauna input'),
    dinner: $('#x-dinner input'),
    pickup: $('#x-pickup input'),
  };
  const extraRows = { sauna: $('#x-sauna'), dinner: $('#x-dinner'), pickup: $('#x-pickup') };

  Object.values(extraInputs).forEach((input) => input.addEventListener('change', () => update({ keepHint: true })));

  const nightsCount = () => (state.checkIn && state.checkOut ? diffDays(state.checkIn, state.checkOut) : 0);

  /* ------------------------------------------------------------------
     Calendar
     ------------------------------------------------------------------ */
  const hint = (text, warn = false) => {
    els.hint.textContent = text;
    els.hint.classList.toggle('is-warn', warn);
  };

  const defaultHint = () => {
    const pkg = CONFIG.packages[state.pkg];
    if (!state.checkIn) return hint(pkg.nights ? `Select your arrival day. We’ll add ${pkg.nights} nights.` : 'Select your arrival day.');
    if (!state.checkOut) return hint('Now select the day you leave.');
    hint(`${nightsCount()} night${nightsCount() === 1 ? '' : 's'}: ${fmtShort.format(state.checkIn)} → ${fmtShort.format(state.checkOut)}.`);
  };

  const monthHTML = (first) => {
    const y = first.getFullYear();
    const m = first.getMonth();
    const lead = (first.getDay() + 6) % 7; // Monday first
    const total = new Date(y, m + 1, 0).getDate();
    const previewEnd = !state.checkOut && state.checkIn && state.hover && state.hover > state.checkIn ? state.hover : null;

    let html = `<div class="cal__month"><h3 class="cal__month-title">${fmtMonth.format(first)}</h3><div class="cal__grid" role="grid" aria-label="${fmtMonth.format(first)}">`;
    ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'].forEach((d) => { html += `<div class="cal__dow" role="columnheader">${d}</div>`; });
    for (let i = 0; i < lead; i++) html += '<div class="cal__blank"></div>';

    for (let n = 1; n <= total; n++) {
      const date = at(y, m, n);
      const past = date < firstBookable;
      const booked = !past && bookedNights.has(key(date));
      const isStart = sameDay(date, state.checkIn);
      const isEnd = sameDay(date, state.checkOut);
      const inRange = state.checkIn && state.checkOut && date > state.checkIn && date < state.checkOut;
      const inPreview = previewEnd && date > state.checkIn && date < previewEnd;
      const isPreviewEnd = previewEnd && sameDay(date, previewEnd);

      // A date is a valid *departure* day if all nights before it are free — even if that night is booked.
      let clickable = false;
      if (state.checkIn && !state.checkOut && CONFIG.packages[state.pkg].nights === null && date > state.checkIn) {
        clickable = nightsFree(state.checkIn, date) && date <= lastBookable;
      }
      if (!clickable) clickable = isNightFree(date);

      const cls = ['cal-day'];
      if (past) cls.push('is-past');
      if (booked) cls.push('is-booked');
      if (sameDay(date, today)) cls.push('is-today');
      if (isStart) cls.push('is-start');
      if (isEnd) cls.push('is-end');
      if (isStart && state.checkOut) cls.push('has-range');
      if (isEnd && state.checkIn) cls.push('has-range');
      if (inRange) cls.push('is-range');
      if (inPreview) cls.push('is-preview');
      if (isPreviewEnd) cls.push('is-preview-end');
      if (isStart && previewEnd) cls.push('has-preview');

      const label = `${fmtLong.format(date)}${booked ? ', booked' : ''}${past ? ', unavailable' : ''}${isStart ? ', arrival' : ''}${isEnd ? ', departure' : ''}`;
      html += `<button type="button" class="${cls.join(' ')}" data-date="${key(date)}" aria-label="${label}" aria-disabled="${clickable ? 'false' : 'true'}"${isStart || isEnd ? ' aria-pressed="true"' : ''}>${n}</button>`;
    }
    return `${html}</div></div>`;
  };

  const renderCalendar = () => {
    const second = at(state.view.getFullYear(), state.view.getMonth() + 1, 1);
    els.months.innerHTML = monthHTML(state.view) + monthHTML(second);
    const minView = at(today.getFullYear(), today.getMonth(), 1);
    const maxView = at(today.getFullYear(), today.getMonth() + CONFIG.monthsAhead - 1, 1);
    els.prev.disabled = state.view <= minView;
    els.next.disabled = state.view >= maxView;
  };

  const paintCalendarOnly = () => {
    // Re-render while keeping keyboard focus on the same day.
    const focused = document.activeElement && document.activeElement.dataset ? document.activeElement.dataset.date : null;
    renderCalendar();
    if (focused) { const btn = $(`.cal-day[data-date="${focused}"]`, els.months); if (btn) btn.focus({ preventScroll: true }); }
  };

  const setError = (el, msg) => {
    el.textContent = msg || '';
    el.hidden = !msg;
  };

  const clearRange = () => { state.checkIn = null; state.checkOut = null; state.hover = null; };

  const pickDate = (date) => {
    setError(els.errDates, '');
    const pkg = CONFIG.packages[state.pkg];

    if (pkg.nights) { // fixed package: one click = arrival, departure is derived
      if (!isNightFree(date)) return hint('That night is not available — pick another arrival day.', true);
      const out = addDays(date, pkg.nights);
      if (!nightsFree(date, out)) {
        clearRange();
        return hint(`The ${pkg.nights} nights after that day aren’t all free. Try another arrival day.`, true);
      }
      state.checkIn = date; state.checkOut = out;
      return;
    }

    // custom stay: first click = arrival, second = departure
    if (!state.checkIn || state.checkOut || date <= state.checkIn) {
      if (!isNightFree(date)) return hint('That night is not available — pick another arrival day.', true);
      state.checkIn = date; state.checkOut = null;
      return;
    }
    const n = diffDays(state.checkIn, date);
    if (n < CONFIG.minNights) return hint(`The minimum stay is ${CONFIG.minNights} nights.`, true);
    if (n > CONFIG.maxNights) return hint(`The longest stay is ${CONFIG.maxNights} nights. Need more? Write to us in the notes.`, true);
    if (!nightsFree(state.checkIn, date)) return hint('Some of those nights are already booked — pick different dates.', true);
    state.checkOut = date;
  };

  els.months.addEventListener('click', (e) => {
    const btn = e.target.closest('.cal-day');
    if (!btn) return;
    if (btn.getAttribute('aria-disabled') === 'true') {
      const d = btn.dataset.date.split('-').map(Number);
      const date = at(d[0], d[1] - 1, d[2]);
      hint(date < firstBookable ? 'Past dates can’t be booked.' : 'That night is already booked.', true);
      return;
    }
    const d = btn.dataset.date.split('-').map(Number);
    els.hint.classList.remove('is-warn');
    pickDate(at(d[0], d[1] - 1, d[2]));
    state.hover = null;
    update({ keepHint: els.hint.classList.contains('is-warn') });
    const again = $(`.cal-day[data-date="${btn.dataset.date}"]`, els.months);
    if (again) again.focus({ preventScroll: true });
  });

  els.months.addEventListener('mouseover', (e) => {
    const btn = e.target.closest('.cal-day');
    if (!btn || !state.checkIn || state.checkOut || CONFIG.packages[state.pkg].nights) return;
    const [y, m, d] = btn.dataset.date.split('-').map(Number);
    const date = at(y, m - 1, d);
    if (state.hover && sameDay(state.hover, date)) return;
    state.hover = date;
    paintCalendarOnly();
  });
  els.months.addEventListener('mouseleave', () => {
    if (state.hover) { state.hover = null; paintCalendarOnly(); }
  });

  // Arrow-key navigation between days
  els.months.addEventListener('keydown', (e) => {
    const btn = e.target.closest('.cal-day');
    if (!btn) return;
    const step = { ArrowLeft: -1, ArrowRight: 1, ArrowUp: -7, ArrowDown: 7 }[e.key];
    if (!step) return;
    e.preventDefault();
    const [y, m, d] = btn.dataset.date.split('-').map(Number);
    const target = addDays(at(y, m - 1, d), step);
    if (target < at(today.getFullYear(), today.getMonth(), 1) || target > lastBookable) return;
    const visible = () => $(`.cal-day[data-date="${key(target)}"]`, els.months);
    if (!visible()) {
      state.view = at(target.getFullYear(), target.getMonth() - (step < 0 ? 0 : 1), 1);
      renderCalendar();
    }
    const next = visible();
    if (next) next.focus();
  });

  els.prev.addEventListener('click', () => { state.view = at(state.view.getFullYear(), state.view.getMonth() - 1, 1); renderCalendar(); });
  els.next.addEventListener('click', () => { state.view = at(state.view.getFullYear(), state.view.getMonth() + 1, 1); renderCalendar(); });

  /* ------------------------------------------------------------------
     Packages
     ------------------------------------------------------------------ */
  const setPackage = (name, { fromUser = false } = {}) => {
    if (!CONFIG.packages[name]) name = 'custom';
    state.pkg = name;
    $$('.pkg', els.packages).forEach((b) => b.setAttribute('aria-checked', String(b.dataset.package === name)));

    const pkg = CONFIG.packages[name];
    if (pkg.nights && state.checkIn) {
      const out = addDays(state.checkIn, pkg.nights);
      if (nightsFree(state.checkIn, out)) {
        state.checkOut = out;
      } else {
        clearRange();
        if (fromUser) hint(`Those ${pkg.nights} nights aren’t all free from your arrival day. Pick another start.`, true);
      }
    }
    // Included extras are always on; others reset when a package takes them over.
    pkg.includes.forEach((x) => { extraInputs[x].checked = false; });
    update({ keepHint: els.hint.classList.contains('is-warn') && fromUser });
  };

  els.packages.addEventListener('click', (e) => {
    const b = e.target.closest('.pkg');
    if (b) setPackage(b.dataset.package, { fromUser: true });
  });
  els.packages.addEventListener('keydown', (e) => { // roving arrow keys for the radio group
    const items = $$('.pkg', els.packages);
    const i = items.indexOf(document.activeElement);
    if (i < 0 || !['ArrowRight', 'ArrowDown', 'ArrowLeft', 'ArrowUp'].includes(e.key)) return;
    e.preventDefault();
    const next = items[(i + (e.key === 'ArrowRight' || e.key === 'ArrowDown' ? 1 : items.length - 1)) % items.length];
    next.focus();
    setPackage(next.dataset.package, { fromUser: true });
  });

  /* ------------------------------------------------------------------
     Guests
     ------------------------------------------------------------------ */
  const setGuests = (n) => {
    state.guests = Math.min(CONFIG.maxGuests, Math.max(1, n));
    update({ keepHint: true });
  };
  els.guestsMinus.addEventListener('click', () => setGuests(state.guests - 1));
  els.guestsPlus.addEventListener('click', () => setGuests(state.guests + 1));

  /* ------------------------------------------------------------------
     Pricing + summary
     ------------------------------------------------------------------ */
  const quote = () => {
    const pkg = CONFIG.packages[state.pkg];
    const nights = nightsCount();
    const lines = [];
    let total = 0;

    if (nights) {
      const base = pkg.price != null ? pkg.price : nights * CONFIG.nightly;
      total += base;
      lines.push([pkg.price != null ? `${pkg.label} · ${nights} nights` : `${nights} night${nights === 1 ? '' : 's'} × ${eur(CONFIG.nightly)}`, base]);
      pkg.includes.forEach((x) => lines.push([`${CONFIG.extras[x].label} (included)`, null]));
    }
    Object.entries(CONFIG.extras).forEach(([id, ex]) => {
      if (pkg.includes.includes(id) || !extraInputs[id].checked) return;
      total += ex.price;
      lines.push([ex.label, ex.price]);
    });
    return { nights, lines, total };
  };

  const update = ({ keepHint = false } = {}) => {
    const q = quote();
    const pkg = CONFIG.packages[state.pkg];

    // Extras included in the package
    Object.keys(extraRows).forEach((id) => {
      const included = pkg.includes.includes(id);
      extraRows[id].classList.toggle('is-included', included);
      extraInputs[id].disabled = included;
      const note = $('[data-note]', extraRows[id]);
      if (included) note.textContent = 'Included in this format';
      else note.textContent = { sauna: '€40', dinner: '€60 for the table', pickup: '€25 each way' }[id];
    });

    els.guestsVal.textContent = state.guests;
    els.guestsMinus.disabled = state.guests <= 1;
    els.guestsPlus.disabled = state.guests >= CONFIG.maxGuests;

    els.sIn.textContent = state.checkIn ? fmtLong.format(state.checkIn) : '—';
    els.sOut.textContent = state.checkOut ? fmtLong.format(state.checkOut) : '—';
    els.sNights.textContent = q.nights || '—';
    els.sGuests.textContent = state.guests;
    els.sTotal.textContent = eur(q.total);

    els.sLines.innerHTML = '';
    q.lines.forEach(([label, price]) => {
      const li = document.createElement('li');
      const a = document.createElement('span'); a.textContent = label;
      const b = document.createElement('span'); b.textContent = price == null ? '—' : eur(price);
      li.append(a, b);
      els.sLines.append(li);
    });

    const tip = state.pkg === 'custom' && q.nights === 7;
    els.sTip.hidden = !tip;
    if (tip) els.sTip.textContent = `Tip: the Week format is ${eur(q.nights * CONFIG.nightly - CONFIG.packages.week.price)} cheaper and includes a sauna evening.`;

    if (!keepHint) defaultHint();
    if (state.checkIn) {
      const m = at(state.checkIn.getFullYear(), state.checkIn.getMonth(), 1);
      const visibleFirst = state.view, visibleSecond = at(state.view.getFullYear(), state.view.getMonth() + 1, 1);
      if (m < visibleFirst || m > visibleSecond) state.view = m;
    }
    renderCalendar();
  };

  /* ------------------------------------------------------------------
     Validation + submit
     ------------------------------------------------------------------ */
  const emailOk = (v) => /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/.test(v);
  const fields = {
    name: { input: $('#f-name'), error: $('[data-for="f-name"]'), check: (v) => (v.trim().length >= 2 ? '' : 'Please tell us your name.') },
    email: { input: $('#f-email'), error: $('[data-for="f-email"]'), check: (v) => (emailOk(v.trim()) ? '' : 'Please enter a valid email address.') },
  };
  const validateField = (f) => {
    const msg = f.check(f.input.value);
    f.input.setAttribute('aria-invalid', msg ? 'true' : 'false');
    setError(f.error, msg);
    return !msg;
  };
  Object.values(fields).forEach((f) => {
    f.input.addEventListener('blur', () => { if (f.input.value) validateField(f); });
    f.input.addEventListener('input', () => { if (f.input.getAttribute('aria-invalid') === 'true') validateField(f); });
  });

  const STORE = 'fjernskog.bookings';
  const refCode = () => `FS-${Math.random().toString(36).slice(2, 8).toUpperCase()}`;

  // Replace the body of this function with a real request (e.g. fetch('/api/bookings', …) or a form service).
  const submitBooking = (payload) => new Promise((resolve) => {
    try {
      const all = JSON.parse(localStorage.getItem(STORE) || '[]');
      all.push(payload);
      localStorage.setItem(STORE, JSON.stringify(all));
    } catch (_) { /* storage may be unavailable (private mode) — the confirmation still works */ }
    setTimeout(() => resolve(payload), 1000);
  });

  let last = null;

  els.form.addEventListener('submit', async (e) => {
    e.preventDefault();
    let firstBad = null;

    if (!state.checkIn || !state.checkOut) {
      setError(els.errDates, 'Please choose your arrival and departure dates.');
      firstBad = firstBad || $('#cal');
    } else setError(els.errDates, '');

    Object.values(fields).forEach((f) => { if (!validateField(f) && !firstBad) firstBad = f.input; });

    if (firstBad) {
      firstBad.scrollIntoView({ behavior: 'smooth', block: 'center' });
      if (firstBad.focus && firstBad.tagName === 'INPUT') firstBad.focus({ preventScroll: true });
      return;
    }

    const q = quote();
    const pkg = CONFIG.packages[state.pkg];
    const payload = {
      ref: refCode(),
      package: state.pkg,
      checkIn: key(state.checkIn),
      checkOut: key(state.checkOut),
      nights: q.nights,
      guests: state.guests,
      extras: Object.keys(CONFIG.extras).filter((id) => pkg.includes.includes(id) || extraInputs[id].checked),
      total: q.total,
      name: fields.name.input.value.trim(),
      email: fields.email.input.value.trim(),
      phone: $('#f-phone').value.trim(),
      notes: $('#f-notes').value.trim(),
      createdAt: new Date().toISOString(),
    };

    els.submit.classList.add('is-dropping');
    $('.submit__label', els.submit).textContent = 'In the chest…';
    const saved = await submitBooking(payload);
    last = saved;
    showConfirmation(saved);
  });

  const showConfirmation = (b) => {
    const first = b.name.split(' ')[0];
    $('#confirm-msg').textContent = `Thank you, ${first}. We’ve received your request and will confirm by email within a day. Until then: start looking for that book you never had time to read.`;
    const card = $('#confirm-card');
    card.innerHTML = '';
    const row = (k, v, cls) => {
      const wrap = document.createElement('div');
      const dt = document.createElement('dt'); dt.textContent = k;
      const dd = document.createElement('dd'); dd.textContent = v; if (cls) dd.className = cls;
      wrap.append(dt, dd); card.append(wrap);
    };
    const [iy, im, id] = b.checkIn.split('-').map(Number);
    const [oy, om, od] = b.checkOut.split('-').map(Number);
    row('Reference', b.ref, 'ref');
    row('Arrive', fmtLong.format(at(iy, im - 1, id)));
    row('Leave', fmtLong.format(at(oy, om - 1, od)));
    row('Nights', String(b.nights));
    row('Guests', String(b.guests));
    if (b.extras.length) row('Extras', b.extras.map((x) => CONFIG.extras[x].label).join(', '));
    row('Total to pay on arrival', eur(b.total));

    els.flow.hidden = true;
    els.confirm.hidden = false;
    window.scrollTo({ top: 0, behavior: 'smooth' });
    els.confirm.focus({ preventScroll: true });
  };

  /* ---------- .ics download ---------- */
  $('#ics').addEventListener('click', () => {
    if (!last) return;
    const compact = (s) => s.replace(/-/g, '');
    const stamp = new Date().toISOString().replace(/[-:]/g, '').replace(/\.\d{3}/, '');
    const ics = [
      'BEGIN:VCALENDAR', 'VERSION:2.0', 'PRODID:-//Fjern skog//Booking//EN', 'CALSCALE:GREGORIAN', 'BEGIN:VEVENT',
      `UID:${last.ref}@fjernskog.example`, `DTSTAMP:${stamp}`,
      `DTSTART;VALUE=DATE:${compact(last.checkIn)}`, `DTEND;VALUE=DATE:${compact(last.checkOut)}`,
      'SUMMARY:Fjern skog — a stay with no signal',
      `DESCRIPTION:Reference ${last.ref}. Phone goes in the chest on arrival.`,
      'LOCATION:Fjern skog\\, Telemark\\, Norway', 'END:VEVENT', 'END:VCALENDAR',
    ].join('\r\n');
    const url = URL.createObjectURL(new Blob([ics], { type: 'text/calendar' }));
    const a = document.createElement('a');
    a.href = url; a.download = `fjern-skog-${last.ref}.ics`;
    document.body.append(a); a.click(); a.remove();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  });

  $('#again').addEventListener('click', () => {
    clearRange();
    els.form.reset();
    Object.values(fields).forEach((f) => { f.input.setAttribute('aria-invalid', 'false'); });
    state.guests = 2;
    els.submit.classList.remove('is-dropping');
    $('.submit__label', els.submit).textContent = 'Hand in my phone';
    els.confirm.hidden = true;
    els.flow.hidden = false;
    setPackage('custom');
    window.scrollTo({ top: 0, behavior: 'smooth' });
  });

  /* ------------------------------------------------------------------
     Init (supports ?package=weekend|two|week and #details)
     ------------------------------------------------------------------ */
  const params = new URLSearchParams(window.location.search);
  setPackage(params.get('package') || 'custom');
})();
