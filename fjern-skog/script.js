(function(){
  var reduce = matchMedia('(prefers-reduced-motion: reduce)').matches;
  var $ = function(s,c){return (c||document).querySelector(s)};
  var $$ = function(s,c){return Array.prototype.slice.call((c||document).querySelectorAll(s))};

  // page transition in
  window.addEventListener('load', function(){ setTimeout(function(){ $('#curtain').classList.add('gone'); }, 150); });

  // nav + mobile menu
  var nav = $('#nav'), btn = $('#menuBtn'), menu = $('#menu');
  function setMenu(open){
    btn.classList.toggle('open', open);
    menu.classList.toggle('open', open);
    btn.setAttribute('aria-expanded', open);
    menu.setAttribute('aria-hidden', !open);
    btn.setAttribute('aria-label', open ? 'Close menu' : 'Open menu');
    document.body.style.overflow = open ? 'hidden' : '';
  }
  btn.addEventListener('click', function(){ setMenu(!menu.classList.contains('open')); });
  $$('#menu a').forEach(function(a){ a.addEventListener('click', function(){ setMenu(false); }); });
  document.addEventListener('keydown', function(e){ if(e.key === 'Escape') setMenu(false); });

  // photographs missing: keep the composition, show a quiet plate instead of a broken icon
  $$('img').forEach(function(im){
    function miss(){ im.style.visibility = 'hidden'; im.parentNode.classList.add('missing'); }
    if (im.complete && im.naturalWidth === 0) miss(); else im.addEventListener('error', miss);
  });

  // hero + parallax
  var hero = $('#hero'), layers = $$('.layer[data-speed]'), veil = $('#veil'),
      content = $('#heroContent'), mist3 = $('.layer--mist3'), cue = $('.scrollcue'),
      glows = $$('.glow'), branch = $('.branch'), imgs = $$('img[data-parallax]');
  var ticking = false;
  function clamp(v){ return Math.max(0, Math.min(1, v)); }

  function update(){
    ticking = false;
    var y = window.scrollY, vh = window.innerHeight;
    nav.classList.toggle('solid', y > vh * 0.12 || menu.classList.contains('open') === false && y > vh * 0.12);

    var span = hero.offsetHeight - vh;
    var p = clamp(y / span); // 0..1 through hero
    if (y <= hero.offsetHeight) {
      layers.forEach(function(l){
        var s = parseFloat(l.dataset.speed);
        // background barely moves, foreground moves faster
        l.style.transform = 'translate3d(0,' + (-y * s * 0.35).toFixed(1) + 'px,0)' +
          (l.classList.contains('layer--trees-near') ? ' scale(' + (1 + p * 0.22).toFixed(3) + ')' : '') +
          (l.classList.contains('layer--trees-far') ? ' scale(' + (1 + p * 0.1).toFixed(3) + ')' : '');
      });
      // foreground closes in: branches descend and mist thickens over the house
      if (branch) branch.style.transform = 'translateY(' + (p * 55).toFixed(1) + '%) scaleY(' + (1 + p * 0.9).toFixed(2) + ')';
      mist3.style.opacity = (p * 0.95).toFixed(2);
      // windows stay lit, fade last
      var g = 0.85 - clamp((p - 0.7) / 0.3) * 0.7;
      glows.forEach(function(el){ el.style.filter = 'blur(' + (5 + p * 6) + 'px)'; });
      $('.layer--house').style.opacity = g.toFixed(2);
      veil.style.opacity = (clamp((p - 0.62) / 0.38) * 0.94).toFixed(2);
      content.style.opacity = (1 - clamp(p / 0.28)).toFixed(2);
      content.style.transform = 'translateY(' + (-p * 60).toFixed(1) + 'px)';
      cue.style.opacity = (1 - clamp(p / 0.1)).toFixed(2);
    }

    // gentle image parallax
    imgs.forEach(function(im){
      var r = im.parentNode.getBoundingClientRect();
      if (r.bottom < -100 || r.top > vh + 100) return;
      var k = parseFloat(im.dataset.parallax);
      var off = ((r.top + r.height / 2) - vh / 2) * -k;
      im.style.transform = 'translate3d(0,' + off.toFixed(1) + 'px,0)';
    });
  }
  function req(){ if(!ticking){ ticking = true; requestAnimationFrame(update); } }
  if (!reduce) { addEventListener('scroll', req, {passive:true}); addEventListener('resize', req); }
  addEventListener('scroll', function(){ nav.classList.toggle('solid', window.scrollY > window.innerHeight * 0.12); }, {passive:true});
  update();

  // reveals
  var io = new IntersectionObserver(function(es){
    es.forEach(function(e){ if(e.isIntersecting){ e.target.classList.add('in'); io.unobserve(e.target); } });
  }, {threshold: .18, rootMargin: '0px 0px -6% 0px'});
  $$('.reveal, .reveal-img').forEach(function(el){ io.observe(el); });

  // smooth in-page transitions (offset for fixed nav)
  $$('a[href^="#"]').forEach(function(a){
    a.addEventListener('click', function(e){
      var id = a.getAttribute('href');
      if (id.length < 2) return;
      var t = $(id); if(!t) return;
      e.preventDefault();
      t.scrollIntoView({behavior: reduce ? 'auto' : 'smooth', block: 'start'});
      history.replaceState(null, '', id);
    });
  });

  // booking
  var arrive = $('#arrive'), depart = $('#depart'), gc = $('#gCount'), acc = $('#acc'),
      avail = $('#avail'), availText = $('#availText'), form = $('#bookForm'), done = $('#bookDone');
  var guests = 2;
  function iso(d){ return d.toISOString().slice(0,10); }
  var today = new Date(); arrive.min = iso(today);
  // demo: a fixed set of weeks already taken (replace with real backend)
  var booked = [['2026-10-09','2026-10-14'],['2026-11-20','2026-11-24'],['2026-12-22','2027-01-03']];
  function max(){ return acc.value === 'house' ? 8 : 2; }
  function setGuests(n){ guests = Math.max(1, Math.min(max(), n)); gc.textContent = guests; check(); }
  $('#gMinus').onclick = function(){ setGuests(guests - 1); };
  $('#gPlus').onclick = function(){ setGuests(guests + 1); };
  acc.onchange = function(){ setGuests(guests); };
  arrive.onchange = function(){
    var d = new Date(arrive.value); d.setDate(d.getDate() + 1); depart.min = iso(d);
    if (depart.value && depart.value <= arrive.value) depart.value = '';
    check();
  };
  depart.onchange = check;
  function state(cls, msg){ avail.className = 'avail ' + cls; availText.textContent = msg; }
  function check(){
    if (!arrive.value || !depart.value) { state('', 'Choose your dates to check availability.'); return false; }
    var a = arrive.value, d = depart.value, nights = Math.round((new Date(d) - new Date(a)) / 864e5);
    var clash = booked.some(function(b){ return a < b[1] && d > b[0]; });
    if (clash) { state('no', 'Sadly the house is occupied on these dates. Try another week.'); return false; }
    state('ok', 'Available — ' + nights + ' night' + (nights > 1 ? 's' : '') + ', ' + guests + ' guest' + (guests > 1 ? 's' : '') + '.');
    return true;
  }
  form.addEventListener('submit', function(e){
    e.preventDefault();
    $$('.field', form).forEach(function(f){ f.classList.remove('err'); });
    var bad = [arrive, depart, $('#name'), $('#email')].filter(function(i){ return !i.value.trim() || (i.type === 'email' && !/^\S+@\S+\.\S+$/.test(i.value)); });
    bad.forEach(function(i){ i.closest('.field').classList.add('err'); });
    if (bad.length) { bad[0].focus(); return; }
    if (!check()) return;
    done.hidden = false;
    done.textContent = 'Thank you, ' + $('#name').value.trim().split(' ')[0] + '. Your request has been received — we will write to you within two days.';
    $('#bookBtn').disabled = true;
    done.scrollIntoView({behavior:'smooth', block:'center'});
  });
})();
