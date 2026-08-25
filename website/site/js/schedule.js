/* Self-scheduling for jobs that already exist in ServiceM8.
 *
 * Reached from /s/<token>, which nginx rewrites to schedule.html?t=<token>.
 * The token identifies one SM8 job. The customer picks a slot and the API
 * attaches it to THAT job — it never creates a new one, which matters
 * because on contract work the bill goes to YourRepair, not the occupier.
 *
 * Deliberately simple: no build step, no framework, matches booking.js.
 */
(function () {
  'use strict';

  const API_BASE = 'https://api.bettercallwes.co.uk';

  // The token comes from the PATH, not a query string. nginx rewrites
  // /s/<token> to schedule.html?t=<token> internally, which means nginx
  // sees the query string but the browser never does — the address bar
  // still reads /s/<token>. Reading location.search here returned empty
  // and every link showed "that link looks incomplete".
  // The ?t= fallback is for hitting schedule.html directly, which is
  // handy for testing and costs nothing.
  const TOKEN = (function () {
    const m = /^\/s\/([A-Za-z0-9_-]+)\/?$/.exec(window.location.pathname);
    if (m) return m[1];
    return new URLSearchParams(window.location.search).get('t') || '';
  }());

  const $ = (id) => document.getElementById(id);
  const show = (id) => { $(id).hidden = false; };
  const hide = (id) => { $(id).hidden = true; };
  const hideAll = () => ['state-loading', 'state-error', 'state-already',
    'state-pick', 'state-confirm', 'state-done'].forEach(hide);

  let chosen = null;   // {start, end}
  let state = null;    // ScheduleState from the API

  // ─── Formatting ────────────────────────────────────────────────
  const DAYS = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];
  const MONTHS = ['January', 'February', 'March', 'April', 'May', 'June', 'July',
    'August', 'September', 'October', 'November', 'December'];

  function parseLocal(iso) {
    // The API returns naive local ISO strings ("2026-08-26T09:00:00").
    // Appending Z or letting Date guess a timezone shifts UK times by an
    // hour in summer, which would show the customer the wrong slot.
    const m = /^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2})/.exec(iso);
    if (!m) return new Date(iso);
    return new Date(+m[1], +m[2] - 1, +m[3], +m[4], +m[5]);
  }

  const time = (d) => {
    const h = d.getHours(), mm = d.getMinutes();
    const ampm = h < 12 ? 'am' : 'pm';
    const h12 = h % 12 === 0 ? 12 : h % 12;
    return mm === 0 ? `${h12}${ampm}` : `${h12}.${String(mm).padStart(2, '0')}${ampm}`;
  };
  const dayLabel = (d) => `${DAYS[d.getDay()]} ${d.getDate()} ${MONTHS[d.getMonth()]}`;
  // Half-day allocations read better than "9.30am to 10.30am" for contract
  // work: the customer needs to know which half of the day to be in.
  const WINDOW_TEXT = { Morning: '9am to 12pm', Afternoon: '1pm to 5pm' };
  const fullLabel = (s, e, period) => period
    ? `${dayLabel(s)} ${period.toLowerCase()} (${WINDOW_TEXT[period] || ''})`
    : `${dayLabel(s)}, ${time(s)} to ${time(e)}`;

  // ─── API ───────────────────────────────────────────────────────
  async function api(path, opts) {
    const resp = await fetch(
      `${API_BASE}/api/schedule/${encodeURIComponent(TOKEN)}${path}`, opts);
    let body = null;
    try { body = await resp.json(); } catch (e) { /* non-JSON error page */ }
    if (!resp.ok) {
      const err = new Error((body && body.detail) || `Request failed (${resp.status})`);
      err.status = resp.status;
      throw err;
    }
    return body;
  }

  function fail(title, body) {
    hideAll();
    $('error-title').textContent = title;
    $('error-body').textContent = body || '';
    show('state-error');
  }

  // ─── Render ────────────────────────────────────────────────────
  function renderSummary() {
    const dl = $('summary');
    dl.innerHTML = '';
    const rows = [
      ['Job', state.service_name],
      ['Address', state.job_address],
      ['Reference', state.job_ref ? `#${state.job_ref}` : ''],
    ];
    rows.forEach(([k, v]) => {
      if (!v) return;
      // .booking-row is the existing dt/dd pair styling from manage-booking
      const row = document.createElement('div');
      row.className = 'booking-row';
      const dt = document.createElement('dt'); dt.textContent = k;
      const dd = document.createElement('dd'); dd.textContent = v;
      row.append(dt, dd);
      dl.appendChild(row);
    });
  }

  let slotsByDay = new Map();

  function renderSlots(slots) {
    const strip = $('day-strip');
    const list = $('slots');
    strip.innerHTML = '';
    list.innerHTML = '';
    slotsByDay = new Map();

    if (!slots.length) { show('slots-empty'); hide('slots-hint'); return; }

    // Group by day. A flat list of 40 times is a wall of numbers; the day
    // strip lets people find their day first, same as the booking form.
    slots.forEach((s) => {
      const start = parseLocal(s.start);
      const key = start.toDateString();
      if (!slotsByDay.has(key)) slotsByDay.set(key, []);
      slotsByDay.get(key).push({ start, end: parseLocal(s.end), period: s.period });
    });

    [...slotsByDay.keys()].forEach((key, i) => {
      const d = new Date(key);
      const pill = document.createElement('button');
      pill.type = 'button';
      pill.className = 'day-pill' + (i === 0 ? ' selected' : '');
      pill.dataset.key = key;
      pill.innerHTML =
        `<span class="dow">${DAYS[d.getDay()].slice(0, 3)}</span>`
        + `<span class="date">${d.getDate()}</span>`
        + `<span class="month">${MONTHS[d.getMonth()].slice(0, 3)}</span>`;
      pill.addEventListener('click', () => {
        strip.querySelectorAll('.day-pill').forEach((p) => p.classList.remove('selected'));
        pill.classList.add('selected');
        renderDay(key);
      });
      strip.appendChild(pill);
    });

    renderDay([...slotsByDay.keys()][0]);
  }

  function renderDay(key) {
    const list = $('slots');
    list.innerHTML = '';
    (slotsByDay.get(key) || []).forEach((s) => {
      const b = document.createElement('button');
      b.type = 'button';
      b.className = 'slot';
      if (s.period) {
        b.innerHTML = `${s.period}<span class="month" style="display:block;font-weight:500;">`
          + `${WINDOW_TEXT[s.period] || ''}</span>`;
        b.style.minHeight = '58px';
      } else {
        b.textContent = time(s.start);
      }
      b.addEventListener('click', () => {
        list.querySelectorAll('.slot').forEach((x) => x.classList.remove('selected'));
        b.classList.add('selected');
        chosen = s;
        hideAll();
        $('confirm-when').textContent = fullLabel(s.start, s.end, s.period);
        hide('confirm-error');
        show('state-confirm');
        if (window.lucide) window.lucide.createIcons();
      });
      list.appendChild(b);
    });
  }

  // ─── Flow ──────────────────────────────────────────────────────
  async function load() {
    if (!TOKEN) {
      fail('That link looks incomplete.',
        'Please use the full link from your message, or get in touch and we\'ll sort it.');
      return;
    }
    try {
      state = await api('');
    } catch (e) {
      if (e.status === 410) {
        fail('This link has expired.', 'Give Wes a call and he\'ll book you in.');
      } else if (e.status === 409) {
        fail('This job can\'t be booked online.', e.message);
      } else if (e.status === 400) {
        fail('That link isn\'t valid.',
          'Please use the link exactly as it appeared in your message.');
      } else {
        fail('Sorry — something went wrong.', e.message);
      }
      return;
    }

    if (state.already_scheduled) {
      hideAll();
      $('already-when').textContent = state.slot_start
        ? `Your appointment is ${fullLabel(parseLocal(state.slot_start), parseLocal(state.slot_end))}.`
        : 'Your appointment is already in the diary.';
      show('state-already');
      return;
    }

    $('greeting').textContent = state.customer_first
      ? `Hi ${state.customer_first}, pick a time that suits you`
      : 'Pick a time that suits you';
    $('lede').textContent =
      `Choose a slot for your ${(state.service_name || 'appointment').toLowerCase()}. `
      + 'Pick a morning or an afternoon that suits you and Wes will confirm straight away.';
    renderSummary();

    hideAll();
    show('state-pick');

    try {
      renderSlots(await api('/availability?days=21'));
    } catch (e) {
      hide('slots-hint');
      $('slots-empty').hidden = false;
    }
    if (window.lucide) window.lucide.createIcons();
  }

  async function confirm() {
    if (!chosen) return;
    const btn = $('btn-confirm');
    btn.disabled = true;
    btn.textContent = 'Booking…';
    hide('confirm-error');
    try {
      const fmt = (d) =>
        `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-`
        + `${String(d.getDate()).padStart(2, '0')}T${String(d.getHours()).padStart(2, '0')}:`
        + `${String(d.getMinutes()).padStart(2, '0')}:00`;
      await api('/confirm', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ slot_start: fmt(chosen.start), slot_end: fmt(chosen.end) }),
      });
      hideAll();
      $('done-when').textContent = fullLabel(chosen.start, chosen.end, chosen.period);
      show('state-done');
    } catch (e) {
      // 409 = someone (or Wes) took it first. Reload rather than leave
      // them staring at a slot they can't have.
      if (e.status === 409) {
        $('confirm-error').textContent = e.message + ' Reloading the available times…';
        $('confirm-error').hidden = false;
        setTimeout(load, 1800);
      } else {
        $('confirm-error').textContent = e.message;
        $('confirm-error').hidden = false;
      }
      btn.disabled = false;
      btn.textContent = 'Yes, book it';
    }
  }

  document.addEventListener('DOMContentLoaded', () => {
    $('btn-confirm').addEventListener('click', confirm);
    $('btn-back').addEventListener('click', () => { hideAll(); show('state-pick'); });
    load();
  });
})();
