/* Manage-booking page — reschedule + cancel a customer's existing
 * booking via the magic-link token in ?t=...
 *
 * Backend endpoints used:
 *   GET  /api/booking/{token}                 → current state
 *   GET  /api/booking/{token}/availability    → free slots
 *   POST /api/booking/{token}/reschedule      → move the slot
 *   POST /api/booking/{token}/cancel          → cancel the job
 *
 * No framework — vanilla JS, kept small enough to be readable.
 */

(function () {
  'use strict';

  const API_BASE = 'https://api.bettercallwes.co.uk';

  const $ = (sel) => document.querySelector(sel);

  // ─── Pull the token from the URL ────────────────────────────────────────
  const TOKEN = new URLSearchParams(window.location.search).get('t') || '';

  // ─── State held in memory ──────────────────────────────────────────────
  const state = {
    booking: null,    // ManageBookingState (from API)
    slots: [],        // available slots for the service
    pickedSlot: null, // selected slot for reschedule
    cancelReason: '', // radio category selected on the cancel panel
  };

  // Pre-set cancellation reasons. Single source of truth for the radio
  // labels — these strings land in SM8's "Reason for cancellation" field
  // as-is, so they need to read clearly there too.
  const CANCEL_REASONS = [
    'Found another tradesperson',
    'Problem resolved itself',
    'Change of plans',
    'Postponed — will book again later',
    'Other',
  ];

  const fmt = {
    longDate(d) {
      const day = d.getDate();
      const suffix = (day >= 10 && day <= 20) ? 'th' :
        ({ 1: 'st', 2: 'nd', 3: 'rd' })[day % 10] || 'th';
      return d.toLocaleDateString('en-GB', { weekday: 'long', month: 'long' })
        .replace(' ', ` ${day}${suffix} `);
    },
    time(d) {
      return d.toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit', hour12: false });
    },
    dayPill(d) {
      return {
        dow: d.toLocaleDateString('en-GB', { weekday: 'short' }),
        date: d.getDate(),
        month: d.toLocaleDateString('en-GB', { month: 'short' }),
      };
    },
  };

  // ─── Visibility helpers ────────────────────────────────────────────────
  function showState(stateName) {
    ['state-loading', 'state-error', 'state-loaded', 'state-rescheduled', 'state-cancelled']
      .forEach((id) => {
        const el = document.getElementById(id);
        if (el) el.hidden = (id !== stateName);
      });
    lucide.createIcons();
  }

  function showPanel(panelName) {
    ['panel-reschedule', 'panel-cancel'].forEach((id) => {
      document.getElementById(id).classList.toggle('show', id === panelName);
    });
    // Hide the action buttons when a panel is open
    document.getElementById('action-buttons').style.display = panelName ? 'none' : '';
    lucide.createIcons();
  }

  // ─── API ───────────────────────────────────────────────────────────────
  async function apiGet(path) {
    const resp = await fetch(`${API_BASE}/api/booking/${encodeURIComponent(TOKEN)}${path}`);
    const body = await resp.json().catch(() => ({}));
    if (!resp.ok) throw new ApiError(body.detail || `Request failed (${resp.status})`, resp.status);
    return body;
  }
  async function apiPost(path, body) {
    const resp = await fetch(`${API_BASE}/api/booking/${encodeURIComponent(TOKEN)}${path}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body || {}),
    });
    const respBody = await resp.json().catch(() => ({}));
    if (!resp.ok) throw new ApiError(respBody.detail || `Request failed (${resp.status})`, resp.status);
    return respBody;
  }
  class ApiError extends Error {
    constructor(msg, status) { super(msg); this.status = status; }
  }

  // ─── Boot ──────────────────────────────────────────────────────────────
  async function boot() {
    if (!TOKEN) {
      return showError(
        'No booking link provided',
        'This page needs a valid management link from your confirmation email or SMS.'
      );
    }
    try {
      state.booking = await apiGet('');
      renderLoaded();
    } catch (e) {
      if (e instanceof ApiError && e.status === 410) {
        showError("This link has expired", e.message);
      } else if (e instanceof ApiError && e.status === 400) {
        showError("Invalid link", e.message);
      } else if (e instanceof ApiError && e.status === 503) {
        showError("Self-serve management isn't available", e.message);
      } else {
        showError("Something went wrong", e.message || 'Please try again later.');
      }
    }
  }

  function showError(title, body) {
    document.getElementById('error-title').textContent = title;
    document.getElementById('error-body').textContent = body;
    showState('state-error');
  }

  // ─── Render the loaded state ───────────────────────────────────────────
  function renderLoaded() {
    const b = state.booking;
    document.getElementById('greeting').textContent = `Hi ${b.customer_first}, manage your booking`;

    const start = new Date(b.slot_start);
    const end = new Date(b.slot_end);
    const dl = $('#summary');
    dl.innerHTML = '';
    addRow(dl, 'Service', b.service_name);
    addRow(dl, 'When', `${fmt.longDate(start)} at ${fmt.time(start)}–${fmt.time(end)}`);
    addRow(dl, 'Address', b.job_address);

    document.getElementById('meta-resched').textContent = `${b.reschedules_used} / ${b.reschedules_max}`;
    document.getElementById('meta-lead').textContent = `${b.lead_hours} hours`;

    // Gate actions on lead-time / reschedule count
    const rescheduleBtn = $('#btn-reschedule');
    const cancelBtn = $('#btn-cancel');
    const reschedulesLeft = b.reschedules_max - b.reschedules_used;
    if (!b.can_modify) {
      rescheduleBtn.disabled = true;
      cancelBtn.disabled = true;
      rescheduleBtn.title = `Within ${b.lead_hours}h of the booking — please contact Wes`;
      cancelBtn.title = rescheduleBtn.title;
    } else if (reschedulesLeft <= 0) {
      rescheduleBtn.disabled = true;
      rescheduleBtn.title = "You've used all your self-serve reschedules";
    }

    bindActions();
    showState('state-loaded');
  }

  function addRow(dl, label, value) {
    const wrap = document.createElement('div'); wrap.className = 'booking-row';
    const dt = document.createElement('dt'); dt.textContent = label;
    const dd = document.createElement('dd'); dd.textContent = value;
    wrap.appendChild(dt); wrap.appendChild(dd); dl.appendChild(wrap);
  }

  function bindActions() {
    $('#btn-reschedule').onclick = openReschedule;
    $('#btn-cancel').onclick = openCancel;
    $('#btn-reschedule-back').onclick = () => showPanel(null);
    $('#btn-cancel-back').onclick = () => showPanel(null);
    $('#btn-reschedule-confirm').onclick = doReschedule;
    $('#btn-cancel-confirm').onclick = doCancel;
  }

  function openCancel() {
    renderCancelReasons();
    showPanel('panel-cancel');
  }

  function renderCancelReasons() {
    const wrap = $('#reason-options');
    wrap.innerHTML = '';
    state.cancelReason = '';
    CANCEL_REASONS.forEach((label, idx) => {
      const id = `reason-${idx}`;
      const opt = document.createElement('label');
      opt.className = 'reason-opt';
      opt.htmlFor = id;
      opt.innerHTML =
        `<input type="radio" name="cancel-reason" id="${id}" value="${label.replace(/"/g, '&quot;')}">` +
        `<span>${label}</span>`;
      opt.querySelector('input').onchange = (e) => {
        document.querySelectorAll('.reason-opt').forEach((x) => x.classList.remove('selected'));
        opt.classList.add('selected');
        state.cancelReason = e.target.value;
      };
      wrap.appendChild(opt);
    });
  }

  // ─── Reschedule flow ───────────────────────────────────────────────────
  async function openReschedule() {
    showPanel('panel-reschedule');
    state.pickedSlot = null;
    $('#btn-reschedule-confirm').disabled = true;
    $('#reschedule-error').hidden = true;
    $('#reschedule-slots').innerHTML =
      '<div class="loading"><span class="spinner"></span> Loading available slots…</div>';
    try {
      state.slots = await apiGet('/availability?days=14');
      renderSlotPicker();
    } catch (e) {
      $('#reschedule-slots').innerHTML = '';
      $('#reschedule-error').textContent = e.message || 'Could not load slots';
      $('#reschedule-error').hidden = false;
    }
  }

  function renderSlotPicker() {
    const container = $('#reschedule-slots');
    container.innerHTML = '';

    if (!state.slots.length) {
      container.innerHTML =
        '<div class="info" style="margin: 0;">No slots available in the next 14 days. ' +
        'Try again later or message Wes.</div>';
      return;
    }

    // Group slots by date
    const byDay = new Map();
    state.slots.forEach((s) => {
      const d = new Date(s.start);
      const key = d.toISOString().slice(0, 10);
      if (!byDay.has(key)) byDay.set(key, { date: d, slots: [] });
      byDay.get(key).slots.push(s);
    });
    const days = [...byDay.values()];

    // Day strip
    const strip = document.createElement('div'); strip.className = 'day-strip';
    days.forEach((d, i) => {
      const pill = document.createElement('button');
      pill.type = 'button'; pill.className = 'day-pill';
      const p = fmt.dayPill(d.date);
      pill.innerHTML =
        `<span class="dow">${p.dow}</span>` +
        `<span class="date">${p.date}</span>` +
        `<span class="month">${p.month}</span>`;
      if (i === 0) pill.classList.add('selected');
      pill.onclick = () => {
        document.querySelectorAll('.day-pill').forEach((x) => x.classList.remove('selected'));
        pill.classList.add('selected');
        renderSlotsForDay(d);
      };
      strip.appendChild(pill);
    });
    container.appendChild(strip);

    const slotList = document.createElement('div');
    slotList.className = 'slot-list';
    slotList.id = 'reschedule-slot-list';
    container.appendChild(slotList);

    renderSlotsForDay(days[0]);
  }

  function renderSlotsForDay(day) {
    const list = $('#reschedule-slot-list');
    list.innerHTML = '';
    day.slots.forEach((s) => {
      const btn = document.createElement('button');
      btn.type = 'button'; btn.className = 'slot';
      const start = new Date(s.start);
      btn.textContent = fmt.time(start);
      btn.onclick = () => {
        document.querySelectorAll('.slot').forEach((x) => x.classList.remove('selected'));
        btn.classList.add('selected');
        state.pickedSlot = s;
        $('#btn-reschedule-confirm').disabled = false;
      };
      list.appendChild(btn);
    });
  }

  async function doReschedule() {
    if (!state.pickedSlot) return;
    const btn = $('#btn-reschedule-confirm');
    btn.disabled = true;
    btn.innerHTML = '<span class="spinner"></span> Saving…';
    $('#reschedule-error').hidden = true;
    try {
      const result = await apiPost('/reschedule', {
        slot_start: state.pickedSlot.start,
        slot_end: state.pickedSlot.end,
      });
      // Render the rescheduled-success state
      const dl = $('#rescheduled-summary');
      dl.innerHTML = '';
      const start = new Date(result.slot_start);
      const end = new Date(result.slot_end);
      addRow(dl, 'Service', result.service_name);
      addRow(dl, 'When', `${fmt.longDate(start)} at ${fmt.time(start)}–${fmt.time(end)}`);
      addRow(dl, 'Address', result.job_address);
      showState('state-rescheduled');

      // GA4 + Clarity events for measurement
      try { gtag('event', 'booking_rescheduled', { transaction_id: result.job_uuid }); } catch (e) {}
      try { clarity('event', 'booking_rescheduled'); } catch (e) {}
    } catch (e) {
      $('#reschedule-error').textContent = e.message || 'Could not reschedule. Please try again.';
      $('#reschedule-error').hidden = false;
      btn.disabled = false;
      btn.innerHTML = 'Confirm new time';
    }
  }

  // ─── Cancel flow ───────────────────────────────────────────────────────
  async function doCancel() {
    const btn = $('#btn-cancel-confirm');
    btn.disabled = true;
    btn.innerHTML = '<span class="spinner"></span> Cancelling…';
    $('#cancel-error').hidden = true;
    const reasonText = ($('#cancel-reason-text').value || '').trim();
    try {
      await apiPost('/cancel', {
        reason_category: state.cancelReason || '',
        reason_text: reasonText,
      });
      showState('state-cancelled');

      // Fire conversion events — include the reason category as a custom
      // dim so you can slice by it later.
      try {
        gtag('event', 'booking_cancelled', {
          transaction_id: state.booking.job_uuid,
          reason: state.cancelReason || 'Not given',
        });
      } catch (e) {}
      try { clarity('event', 'booking_cancelled'); } catch (e) {}
    } catch (e) {
      $('#cancel-error').textContent = e.message || 'Could not cancel. Please try again.';
      $('#cancel-error').hidden = false;
      btn.disabled = false;
      btn.innerHTML = 'Yes, cancel my booking';
    }
  }

  // ─── Go ────────────────────────────────────────────────────────────────
  document.addEventListener('DOMContentLoaded', boot);
})();
