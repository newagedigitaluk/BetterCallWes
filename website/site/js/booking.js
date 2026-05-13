/* Better Call Wes — booking form logic.
 * Talks to the FastAPI service at api.bettercallwes.co.uk.
 * Single source of truth for service/question wiring lives in services.json,
 * which the API returns enriched with live ServiceM8 prices.
 */
(function () {
  'use strict';

  const API_BASE = 'https://api.bettercallwes.co.uk';

  // ─── DOM helpers ─────────────────────────────────────────────────────────

  const $ = (sel) => document.querySelector(sel);
  const el = (tag, attrs, ...children) => {
    const node = document.createElement(tag);
    if (attrs) {
      for (const [k, v] of Object.entries(attrs)) {
        if (k === 'className') node.className = v;
        else if (k === 'dataset') Object.assign(node.dataset, v);
        else if (k.startsWith('on')) node.addEventListener(k.slice(2).toLowerCase(), v);
        else if (v === true) node.setAttribute(k, '');
        else if (v !== false && v != null) node.setAttribute(k, v);
      }
    }
    for (const c of children.flat()) {
      if (c == null) continue;
      node.appendChild(typeof c === 'string' ? document.createTextNode(c) : c);
    }
    return node;
  };

  const fmtGBP = (n) =>
    new Intl.NumberFormat('en-GB', { style: 'currency', currency: 'GBP', minimumFractionDigits: 0 }).format(n);

  // ─── UTM attribution capture ─────────────────────────────────────────────
  //
  // The inline <script> in every page's <head> handles first-touch
  // capture into sessionStorage. We just read it here.

  function captureUTM() {
    try {
      const cached = sessionStorage.getItem('bcw_utm');
      return cached ? JSON.parse(cached) : {};
    } catch (e) {
      return {};
    }
  }

  // ─── State ───────────────────────────────────────────────────────────────

  const state = {
    config: null,        // full /api/services response
    serviceSlug: null,   // which service the user picked
    answers: {},         // qid -> value (string | bool | number | array)
    slot: null,          // { start: Date, end: Date }
    customer: {},        // form values
    submitting: false,
  };

  // ─── Boot ────────────────────────────────────────────────────────────────

  async function boot() {
    try {
      const resp = await fetch(`${API_BASE}/api/services`);
      if (!resp.ok) throw new Error(`API responded ${resp.status}`);
      state.config = await resp.json();
    } catch (e) {
      $('#service-grid').innerHTML =
        '<div class="error">Sorry — the booking system is temporarily unavailable. ' +
        'Please <a href="https://wa.me/447700155655">WhatsApp Wes</a> or call 07700 155 655.</div>';
      console.error('Failed to load services:', e);
      return;
    }
    renderServicePicker();
    bindDetailsForm();
    bindSubmit();
    handleURLPreselect();
  }

  function handleURLPreselect() {
    const params = new URLSearchParams(window.location.search);
    const slug = params.get('service');
    if (slug && state.config.services[slug]) {
      selectService(slug);
    }
  }

  // ─── Step 1: service picker ──────────────────────────────────────────────

  function renderServicePicker() {
    const grid = $('#service-grid');
    grid.innerHTML = '';
    for (const [slug, svc] of Object.entries(state.config.services)) {
      const fromPrice = svc.base_material && svc.base_material.price
        ? `From ${fmtGBP(svc.base_material.price)}`
        : '';
      const card = el('button', {
        type: 'button',
        className: 'service-card',
        dataset: { slug },
        onclick: () => selectService(slug),
      },
        el('div', { className: 'name' }, svc.name),
        el('div', { className: 'desc' }, svc.short_description || ''),
        fromPrice ? el('div', { className: 'from' }, fromPrice) : null
      );
      grid.appendChild(card);
    }
  }

  function selectService(slug) {
    state.serviceSlug = slug;
    state.answers = {};
    state.slot = null;
    document.querySelectorAll('.service-card').forEach((c) => {
      c.classList.toggle('selected', c.dataset.slug === slug);
    });
    renderQuestions();
    unlockStep('step-questions');
    lockStep('step-slot');
    lockStep('step-details');
    lockStep('step-submit');
    updateTotal();
    scrollIntoView('#step-questions');
  }

  // ─── Step 2: questions ───────────────────────────────────────────────────

  function renderQuestions() {
    const svc = state.config.services[state.serviceSlug];
    const form = $('#questions-form');
    form.innerHTML = '';
    for (const q of svc.questions || []) {
      const wrap = el('div', {
        className: 'question',
        dataset: { qid: q.id },
      });
      wrap.appendChild(el('label', { className: 'q-label', for: `q-${q.id}` }, q.label));
      if (q.subtext) {
        wrap.appendChild(el('span', { className: 'q-sub' }, q.subtext));
      }
      wrap.appendChild(renderQuestionInput(q));
      form.appendChild(wrap);
    }
    applyConditionalVisibility();
    bindAnswerListeners();
    // Auto-set defaults for number questions
    for (const q of svc.questions || []) {
      if (q.type === 'number' && q.default != null) {
        state.answers[q.id] = q.default;
        const input = form.querySelector(`#q-${q.id}`);
        if (input) input.value = q.default;
      }
    }
    updateTotal();
    updateNextButtonForQuestions();
  }

  function renderQuestionInput(q) {
    if (q.type === 'radio') {
      const options = el('div', { className: 'options' });
      for (const opt of q.options || []) {
        const optLabel = el('label', { className: 'opt' },
          el('input', {
            type: 'radio',
            name: `q-${q.id}`,
            value: opt.value,
            required: q.required,
          }),
          el('span', { className: 'opt-label' }, opt.label),
          opt.material && opt.material.price ? el('span', { className: 'price-delta' }, `+${fmtGBP(deltaForOption(q, opt))}`) : null
        );
        options.appendChild(optLabel);
      }
      return options;
    }
    if (q.type === 'select') {
      const select = el('select', { id: `q-${q.id}`, name: `q-${q.id}`, required: q.required });
      select.appendChild(el('option', { value: '' }, 'Choose...'));
      for (const opt of q.options || []) {
        select.appendChild(el('option', { value: opt.value }, opt.label));
      }
      return select;
    }
    if (q.type === 'checkbox') {
      const wrap = el('label', { className: 'opt' },
        el('input', { type: 'checkbox', id: `q-${q.id}`, name: `q-${q.id}` }),
        el('span', { className: 'opt-label' }, q.label),
        q.material && q.material.price ? el('span', { className: 'price-delta' }, `+${fmtGBP(q.material.price)}`) : null
      );
      // Replace the standalone label (we already added q.label as q-label above) — only render the input + price
      wrap.querySelector('.opt-label').remove();
      return wrap;
    }
    if (q.type === 'checkbox-multi') {
      const options = el('div', { className: 'options' });
      for (const opt of q.options || []) {
        options.appendChild(el('label', { className: 'opt' },
          el('input', { type: 'checkbox', name: `q-${q.id}`, value: opt.value }),
          el('span', { className: 'opt-label' }, opt.label)
        ));
      }
      return options;
    }
    if (q.type === 'number') {
      return el('input', {
        type: 'number',
        id: `q-${q.id}`,
        name: `q-${q.id}`,
        min: q.min != null ? q.min : '',
        max: q.max != null ? q.max : '',
        value: q.default != null ? q.default : '',
        inputmode: 'numeric',
      });
    }
    if (q.type === 'text') {
      return el('input', { type: 'text', id: `q-${q.id}`, name: `q-${q.id}`, placeholder: q.placeholder || '' });
    }
    if (q.type === 'textarea') {
      return el('textarea', { id: `q-${q.id}`, name: `q-${q.id}`, placeholder: q.placeholder || '' });
    }
    if (q.type === 'file') {
      // File uploads not yet supported by booking API — render but ignore on submit.
      return el('input', { type: 'file', id: `q-${q.id}`, name: `q-${q.id}`, accept: q.accept || '*', multiple: q.multiple ? true : false });
    }
    return el('div', null, '(unsupported question type)');
  }

  function deltaForOption(q, opt) {
    // For radio options that swap a material vs the base, the delta is
    // (option's material price) - (base material price).
    const svc = state.config.services[state.serviceSlug];
    const basePrice = svc.base_material && svc.base_material.price ? svc.base_material.price : 0;
    const optPrice = opt.material && opt.material.price ? opt.material.price : 0;
    return Math.max(0, optPrice - basePrice);
  }

  function bindAnswerListeners() {
    const form = $('#questions-form');
    form.addEventListener('input', onAnswerChange);
    form.addEventListener('change', onAnswerChange);
    form.addEventListener('click', (e) => {
      // toggle visual "selected" state on labels for radio/checkbox
      if (e.target.matches('input[type="radio"], input[type="checkbox"]')) {
        const opt = e.target.closest('.opt');
        if (opt) {
          if (e.target.type === 'radio') {
            opt.parentElement.querySelectorAll('.opt').forEach((o) => o.classList.remove('selected'));
            opt.classList.add('selected');
          } else {
            opt.classList.toggle('selected', e.target.checked);
          }
        }
      }
    });
  }

  function onAnswerChange() {
    collectAnswers();
    applyConditionalVisibility();
    updateTotal();
    updateNextButtonForQuestions();
  }

  function collectAnswers() {
    const svc = state.config.services[state.serviceSlug];
    const form = $('#questions-form');
    for (const q of svc.questions || []) {
      const elements = form.querySelectorAll(`[name="q-${q.id}"]`);
      if (!elements.length) continue;
      if (q.type === 'radio') {
        const checked = form.querySelector(`input[name="q-${q.id}"]:checked`);
        state.answers[q.id] = checked ? checked.value : null;
      } else if (q.type === 'checkbox') {
        state.answers[q.id] = !!form.querySelector(`#q-${q.id}`).checked;
      } else if (q.type === 'checkbox-multi') {
        const vals = Array.from(form.querySelectorAll(`input[name="q-${q.id}"]:checked`)).map((i) => i.value);
        state.answers[q.id] = vals;
      } else if (q.type === 'number') {
        const v = form.querySelector(`#q-${q.id}`).value;
        state.answers[q.id] = v === '' ? null : Number(v);
      } else {
        state.answers[q.id] = form.querySelector(`#q-${q.id}`).value || null;
      }
    }
  }

  function applyConditionalVisibility() {
    const svc = state.config.services[state.serviceSlug];
    const form = $('#questions-form');
    for (const q of svc.questions || []) {
      const wrap = form.querySelector(`[data-qid="${q.id}"]`);
      if (!wrap) continue;
      if (q.show_if) {
        const shown = evalShowIf(q.show_if);
        wrap.style.display = shown ? '' : 'none';
        // Clear answer if hidden so it doesn't influence pricing
        if (!shown) {
          state.answers[q.id] = q.type === 'checkbox-multi' ? [] : null;
        }
      }
    }
  }

  function evalShowIf(cond) {
    const target = state.answers[cond.question];
    if (cond.equals != null) {
      if (typeof cond.equals === 'boolean') return Boolean(target) === cond.equals;
      return target === cond.equals;
    }
    if (cond.includes != null) {
      if (Array.isArray(target)) return target.includes(cond.includes);
      return false;
    }
    return true;
  }

  // ─── Running total ───────────────────────────────────────────────────────

  function computeTotal() {
    if (!state.serviceSlug) return 0;
    const svc = state.config.services[state.serviceSlug];
    let total = 0;
    let baseOverridden = false;

    // Walk questions and apply effects
    for (const q of svc.questions || []) {
      if (q.show_if && !evalShowIf(q.show_if)) continue;
      const ans = state.answers[q.id];

      if (q.type === 'radio' && Array.isArray(q.options)) {
        const picked = q.options.find((o) => o.value === ans);
        if (!picked) continue;
        // material_swap → replace base
        if (picked.material_swap && picked.material && picked.material.price != null) {
          total += picked.material.price;
          baseOverridden = true;
        }
        // material_add on radio option
        if (picked.material_add && picked.material && picked.material.price != null) {
          total += picked.material.price;
        }
      }

      if (q.type === 'checkbox' && ans === true) {
        if (q.material && q.material.price != null) total += q.material.price;
      }

      if (q.type === 'number' && typeof ans === 'number' && ans > 0) {
        // material_add (every unit)
        if (q.material_add && q.material && q.material.price != null) {
          total += q.material.price * ans;
        }
        // material_add_when_over (only units above threshold)
        if (q.material_add_when_over && q.material_add_when_over.material_info) {
          const cfg = q.material_add_when_over;
          if (ans > cfg.threshold) {
            total += cfg.material_info.price * (ans - cfg.threshold);
          }
        }
      }
    }

    // Base material (unless overridden by a radio swap)
    if (!baseOverridden && svc.base_material && svc.base_material.price != null) {
      total += svc.base_material.price;
    }

    // Always-add materials (e.g. Power Flush chemicals)
    if (Array.isArray(svc.always_add_material_info)) {
      for (const m of svc.always_add_material_info) {
        if (m && m.price != null) total += m.price;
      }
    }

    return Math.round(total * 100) / 100;
  }

  function updateTotal() {
    const total = computeTotal();
    $('#running-amount').textContent = fmtGBP(total);
    $('#running-total').hidden = !state.serviceSlug;
    $('#running-total').classList.toggle('show', !!state.serviceSlug);
  }

  // ─── Step gating ─────────────────────────────────────────────────────────

  function questionsAreValid() {
    const svc = state.config.services[state.serviceSlug];
    for (const q of svc.questions || []) {
      if (q.show_if && !evalShowIf(q.show_if)) continue;
      if (!q.required) continue;
      const a = state.answers[q.id];
      if (a == null || a === '' || (Array.isArray(a) && a.length === 0)) return false;
    }
    return true;
  }

  function updateNextButtonForQuestions() {
    // We don't render a literal Next button — instead, once required
    // questions are answered we unlock step 3 (slot picker) and scroll
    // to it. Re-check on every change.
    if (!questionsAreValid()) {
      lockStep('step-slot');
      return;
    }
    if ($('#step-slot').hasAttribute('hidden') || $('#step-slot').classList.contains('locked')) {
      unlockStep('step-slot');
      loadSlots();
    }
  }

  function lockStep(id) {
    const s = $(`#${id}`);
    s.classList.add('locked');
    s.hidden = true;
  }
  function unlockStep(id) {
    const s = $(`#${id}`);
    s.classList.remove('locked');
    s.hidden = false;
  }

  function scrollIntoView(sel) {
    const el = $(sel);
    if (el) el.scrollIntoView({ behavior: 'smooth', block: 'start' });
  }

  // ─── Step 3: slot picker ─────────────────────────────────────────────────

  async function loadSlots() {
    const area = $('#slot-area');
    area.innerHTML = '<div class="loading"><span class="spinner"></span> Loading availability&hellip;</div>';
    try {
      const url = `${API_BASE}/api/availability?service=${encodeURIComponent(state.serviceSlug)}&days=14`;
      const resp = await fetch(url);
      if (!resp.ok) throw new Error(`API ${resp.status}`);
      const slots = await resp.json();
      renderSlots(slots);
    } catch (e) {
      area.innerHTML =
        '<div class="error">Couldn\'t load availability. Please <a href="https://wa.me/447700155655">WhatsApp Wes</a> for a slot.</div>';
      console.error('availability failed:', e);
    }
  }

  function renderSlots(slots) {
    const area = $('#slot-area');
    area.innerHTML = '';
    if (!slots.length) {
      area.innerHTML = '<div class="slot-empty">No free slots in the next 14 days. <a href="https://wa.me/447700155655">WhatsApp Wes</a> to find a time.</div>';
      return;
    }

    // Detect whole-day mode (Power Flush — slots are 6+ hours)
    const firstDuration = slots[0].duration_min;
    const isWholeDay = firstDuration >= 360;

    if (isWholeDay) {
      // Render as a vertical list of days
      const wrap = el('div', { className: 'slot-list' });
      for (const s of slots) {
        const start = new Date(s.start);
        wrap.appendChild(el('button', {
          type: 'button',
          className: 'slot slot-whole-day',
          dataset: { start: s.start, end: s.end },
          onclick: (e) => selectSlot(e.currentTarget, s),
        }, formatDayLabel(start)));
      }
      area.appendChild(wrap);
      return;
    }

    // Hourly mode: group by day
    const byDay = new Map();
    for (const s of slots) {
      const dayKey = s.start.slice(0, 10);
      if (!byDay.has(dayKey)) byDay.set(dayKey, []);
      byDay.get(dayKey).push(s);
    }

    const days = Array.from(byDay.keys());
    const dayStrip = el('div', { className: 'day-strip' });
    for (const d of days) {
      const dt = new Date(d + 'T00:00:00');
      dayStrip.appendChild(el('button', {
        type: 'button',
        className: 'day-pill',
        dataset: { day: d },
        onclick: (e) => selectDay(d, byDay.get(d), e.currentTarget),
      },
        el('span', { className: 'dow' }, dt.toLocaleDateString('en-GB', { weekday: 'short' })),
        el('span', { className: 'date' }, String(dt.getDate())),
        el('span', { className: 'month' }, dt.toLocaleDateString('en-GB', { month: 'short' }))
      ));
    }
    area.appendChild(dayStrip);
    const slotList = el('div', { className: 'slot-list', id: 'slot-list' });
    area.appendChild(slotList);

    // Auto-select the first day
    if (days.length) {
      const firstPill = dayStrip.querySelector('.day-pill');
      selectDay(days[0], byDay.get(days[0]), firstPill);
    }
  }

  function selectDay(dayKey, daySlots, pillEl) {
    document.querySelectorAll('.day-pill').forEach((p) => p.classList.remove('selected'));
    pillEl.classList.add('selected');
    const list = $('#slot-list');
    list.innerHTML = '';
    for (const s of daySlots) {
      const start = new Date(s.start);
      list.appendChild(el('button', {
        type: 'button',
        className: 'slot',
        dataset: { start: s.start, end: s.end },
        onclick: (e) => selectSlot(e.currentTarget, s),
      }, start.toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit', hour12: false })));
    }
  }

  function selectSlot(btn, slot) {
    document.querySelectorAll('.slot').forEach((s) => s.classList.remove('selected'));
    btn.classList.add('selected');
    state.slot = { start: slot.start, end: slot.end };
    unlockStep('step-details');
    updateSummary();
    scrollIntoView('#step-details');
  }

  function formatDayLabel(d) {
    return d.toLocaleDateString('en-GB', { weekday: 'long', day: 'numeric', month: 'long' }) + ' — full day';
  }

  // ─── Step 4: details ─────────────────────────────────────────────────────

  function bindDetailsForm() {
    const form = $('#details-form');
    form.addEventListener('input', () => {
      collectCustomer();
      if (customerIsValid()) {
        unlockStep('step-submit');
        updateSummary();
      } else {
        lockStep('step-submit');
      }
    });
    // Also catch postcode focus-out to normalise
    $('#customer_postcode').addEventListener('blur', (e) => {
      e.target.value = e.target.value.toUpperCase().trim();
    });
  }

  function collectCustomer() {
    state.customer = {
      customer_name: $('#customer_name').value.trim(),
      customer_phone: $('#customer_phone').value.trim(),
      customer_email: $('#customer_email').value.trim(),
      customer_postcode: $('#customer_postcode').value.trim().toUpperCase(),
      customer_address: $('#customer_address').value.trim(),
    };
  }

  function customerIsValid() {
    const c = state.customer;
    return (
      c.customer_name && c.customer_name.length >= 2 &&
      c.customer_phone && c.customer_phone.length >= 7 &&
      c.customer_email && /^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(c.customer_email) &&
      c.customer_postcode && c.customer_postcode.length >= 5 &&
      c.customer_address && c.customer_address.length >= 8
    );
  }

  // ─── Step 5: summary + submit ────────────────────────────────────────────

  function updateSummary() {
    const svc = state.config.services[state.serviceSlug];
    const dl = $('#summary');
    dl.innerHTML = '';
    function add(term, def) {
      dl.appendChild(el('dt', null, term));
      dl.appendChild(el('dd', null, def));
    }
    add('Service', svc.name);
    if (state.slot) {
      const start = new Date(state.slot.start);
      const end = new Date(state.slot.end);
      const dayStr = start.toLocaleDateString('en-GB', { weekday: 'long', day: 'numeric', month: 'long' });
      const timeStr = `${start.toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit', hour12: false })} – ${end.toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit', hour12: false })}`;
      add('When', `${dayStr}, ${timeStr}`);
    }
    if (state.customer.customer_name) add('Name', state.customer.customer_name);
    if (state.customer.customer_phone) add('Phone', state.customer.customer_phone);
    if (state.customer.customer_email) add('Email', state.customer.customer_email);
    if (state.customer.customer_address) {
      add('Address', state.customer.customer_address + (state.customer.customer_postcode ? ', ' + state.customer.customer_postcode : ''));
    }
    const totalRow = el('div', { className: 'total-row' },
      el('span', null, 'Estimated total'),
      el('span', { className: 'amount' }, fmtGBP(computeTotal()))
    );
    dl.appendChild(totalRow);
  }

  function bindSubmit() {
    $('#submit-btn').addEventListener('click', submitBooking);
  }

  async function submitBooking() {
    if (state.submitting) return;
    if (!state.serviceSlug || !state.slot || !customerIsValid()) {
      showError('Please complete all the steps first.');
      return;
    }
    state.submitting = true;
    $('#submit-btn').disabled = true;
    $('#submit-btn').textContent = 'Booking...';

    const payload = {
      service: state.serviceSlug,
      answers: state.answers,
      slot_start: state.slot.start,
      slot_end: state.slot.end,
      ...state.customer,
      ...captureUTM(),  // {} when no UTM was ever seen; passed through to SM8 marketing custom fields
    };

    try {
      const resp = await fetch(`${API_BASE}/api/book`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });
      const data = await resp.json();
      if (!resp.ok) {
        const msg = data.detail || `Booking failed (status ${resp.status}).`;
        throw new Error(typeof msg === 'string' ? msg : 'Validation failed.');
      }
      // Success — redirect to thank-you page with key info in URL
      const params = new URLSearchParams({
        job: data.job_uuid || '',
        total: String(data.estimated_total || ''),
        service: state.serviceSlug,
        start: state.slot.start,
      });
      window.location.href = `/booking-confirmed.html?${params.toString()}`;
    } catch (e) {
      console.error('booking failed:', e);
      showError(e.message || 'Something went wrong. Please WhatsApp Wes on 07700 155 655.');
      state.submitting = false;
      $('#submit-btn').disabled = false;
      $('#submit-btn').innerHTML =
        '<i data-lucide="calendar-check" style="width:20px;height:20px;vertical-align:middle;margin-right:0.4rem;"></i> Confirm booking';
      if (window.lucide) window.lucide.createIcons();
    }
  }

  function showError(msg) {
    const e = $('#submit-error');
    e.textContent = msg;
    e.hidden = false;
    e.scrollIntoView({ behavior: 'smooth', block: 'center' });
  }

  // ─── Go ─────────────────────────────────────────────────────────────────

  document.addEventListener('DOMContentLoaded', boot);
})();
