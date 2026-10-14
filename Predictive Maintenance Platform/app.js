/* ══════════════════════════════════════════════════════════════════════════
   SENTINEL PdM — Application controller
   ──────────────────────────────────────────────────────────────────────────
   Organised as ES6 module-style namespaces inside one IIFE so the file works
   over file:// as well as through a dev server (native `type="module"` is
   blocked by CORS on file://). Each section below maps to what would be a
   separate module in a bundled build:

     CONFIG   → config.js
     API      → api/client.js          (Flask integration + mock fallback)
     MOCK     → mock/generator.js      (seed data + live fluctuation)
     STATE    → store.js
     UI       → ui/*.js               (renderers, one per view)
     TWIN     → twin.js               (model-viewer controls)
     BOOT     → main.js
   ══════════════════════════════════════════════════════════════════════════ */

(() => {
  'use strict';

  /* ════════════════════════════════════════════════════════════════════════
     CONFIG
     ════════════════════════════════════════════════════════════════════ */
  const CONFIG = Object.freeze({
    API_BASE: 'http://127.0.0.1:5000/api/v1/',
    REQUEST_TIMEOUT_MS: 2500,
    BACKEND_RETRY_MS: 30_000,      // circuit-breaker cool-down after a failure
    TELEMETRY_INTERVAL_MS: 3000,   // live sensor stream cadence
    ALERT_CHANCE: 0.28,            // p(new anomaly) per tick
    SPARK_POINTS: 24,              // rolling history length per channel
  });

  /* Sensor channel definitions — the AI4I-style 5-channel feature set.
     Temperatures are expressed in °C (the source dataset ships Kelvin; the
     baselines below are already converted). `safe` is the OEM-documented
     operating window used for threshold tinting. */
  const CHANNELS = Object.freeze([
    { key: 'airTemp',     label: 'Air Temperature',     unit: '°C',  icon: 'thermometer',   decimals: 1, safe: [22, 31] },
    { key: 'processTemp',  label: 'Process Temperature', unit: '°C',  icon: 'flame',         decimals: 1, safe: [32, 40] },
    { key: 'rotSpeed',     label: 'Rotational Speed',    unit: 'RPM', icon: 'fan',           decimals: 0, safe: [1200, 2400] },
    { key: 'torque',       label: 'Torque',              unit: 'Nm',  icon: 'move-3d',       decimals: 1, safe: [18, 62] },
    { key: 'toolWear',     label: 'Tool Wear',           unit: 'min', icon: 'hourglass',     decimals: 0, safe: [0, 200] },
  ]);

  /* Failure-mode taxonomy (AI4I 2020 predictive-maintenance labels). */
  const FAILURE_MODES = Object.freeze({
    OSF: { name: 'Overstrain Failure (OSF)', desc: 'Tool wear × torque product beyond the strain limit for this variant.' },
    HDF: { name: 'Heat Dissipation Failure (HDF)', desc: 'Air/process ΔT below 8.6 K while rotational speed stays under 1380 rpm.' },
    PWF: { name: 'Power Failure (PWF)', desc: 'Torque × angular velocity outside the 3.5–9 kW power envelope.' },
    TWF: { name: 'Tool Wear Failure (TWF)', desc: 'Cutting tool has passed its qualified replacement window.' },
    NONE:{ name: 'No Failure Predicted', desc: 'All channels tracking within the learned nominal manifold.' },
  });

  /* ════════════════════════════════════════════════════════════════════════
     MOCK — seed fleet + generators
     ════════════════════════════════════════════════════════════════════ */
  const MOCK = (() => {

    /** Seed fleet. `base` values anchor the live fluctuation walk. */
    const seedFleet = () => ([
      {
        id: 'CNC-LT-01', name: 'CNC Lathe #01', model: 'DMG-CTX-510', serial: 'SN-4471-A19',
        opType: 'H', line: 'Line A · Bay 4', hours: 18742, health: 34, status: 'Critical',
        base: { airTemp: 28.7, processTemp: 38.8, rotSpeed: 1312, torque: 58.4, toolWear: 214 },
        prediction: {
          probability: 87, mode: 'OSF', confidence: 0.94, sigma: 4.2, rul: '31 h',
          component: 'Drive Shaft Bearing', part: '#BRG-9942',
          shap: [
            { feature: 'Torque',              impact:  42 },
            { feature: 'Tool Wear',           impact:  30 },
            { feature: 'Process Temperature', impact:  14 },
            { feature: 'Rotational Speed',    impact: -9 },
            { feature: 'Air Temperature',     impact:   5 },
          ],
          narrative: 'Torque has held above 55 Nm for 6.2 h while tool wear crossed 200 min. ' +
                     'The wear × torque product now sits in the overstrain region the model learned ' +
                     'from 41 historical Type-H failures. Replace the drive shaft bearing before the ' +
                     'next production batch.',
        },
      },
      {
        id: 'PMP-WT-02', name: 'Industrial Water Pump #02', model: 'GRF-NK-125', serial: 'SN-2208-C04',
        opType: 'M', line: 'Utility · Pumphouse', hours: 26410, health: 68, status: 'Warning',
        base: { airTemp: 26.3, processTemp: 36.0, rotSpeed: 1486, torque: 44.7, toolWear: 118 },
        prediction: {
          probability: 41, mode: 'HDF', confidence: 0.81, sigma: 2.4, rul: '9 d',
          component: 'Hydraulic Manifold', part: '#HYD-2210',
          shap: [
            { feature: 'Process Temperature', impact:  26 },
            { feature: 'Air Temperature',     impact:  19 },
            { feature: 'Rotational Speed',    impact:  11 },
            { feature: 'Torque',              impact:  -6 },
            { feature: 'Tool Wear',           impact:   4 },
          ],
          narrative: 'Air/process ΔT has narrowed to 9.7 K over the last 12 h — cooling headroom is ' +
                     'shrinking faster than the seasonal baseline. Inspect the heat exchanger and ' +
                     'manifold seals at the next shift change.',
        },
      },
      {
        id: 'HYD-PR-03', name: 'Hydraulic Press #03', model: 'SCH-PH-200T', serial: 'SN-9931-B77',
        opType: 'H', line: 'Line B · Forming', hours: 11208, health: 91, status: 'Healthy',
        base: { airTemp: 24.9, processTemp: 34.4, rotSpeed: 1702, torque: 31.2, toolWear: 62 },
        prediction: {
          probability: 6, mode: 'NONE', confidence: 0.97, sigma: 0.6, rul: '> 90 d',
          component: 'Ram Cylinder Seal', part: '#SEL-3390',
          shap: [
            { feature: 'Torque',              impact: -18 },
            { feature: 'Tool Wear',           impact: -12 },
            { feature: 'Rotational Speed',    impact:  -8 },
            { feature: 'Process Temperature', impact:   5 },
            { feature: 'Air Temperature',     impact:   3 },
          ],
          narrative: 'All five channels sit inside the nominal manifold. Negative attributions on ' +
                     'torque and tool wear indicate the asset is actively de-risking after the ' +
                     'July seal service.',
        },
      },
      {
        id: 'CNV-BL-04', name: 'Conveyor Belt Drive #04', model: 'INT-CV-40M', serial: 'SN-1177-D21',
        opType: 'L', line: 'Line A · Transfer', hours: 34980, health: 88, status: 'Healthy',
        base: { airTemp: 24.4, processTemp: 33.7, rotSpeed: 2188, torque: 22.8, toolWear: 41 },
        prediction: {
          probability: 11, mode: 'NONE', confidence: 0.93, sigma: 1.1, rul: '> 60 d',
          component: 'Idler Roller Bank', part: '#IDL-5512',
          shap: [
            { feature: 'Rotational Speed',    impact:  14 },
            { feature: 'Torque',              impact:  -9 },
            { feature: 'Air Temperature',     impact:   6 },
            { feature: 'Tool Wear',           impact:  -5 },
            { feature: 'Process Temperature', impact:   2 },
          ],
          narrative: 'Slight positive attribution from sustained high belt speed, offset by low ' +
                     'torque draw. No intervention required this cycle.',
        },
      },
      {
        id: 'CMP-AR-05', name: 'Rotary Air Compressor #05', model: 'ATL-GA-75VSD', serial: 'SN-6604-E08',
        opType: 'M', line: 'Utility · Air Plant', hours: 41355, health: 61, status: 'Warning',
        base: { airTemp: 29.8, processTemp: 39.2, rotSpeed: 1394, torque: 51.6, toolWear: 156 },
        prediction: {
          probability: 54, mode: 'PWF', confidence: 0.86, sigma: 3.1, rul: '4 d',
          component: 'Screw Element Bearing', part: '#BRG-7781',
          shap: [
            { feature: 'Torque',              impact:  33 },
            { feature: 'Rotational Speed',    impact: -21 },
            { feature: 'Tool Wear',           impact:  16 },
            { feature: 'Process Temperature', impact:  10 },
            { feature: 'Air Temperature',     impact:   7 },
          ],
          narrative: 'Torque climbing while speed drops — the classic power-envelope excursion. ' +
                     'Computed shaft power is drifting toward the 3.5 kW lower bound. Schedule an ' +
                     'element inspection within 4 days.',
        },
      },
    ]);

    /** Bounded random walk: nudges a value and keeps it near `base`. */
    const walk = (current, base, volatility, drift = 0) => {
      const noise = (Math.random() - 0.5) * volatility * 2;
      const pull  = (base - current) * 0.14;          // mean reversion
      return current + noise + pull + drift;
    };

    /** One tick of the simulated sensor stream for a single machine. */
    const tickTelemetry = (machine) => {
      const t = machine.telemetry;
      const b = machine.base;
      const critical = machine.status === 'Critical';

      t.airTemp     = walk(t.airTemp,     b.airTemp,     0.35);
      t.processTemp = walk(t.processTemp, b.processTemp, 0.42, critical ? 0.05 : 0);
      t.rotSpeed    = walk(t.rotSpeed,    b.rotSpeed,    26);
      t.torque      = walk(t.torque,      b.torque,      1.9,  critical ? 0.08 : 0);

      // Tool wear is monotonic — it only accumulates until replacement. Healthy
      // assets get an automatic tool change at the limit; the critical asset
      // holds at the limit so its overstrain narrative stays true.
      t.toolWear += (critical ? 0.9 : 0.35) * (0.6 + Math.random() * 0.8);
      if (t.toolWear > machine.wearLimit) {
        if (critical) {
          t.toolWear = machine.wearLimit;
        } else {
          t.toolWear = b.toolWear * 0.18;
          machine.toolChanged = true;        // consumed by the live loop
        }
      }

      t.vibration = walk(t.vibration, critical ? 7.4 : 2.6, 0.22);
      t.acoustic  = walk(t.acoustic,  critical ? 88  : 74,  0.9);
      t.duty      = Math.min(100, Math.max(20, walk(t.duty, critical ? 94 : 71, 2.2)));

      CHANNELS.forEach(({ key }) => pushHistory(machine, key, t[key]));
      return t;
    };

    const pushHistory = (machine, key, value) => {
      const series = machine.history[key];
      series.push(value);
      if (series.length > CONFIG.SPARK_POINTS) series.shift();
    };

    /** Hydrates telemetry + history from the seed baseline. */
    const hydrate = (machine) => {
      machine.telemetry = {
        ...machine.base,
        vibration: machine.status === 'Critical' ? 7.4 : 2.6,
        acoustic:  machine.status === 'Critical' ? 88 : 74,
        duty:      machine.status === 'Critical' ? 94 : 71,
      };
      // Anchors for the live loop: health mean-reverts toward baseHealth minus
      // the current strain penalty, so assets stay inside their status band.
      machine.baseHealth = machine.health;
      machine.wearLimit  = Math.max(machine.base.toolWear * 1.2, 240);
      machine.toolChanged = false;

      machine.history = {};
      CHANNELS.forEach(({ key }) => {
        // Pre-fill the sparkline so trends are visible on first paint.
        machine.history[key] = Array.from({ length: CONFIG.SPARK_POINTS }, (_, i) => {
          const jitter = (Math.random() - 0.5) * Math.abs(machine.base[key]) * 0.012;
          const ramp   = key === 'toolWear' ? -(CONFIG.SPARK_POINTS - i) * 0.6 : 0;
          return machine.base[key] + jitter + ramp;
        });
      });
      return machine;
    };

    const seedAlerts = () => ([
      { id: 1, severity: 'Critical', machineId: 'CNC-LT-01', title: 'Overstrain signature detected',
        detail: 'Torque 58.4 Nm sustained with tool wear at 214 min.', action: 'Replace bearing #BRG-9942',
        ts: minutesAgo(2) },
      { id: 2, severity: 'Critical', machineId: 'CNC-LT-01', title: 'Vibration RMS above alarm band',
        detail: '7.4 mm/s vs 4.5 mm/s ISO 10816 zone C limit.', action: 'Reduce spindle load to 60%',
        ts: minutesAgo(11) },
      { id: 3, severity: 'Warning', machineId: 'CMP-AR-05', title: 'Shaft power drifting low',
        detail: 'Computed 3.71 kW — approaching the 3.5 kW floor.', action: 'Inspect screw element',
        ts: minutesAgo(24) },
      { id: 4, severity: 'Warning', machineId: 'PMP-WT-02', title: 'Cooling headroom narrowing',
        detail: 'Air/process ΔT down to 9.7 K over 12 h.', action: 'Flush heat exchanger',
        ts: minutesAgo(47) },
      { id: 5, severity: 'Info', machineId: 'HYD-PR-03', title: 'Baseline re-learned',
        detail: 'Post-service model recalibration completed.', action: 'No action required',
        ts: minutesAgo(96) },
    ]);

    /** Templates the live loop draws from when it emits a new anomaly. */
    const ANOMALY_TEMPLATES = [
      { severity: 'Warning',  title: 'Torque residual above 2σ',      detail: 'Isolation-forest score {s} on the torque channel.', action: 'Monitor next 3 cycles' },
      { severity: 'Warning',  title: 'Thermal gradient anomaly',      detail: 'ΔT slope {s}× the 24 h rolling median.',            action: 'Verify coolant flow' },
      { severity: 'Critical', title: 'Bearing envelope energy spike', detail: 'BPFO harmonic amplitude up {s}% in 10 min.',        action: 'Escalate to P1 work order' },
      { severity: 'Info',     title: 'Spindle speed step change',     detail: 'Setpoint changed by operator, score {s}.',          action: 'No action required' },
      { severity: 'Warning',  title: 'Tool wear crossed 85% of life', detail: 'Projected replacement in {s} operating hours.',     action: 'Stage replacement tool' },
    ];

    const nextAnomaly = (machines, nextId) => {
      const tpl = ANOMALY_TEMPLATES[Math.floor(Math.random() * ANOMALY_TEMPLATES.length)];
      // Bias anomaly generation toward already-degraded assets.
      const pool = machines.filter((m) => m.status !== 'Healthy');
      const target = (pool.length ? pool : machines)[Math.floor(Math.random() * (pool.length || machines.length))];
      const magnitude = (Math.random() * 3 + 1).toFixed(1);
      return {
        id: nextId,
        severity: tpl.severity,
        machineId: target.id,
        title: tpl.title,
        detail: tpl.detail.replace('{s}', magnitude),
        action: tpl.action,
        ts: new Date(),
      };
    };

    return { seedFleet, seedAlerts, hydrate, tickTelemetry, nextAnomaly };
  })();

  function minutesAgo(m) {
    return new Date(Date.now() - m * 60_000);
  }

  /* ════════════════════════════════════════════════════════════════════════
     API — Flask integration layer
     ──────────────────────────────────────────────────────────────────────
     Every call hits http://127.0.0.1:5000/api/v1/… first and silently falls
     back to the mock generator when the backend is unreachable, so the
     prototype is fully interactive standalone. Wire the real endpoints and
     the UI needs no changes.
     ════════════════════════════════════════════════════════════════════ */
  const API = (() => {
    let online = false;
    let circuitOpenUntil = 0;   // while in the future, skip the network entirely

    /** fetch + timeout wrapper. Resolves `null` on any failure.
     *  A simple circuit breaker keeps a disconnected backend from firing one
     *  failed request per machine per tick — after a failure the client waits
     *  CONFIG.BACKEND_RETRY_MS before probing again and serves mock data in
     *  the meantime. */
    const request = async (path, options = {}) => {
      if (Date.now() < circuitOpenUntil) return null;

      const controller = new AbortController();
      const timer = setTimeout(() => controller.abort(), CONFIG.REQUEST_TIMEOUT_MS);
      try {
        const res = await fetch(CONFIG.API_BASE + path, {
          headers: { 'Content-Type': 'application/json' },
          signal: controller.signal,
          ...options,
        });
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        circuitOpenUntil = 0;
        setOnline(true);
        return await res.json();
      } catch {
        circuitOpenUntil = Date.now() + CONFIG.BACKEND_RETRY_MS;
        setOnline(false);
        return null;                        // caller substitutes mock data
      } finally {
        clearTimeout(timer);
      }
    };

    const setOnline = (value) => {
      if (online === value) return;
      online = value;
      UI.renderApiBadge(value);
    };

    /* ── Public endpoint wrappers ──────────────────────────────────────── */

    /** GET /machines → fleet registry. */
    const fetchFleet = async () => {
      const data = await request('machines');
      return data?.machines ?? MOCK.seedFleet();
    };

    /** GET /machines/:id/telemetry → latest 5-channel sensor frame. */
    const fetchTelemetryData = async (machineId) => {
      const data = await request(`machines/${machineId}/telemetry`);
      const machine = STATE.getMachine(machineId);
      return data?.telemetry ?? MOCK.tickTelemetry(machine);
    };

    /** POST /predict → failure probability, mode class and SHAP vector. */
    const getAIPrediction = async (machineId) => {
      const machine = STATE.getMachine(machineId);
      const data = await request('predict', {
        method: 'POST',
        body: JSON.stringify({ machine_id: machineId, features: machine.telemetry }),
      });
      return data?.prediction ?? machine.prediction;
    };

    /** GET /alerts → anomaly feed. */
    const fetchAlerts = async () => {
      const data = await request('alerts');
      return data?.alerts ?? MOCK.seedAlerts();
    };

    /** GET /machines/:id/repair-plan → spec sheet + prescriptive steps. */
    const fetchRepairPlan = async (machineId) => {
      const data = await request(`machines/${machineId}/repair-plan`);
      return data?.plan ?? REPAIR.mockPlan();
    };

    /** POST /work-orders/:id/signoff → technician completion. */
    const submitSignoff = async (workOrderId, payload) => {
      const data = await request(`work-orders/${workOrderId}/signoff`, {
        method: 'POST',
        body: JSON.stringify(payload),
      });
      return data ?? { accepted: true, queued_offline: true };
    };

    return {
      fetchFleet, fetchTelemetryData, getAIPrediction, fetchAlerts,
      fetchRepairPlan, submitSignoff,
      get isOnline() { return online; },
    };
  })();

  /* ════════════════════════════════════════════════════════════════════════
     STATE
     ════════════════════════════════════════════════════════════════════ */
  const STATE = {
    view: 'fleet',
    machines: [],
    alerts: [],
    selectedId: null,
    statusFilter: 'all',
    searchTerm: '',
    checklist: [],
    alertSeq: 100,
    prevAvgHealth: null,

    getMachine(id) {
      return this.machines.find((m) => m.id === id) ?? this.machines[0];
    },
    get selected() {
      return this.getMachine(this.selectedId);
    },
    get visibleMachines() {
      const term = this.searchTerm.trim().toLowerCase();
      return this.machines.filter((m) => {
        const statusOk = this.statusFilter === 'all' || m.status === this.statusFilter;
        const searchOk = !term ||
          [m.id, m.name, m.serial, m.model, m.line].some((f) => f.toLowerCase().includes(term));
        return statusOk && searchOk;
      });
    },
  };

  /* ════════════════════════════════════════════════════════════════════════
     UTIL
     ════════════════════════════════════════════════════════════════════ */
  const $  = (sel, root = document) => root.querySelector(sel);
  const $$ = (sel, root = document) => [...root.querySelectorAll(sel)];

  const fmt = (value, decimals = 1) =>
    Number(value).toLocaleString('en-IN', { minimumFractionDigits: decimals, maximumFractionDigits: decimals });

  /** Maps a status string to its semantic token suffix. */
  const tone = (status) => ({ Critical: 'crit', Warning: 'warn', Healthy: 'ok', Info: 'probe' }[status] ?? 'probe');

  /** Derives status from a health score, keeping table + KPIs consistent. */
  const statusFromHealth = (health) =>
    health < 45 ? 'Critical' : health < 75 ? 'Warning' : 'Healthy';

  const relativeTime = (date) => {
    const secs = Math.floor((Date.now() - date.getTime()) / 1000);
    if (secs < 60) return `${secs}s ago`;
    if (secs < 3600) return `${Math.floor(secs / 60)}m ago`;
    if (secs < 86400) return `${Math.floor(secs / 3600)}h ago`;
    return `${Math.floor(secs / 86400)}d ago`;
  };

  const clockTime = (date) =>
    date.toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit', second: '2-digit' });

  /** Writes text and flashes the element when the value actually changed. */
  const setLive = (el, text) => {
    if (!el || el.textContent === String(text)) return;
    el.textContent = text;
    el.classList.remove('tick');
    void el.offsetWidth;                    // force reflow to restart animation
    el.classList.add('tick');
  };

  /** Re-scans the DOM for `data-lucide` placeholders. */
  const refreshIcons = () => window.lucide?.createIcons();

  /** Builds an SVG sparkline polyline from a numeric series. */
  const sparkline = (series, color) => {
    const min = Math.min(...series);
    const max = Math.max(...series);
    const span = max - min || 1;
    const points = series
      .map((v, i) => `${(i / (series.length - 1)) * 100},${26 - ((v - min) / span) * 22 - 2}`)
      .join(' ');
    return `<svg class="spark" viewBox="0 0 100 26" preserveAspectRatio="none" aria-hidden="true">
              <polyline points="${points}" stroke="${color}" />
            </svg>`;
  };

  /* ════════════════════════════════════════════════════════════════════════
     REPAIR — spec sheet + prescriptive checklist source data
     ════════════════════════════════════════════════════════════════════ */
  const REPAIR = (() => {
    const mockPlan = () => ({
      workOrderId: 'WO-2026-0814',
      specs: [
        { param: 'Bearing Designation',    spec: 'SKF 6208-2RS1 · Ø40×80×18', measured: '—',           state: 'na' },
        { param: 'Radial Internal Clearance', spec: '0.013 – 0.028 mm',       measured: '0.041 mm',    state: 'crit' },
        { param: 'Replacement Torque (bolts)', spec: '48 ± 2 Nm · cross pattern', measured: '—',       state: 'na' },
        { param: 'Shaft Interference Fit', spec: 'k5 · 0.002 – 0.015 mm',     measured: '0.009 mm',    state: 'ok' },
        { param: 'Operating Temp Limit',   spec: '≤ 110 °C outer race',       measured: '104 °C',      state: 'warn' },
        { param: 'Vibration Limit (ISO 10816)', spec: '≤ 4.5 mm/s RMS',       measured: '7.4 mm/s',    state: 'crit' },
        { param: 'Lubricant',              spec: 'LGHP 2 · 11 g per refill',  measured: 'Due',         state: 'warn' },
        { param: 'Max Rotational Speed',   spec: '≤ 2 400 RPM continuous',    measured: '1 312 RPM',   state: 'ok' },
      ],
      steps: [
        { title: 'Isolate and lock out power supply',
          note: 'Open the main disconnect, apply personal LOTO padlock, verify zero energy with a proving unit.',
          safety: true, est: '6 min' },
        { title: 'Depressurise hydraulic and pneumatic circuits',
          note: 'Bleed the accumulator to 0 bar and tag the line. Confirm on gauge HG-04.',
          safety: true, est: '8 min' },
        { title: 'Remove spindle guard and end cap',
          note: '6× M8 socket head. Retain shims in labelled tray — they set the axial preload.',
          safety: false, est: '12 min' },
        { title: 'Extract worn bearing #BRG-9942',
          note: 'Use hydraulic puller PLR-22. Never hammer the shaft — it work-hardens the seat.',
          safety: false, est: '18 min' },
        { title: 'Inspect and clean shaft seat',
          note: 'Check for fretting or ovality. Reject if runout exceeds 0.02 mm on the dial indicator.',
          safety: false, est: '10 min' },
        { title: 'Induction-heat and fit replacement bearing',
          note: 'Heat to 90 °C max, slide home against the shoulder, allow to shrink-fit before loading.',
          safety: false, est: '15 min' },
        { title: 'Lubricate drive shaft assembly',
          note: 'Inject 11 g LGHP 2 grease. Overfilling raises churning temperature — do not exceed.',
          safety: false, est: '5 min' },
        { title: 'Torque end cap bolts to 48 Nm',
          note: 'Cross pattern, two passes (50% then 100%). Calibrated wrench TW-118 only.',
          safety: false, est: '9 min' },
        { title: 'Restore power and run no-load verification',
          note: 'Remove LOTO, jog to 600 RPM, confirm vibration RMS below 4.5 mm/s before production.',
          safety: false, est: '20 min' },
        { title: 'Log work order and reset AI baseline',
          note: 'Close WO-2026-0814 and trigger model re-baseline so the new bearing sets a clean reference.',
          safety: false, est: '4 min' },
      ],
    });

    return { mockPlan };
  })();

  /* ════════════════════════════════════════════════════════════════════════
     UI — renderers
     ════════════════════════════════════════════════════════════════════ */
  const UI = {

    /* ── Header / global chrome ─────────────────────────────────────────── */
    renderApiBadge(online) {
      const badge = $('#api-badge');
      const text  = $('#api-badge-text');
      if (!badge) return;
      badge.classList.toggle('api-badge--live', online);
      badge.classList.toggle('api-badge--mock', !online);
      text.textContent = online ? 'FLASK LIVE' : 'MOCK STREAM';
      badge.querySelector('i')?.setAttribute('data-lucide', online ? 'plug-zap' : 'unplug');
      const source = $('#fleet-source');
      if (source) {
        source.textContent = online ? 'Flask API · 127.0.0.1:5000' : 'local mock generator';
        source.className = online ? 'text-ok' : 'text-warn';
      }
      refreshIcons();
    },

    renderHeader() {
      const critical = STATE.machines.filter((m) => m.status === 'Critical').length;
      const warning  = STATE.machines.filter((m) => m.status === 'Warning').length;

      setLive($('#hdr-machine-count'), STATE.machines.length);
      setLive($('#hdr-critical-count'), critical);
      setLive($('#bell-badge'), critical + warning);

      const pill = $('#plant-status');
      const text = $('#plant-status-text');
      const level = critical ? 'crit' : warning ? 'warn' : 'ok';
      pill.className = `status-pill status-pill--${level}`;
      text.textContent = critical
        ? `${critical} Critical Fault${critical > 1 ? 's' : ''}`
        : warning ? 'Degraded — Monitoring' : 'System Operational';
      pill.querySelector('.dot').className = 'dot dot--pulse';
    },

    /* ── View 1 · KPI cards ─────────────────────────────────────────────── */
    renderKPIs() {
      const list = STATE.machines;
      if (!list.length) return;

      const avgHealth = list.reduce((s, m) => s + m.health, 0) / list.length;
      const critical  = list.filter((m) => m.status === 'Critical');
      const totalHrs  = list.reduce((s, m) => s + m.hours, 0);
      const predicted = list.filter((m) => m.prediction.probability >= 40).length;

      setLive($('#kpi-health'), avgHealth.toFixed(1));
      $('#kpi-health-bar').style.width = `${avgHealth}%`;
      $('#kpi-health-bar').className =
        `track-fill bg-${avgHealth < 45 ? 'crit' : avgHealth < 75 ? 'warn' : 'ok'}`;

      // Delta vs the previous tick — gives the card a sense of direction.
      const delta = STATE.prevAvgHealth === null ? 0 : avgHealth - STATE.prevAvgHealth;
      const deltaEl = $('#kpi-health-delta');
      const dir = delta > 0.05 ? 'up' : delta < -0.05 ? 'down' : 'flat';
      deltaEl.className = `trend trend--${dir}`;
      deltaEl.textContent = `${dir === 'up' ? '▲' : dir === 'down' ? '▼' : '▬'} ${Math.abs(delta).toFixed(2)}%`;
      STATE.prevAvgHealth = avgHealth;

      setLive($('#kpi-critical'), critical.length);
      const worst = [...list].sort((a, b) => a.health - b.health)[0];
      setLive($('#kpi-critical-worst'), `${worst.id} · ${worst.health.toFixed(0)}%`);

      setLive($('#kpi-hours'), Math.round(totalHrs).toLocaleString('en-IN'));
      setLive($('#kpi-hours-avg'), Math.round(totalHrs / list.length).toLocaleString('en-IN'));
      setLive($('#kpi-predicted'), predicted);
      setLive($('#last-sync'), clockTime(new Date()));
    },

    /* ── View 1 · Fleet table ───────────────────────────────────────────── */
    renderFleetTable() {
      const tbody = $('#fleet-tbody');
      const rows = STATE.visibleMachines;

      tbody.innerHTML = rows.map((m) => {
        const t = tone(m.status);
        const healthColor = { crit: '#e11d48', warn: '#f59e0b', ok: '#10b981' }[t];
        return `
          <tr class="fleet-row ${m.id === STATE.selectedId ? 'is-selected' : ''}"
              data-machine="${m.id}" data-status="${m.status}">
            <td class="td font-mono text-xs font-bold text-probe">${m.id}</td>
            <td class="td">
              <p class="font-semibold text-slate-100">${m.name}</p>
              <p class="font-mono text-[10px] text-slate-500">${m.model} · ${m.line}</p>
            </td>
            <td class="td">
              <span class="rounded border border-hairline bg-void/60 px-1.5 py-0.5 font-mono text-[10px] font-bold text-slate-300">
                TYPE ${m.opType}
              </span>
            </td>
            <td class="td">
              <span class="status-pill status-pill--${t}"><span class="dot ${t === 'ok' ? '' : 'dot--pulse'}"></span>${m.status}</span>
            </td>
            <td class="td">
              <div class="flex items-center gap-2.5">
                <span class="w-10 shrink-0 font-mono text-sm font-bold text-white tabular-nums">${m.health.toFixed(0)}%</span>
                <div class="track"><div class="track-fill" style="width:${m.health}%;background:${healthColor}"></div></div>
              </div>
            </td>
            <td class="td font-mono text-[11px] leading-relaxed text-slate-400">
              <span class="text-slate-200">${fmt(m.telemetry.torque, 1)}</span> Nm ·
              <span class="text-slate-200">${fmt(m.telemetry.rotSpeed, 0)}</span> RPM<br />
              <span class="text-slate-200">${fmt(m.telemetry.processTemp, 1)}</span> °C proc ·
              wear <span class="text-slate-200">${fmt(m.telemetry.toolWear, 0)}</span> min
            </td>
            <td class="td text-right">
              <button class="btn btn--ghost !py-1.5 !text-xs" data-diagnose="${m.id}">
                <i data-lucide="stethoscope" class="h-3.5 w-3.5"></i> View Diagnostics
              </button>
            </td>
          </tr>`;
      }).join('') || `
        <tr><td colspan="7" class="td text-center text-sm text-slate-500">
          No assets match the current filter.
        </td></tr>`;

      $('#fleet-count').textContent =
        `Showing ${rows.length} of ${STATE.machines.length} assets · updated ${clockTime(new Date())}`;
      refreshIcons();
    },

    /* ── View 1 · Alert feed ────────────────────────────────────────────── */
    renderAlerts() {
      const feed = $('#alert-feed');
      if (!STATE.alerts.length) {
        feed.innerHTML = `<li class="px-4 py-10 text-center text-sm text-slate-500">
                            <p>Feed cleared.</p>
                            <p class="mt-1 font-mono text-[11px]">Listening for anomalies…</p>
                          </li>`;
        return;
      }

      feed.innerHTML = STATE.alerts.map((a) => {
        const t = tone(a.severity);
        return `
          <li class="alert-item text-${t}" data-alert-machine="${a.machineId}">
            <span class="alert-rail"></span>
            <div class="min-w-0 flex-1">
              <div class="flex items-baseline justify-between gap-2">
                <p class="truncate text-xs font-bold text-slate-100">${a.title}</p>
                <time class="shrink-0 font-mono text-[10px] text-slate-500">${relativeTime(a.ts)}</time>
              </div>
              <p class="mt-0.5 font-mono text-[10px] text-slate-500">${a.machineId} · ${clockTime(a.ts)}</p>
              <p class="mt-1 text-[11px] leading-relaxed text-slate-400">${a.detail}</p>
              <span class="alert-flag"><i data-lucide="arrow-right" class="h-2.5 w-2.5"></i>${a.action}</span>
            </div>
          </li>`;
      }).join('');
      refreshIcons();
    },

    /* ── View 2 · Machine header + switcher ─────────────────────────────── */
    renderDiagnosticHeader() {
      const m = STATE.selected;
      if (!m) return;
      const t = tone(m.status);

      $('#diag-name').textContent   = m.name;
      $('#diag-model').textContent  = m.model;
      $('#diag-serial').textContent = m.serial;
      $('#diag-line').textContent   = m.line;
      setLive($('#diag-hours'), Math.round(m.hours).toLocaleString('en-IN'));

      const pill = $('#diag-status');
      pill.className = `status-pill status-pill--${t}`;
      pill.innerHTML = `<span class="dot ${t === 'ok' ? '' : 'dot--pulse'}"></span><span>${m.status}</span>`;

      $('#nav-diag-machine').textContent = m.id;
      $('#nav-diag-machine').classList.remove('hidden');
      $('#repair-asset').textContent = `${m.id} — ${m.name}`;

      const select = $('#diag-select');
      if (select.options.length !== STATE.machines.length) {
        select.innerHTML = STATE.machines
          .map((x) => `<option value="${x.id}">${x.id} · ${x.name}</option>`).join('');
      }
      select.value = m.id;
    },

    /* ── View 2 · Column 1 · sensor cards ───────────────────────────────── */
    renderSensors() {
      const m = STATE.selected;
      if (!m) return;
      const grid = $('#sensor-grid');

      // Build the card shells once, then patch values on every tick so the
      // sparklines and DOM nodes aren't thrown away 20× a minute.
      if (grid.dataset.machine !== m.id) {
        grid.dataset.machine = m.id;
        grid.innerHTML = CHANNELS.map((c) => `
          <article class="sensor-card" data-channel="${c.key}">
            <header class="flex items-center justify-between gap-2">
              <span class="micro-label text-slate-400">${c.label}</span>
              <i data-lucide="${c.icon}" class="h-3.5 w-3.5 text-slate-500"></i>
            </header>
            <div class="mt-2 flex items-end justify-between gap-2">
              <p class="sensor-value" data-role="value">—<span class="ml-1 text-[11px] font-medium text-slate-500">${c.unit}</span></p>
              <p class="trend trend--flat" data-role="trend">▬ 0.0</p>
            </div>
            <div class="mt-1.5" data-role="spark"></div>
            <p class="mt-1 font-mono text-[9.5px] text-slate-600" data-role="safe">
              SAFE ${c.safe[0]}–${c.safe[1]} ${c.unit}
            </p>
          </article>`).join('');
        refreshIcons();
      }

      CHANNELS.forEach((c) => {
        const card    = grid.querySelector(`[data-channel="${c.key}"]`);
        const series  = m.history[c.key];
        const value   = m.telemetry[c.key];
        const prev    = series[series.length - 2] ?? value;
        const delta   = value - prev;
        const [lo, hi] = c.safe;

        // Threshold state drives the card border + value colour.
        const over  = value > hi || value < lo;
        const near  = !over && (value > hi - (hi - lo) * 0.08 || value < lo + (hi - lo) * 0.08);
        const state = over ? 'crit' : near ? 'warn' : 'ok';
        card.dataset.state = state;

        const valueEl = card.querySelector('[data-role="value"]');
        valueEl.innerHTML =
          `${fmt(value, c.decimals)}<span class="ml-1 text-[11px] font-medium text-slate-500">${c.unit}</span>`;
        valueEl.classList.toggle('text-crit', state === 'crit');
        valueEl.classList.toggle('text-warn', state === 'warn');
        valueEl.classList.toggle('text-white', state === 'ok');

        const trendEl = card.querySelector('[data-role="trend"]');
        const dir = delta > 0.01 ? 'up' : delta < -0.01 ? 'down' : 'flat';
        // Rising temperature/torque/wear is bad; rising speed is neutral-good.
        const goodWhenRising = c.key === 'rotSpeed';
        const trendClass = dir === 'flat' ? 'flat' : (dir === 'up') === goodWhenRising ? 'up' : 'down';
        trendEl.className = `trend trend--${trendClass}`;
        trendEl.textContent =
          `${dir === 'up' ? '▲' : dir === 'down' ? '▼' : '▬'} ${Math.abs(delta).toFixed(c.decimals || 1)}`;

        const strokeColor = { crit: '#e11d48', warn: '#f59e0b', ok: '#22d3ee' }[state];
        card.querySelector('[data-role="spark"]').innerHTML = sparkline(series, strokeColor);
      });

      setLive($('#duty-cycle'), m.telemetry.duty.toFixed(0));
      $('#duty-bar').style.width = `${m.telemetry.duty}%`;
      $('#duty-bar').className =
        `track-fill bg-${m.telemetry.duty > 90 ? 'crit' : m.telemetry.duty > 80 ? 'warn' : 'probe'}`;
      setLive($('#vib-rms'), fmt(m.telemetry.vibration, 2));
      setLive($('#acoustic'), fmt(m.telemetry.acoustic, 1));
    },

    /* ── View 2 · Column 3 · AI prognosis + SHAP ────────────────────────── */
    renderPrediction() {
      const m = STATE.selected;
      if (!m) return;
      const p = m.prediction;
      const t = p.probability >= 70 ? 'crit' : p.probability >= 35 ? 'warn' : 'ok';

      // Radial gauge: r=52 → circumference ≈ 326.7
      const CIRCUMFERENCE = 326.7;
      const arc = $('#gauge-arc');
      arc.style.strokeDashoffset = CIRCUMFERENCE * (1 - p.probability / 100);
      arc.className.baseVal = `text-${t} transition-[stroke-dashoffset] duration-700 ease-out`;

      $('#gauge-value').innerHTML =
        `${p.probability.toFixed(0)}<span class="text-xl text-slate-500">%</span>`;

      const band = $('#risk-band');
      band.className = `mt-3 font-semibold text-${t}`;
      band.textContent = p.probability >= 70 ? 'HIGH RISK — Immediate Action'
                        : p.probability >= 35 ? 'ELEVATED RISK — Schedule Service'
                        : 'LOW RISK — Nominal Operation';

      $('#rul-value').textContent = p.rul;

      const mode = FAILURE_MODES[p.mode] ?? FAILURE_MODES.NONE;
      const badge = $('#failure-mode');
      badge.className = `mode-badge mode-badge--${t}`;
      badge.querySelector('i')?.setAttribute('data-lucide',
        t === 'crit' ? 'alert-octagon' : t === 'warn' ? 'alert-triangle' : 'circle-check');
      $('#failure-mode-name').textContent = mode.name;
      $('#failure-mode-desc').textContent = mode.desc;

      setLive($('#pred-confidence'), `${(p.confidence * 100).toFixed(0)}%`);
      setLive($('#pred-sigma'), `${p.sigma.toFixed(1)}σ`);

      this.renderShap(p);
      $('#shap-narrative').textContent = p.narrative;
      $('#twin-focus').textContent = p.component;
      $('#twin-focus').className = `font-mono text-xs font-bold text-${t}`;
      refreshIcons();
    },

    renderShap(prediction) {
      const list = $('#shap-list');
      const scale = Math.max(...prediction.shap.map((f) => Math.abs(f.impact)));

      list.innerHTML = prediction.shap.map((f) => {
        const positive = f.impact >= 0;
        const width = (Math.abs(f.impact) / scale) * 50;   // 50% = half the axis
        return `
          <li class="shap-row">
            <div class="shap-meta">
              <span class="shap-feature">${f.feature}</span>
              <span class="shap-impact ${positive ? 'text-crit' : 'text-ok'}">
                ${positive ? '+' : '−'}${Math.abs(f.impact)}%
              </span>
            </div>
            <div class="shap-axis">
              <div class="shap-bar ${positive ? 'shap-bar--pos' : 'shap-bar--neg'}" style="width:${width}%"></div>
            </div>
          </li>`;
      }).join('');

      // Axis caption
      list.insertAdjacentHTML('beforeend', `
        <li class="flex justify-between pt-1 font-mono text-[9.5px] text-slate-600">
          <span>◀ reduces risk</span><span>increases risk ▶</span>
        </li>`);
    },

    /* ── View 3 · Spec sheet + checklist ────────────────────────────────── */
    renderRepair(plan) {
      const tbody = $('#spec-tbody');
      const label = { ok: 'In Spec', warn: 'Watch', crit: 'Out of Spec', na: '—' };

      tbody.innerHTML = plan.specs.map((s) => `
        <tr>
          <td class="td text-slate-300">${s.param}</td>
          <td class="td font-mono text-xs text-slate-400">${s.spec}</td>
          <td class="td font-mono text-xs font-bold ${
            s.state === 'crit' ? 'text-crit' : s.state === 'warn' ? 'text-warn' : 'text-slate-200'}">${s.measured}</td>
          <td class="td text-right">
            ${s.state === 'na'
              ? '<span class="font-mono text-xs text-slate-600">—</span>'
              : `<span class="status-pill status-pill--${s.state}"><span class="dot"></span>${label[s.state]}</span>`}
          </td>
        </tr>`).join('');

      // Checklist state persists across re-renders within a session.
      if (!STATE.checklist.length) {
        STATE.checklist = plan.steps.map((s) => ({ ...s, done: false }));
      }
      this.renderChecklist();
      refreshIcons();
    },

    /** Full build of the checklist. Use `syncChecklist` for state changes so
     *  toggling a step doesn't destroy the row the technician is tabbing through. */
    renderChecklist() {
      const ol = $('#checklist');
      ol.innerHTML = STATE.checklist.map((s, i) => `
          <li class="check-step" data-step="${i}">
            <button class="check-box" data-toggle="${i}" aria-pressed="false"
                    aria-label="Toggle step ${i + 1}">
              <i data-lucide="check" class="h-3.5 w-3.5"></i>
            </button>
            <div class="min-w-0 flex-1">
              <div class="flex items-baseline justify-between gap-3">
                <p class="check-title">
                  <span class="check-index">STEP ${String(i + 1).padStart(2, '0')}</span>
                  ${s.title}
                  ${s.safety ? '<span class="safety-tag"><i data-lucide="lock" class="h-2.5 w-2.5"></i>LOTO</span>' : ''}
                </p>
                <span class="shrink-0 font-mono text-[10px] text-slate-500">${s.est}</span>
              </div>
              <p class="check-note">${s.note}</p>
            </div>
          </li>`).join('');
      refreshIcons();
      this.syncChecklist();
    },

    /** Patches done/locked state and the progress bar without rebuilding rows. */
    syncChecklist() {
      const steps = STATE.checklist;
      // Steps 1–2 are safety-gated; everything after unlocks once both pass.
      const gateOpen = steps.slice(0, 2).every((s) => s.done);

      $$('#checklist .check-step').forEach((row, i) => {
        const step = steps[i];
        if (!step) return;
        row.classList.toggle('is-done', step.done);
        row.classList.toggle('is-locked', i > 1 && !gateOpen);
        row.querySelector('.check-box')?.setAttribute('aria-pressed', String(step.done));
      });

      const done = steps.filter((s) => s.done).length;
      $('#checklist-progress').textContent = `${done} / ${steps.length}`;
      $('#checklist-bar').style.width = `${steps.length ? (done / steps.length) * 100 : 0}%`;
    },

    /* ── Toasts ─────────────────────────────────────────────────────────── */
    toast(message, severity = 'Info') {
      const t = tone(severity);
      const icon = { crit: 'alert-octagon', warn: 'alert-triangle', ok: 'circle-check', probe: 'info' }[t];
      const el = document.createElement('div');
      el.className = 'toast pointer-events-auto';
      el.innerHTML = `<i data-lucide="${icon}" class="mt-0.5 h-4 w-4 shrink-0 text-${t}"></i>
                      <p class="leading-relaxed">${message}</p>`;
      $('#toast-host').prepend(el);
      refreshIcons();
      setTimeout(() => {
        el.classList.add('is-leaving');
        el.addEventListener('animationend', () => el.remove(), { once: true });
      }, 4200);
    },
  };

  /* ════════════════════════════════════════════════════════════════════════
     TWIN — 3D digital twin controls
     ════════════════════════════════════════════════════════════════════ */
  const TWIN = (() => {
    const viewer = () => $('#digital-twin');
    const stage  = () => $('#twin-stage');

    const init = () => {
      const mv = viewer();
      if (!mv) return;

      // Auto-rotate toggle
      $('#tw-rotate').addEventListener('click', (e) => {
        const on = mv.toggleAttribute('auto-rotate');
        e.currentTarget.classList.toggle('is-active', on);
      });

      // Hotspot visibility toggle
      $('#tw-hotspots').addEventListener('click', (e) => {
        const off = stage().classList.toggle('hotspots-off');
        e.currentTarget.classList.toggle('is-active', !off);
      });

      // Reset camera to the framed default
      $('#tw-reset').addEventListener('click', () => {
        mv.cameraOrbit = '28deg 78deg 3.2m';
        mv.fieldOfView = '32deg';
        mv.resetTurntableRotation?.();
        UI.toast('Camera reset to inspection framing.');
      });

      // Fullscreen
      $('#tw-full').addEventListener('click', () => {
        const el = stage();
        document.fullscreenElement ? document.exitFullscreen() : el.requestFullscreen?.();
      });

      // Clicking a hotspot pins its label and reports the component
      $$('.hotspot', mv).forEach((hs) => {
        hs.addEventListener('click', () => {
          $$('.hotspot', mv).forEach((o) => o !== hs && o.classList.remove('is-open'));
          const open = hs.classList.toggle('is-open');
          if (!open) return;
          const { component, part } = hs.dataset;
          $('#twin-focus').textContent = component;
          UI.toast(`Inspecting <b>${component}</b> — part ${part}.`,
                   hs.classList.contains('hotspot--crit') ? 'Critical'
                   : hs.classList.contains('hotspot--warn') ? 'Warning' : 'Healthy');
        });
      });

      // Progress bar for model download
      mv.addEventListener('progress', (e) => {
        const fill = $('.twin-progress-fill', mv);
        if (fill) fill.style.width = `${e.detail.totalProgress * 100}%`;
      });

      mv.addEventListener('load', () => UI.toast('Digital twin mesh loaded — 4 components annotated.', 'Healthy'));
    };

    /** Cosmetic HUD figures so the twin panel feels instrumented. */
    const tickHud = () => {
      setLive($('#twin-sync-latency'), (14 + Math.random() * 10).toFixed(0));
      setLive($('#twin-sync-fps'), (57 + Math.random() * 4).toFixed(0));
    };

    return { init, tickHud };
  })();

  /* ════════════════════════════════════════════════════════════════════════
     ROUTER — tab / view switching
     ════════════════════════════════════════════════════════════════════ */
  const ROUTER = {
    go(view) {
      if (!['fleet', 'diagnostic', 'repair'].includes(view)) return;
      STATE.view = view;

      $$('.view').forEach((section) => section.classList.toggle('hidden', section.dataset.view !== view));
      $$('.nav-tab').forEach((tab) => {
        const active = tab.dataset.view === view;
        tab.classList.toggle('is-active', active);
        active ? tab.setAttribute('aria-current', 'page') : tab.removeAttribute('aria-current');
      });

      // Render on entry so a freshly-shown view is never stale.
      if (view === 'fleet') { UI.renderKPIs(); UI.renderFleetTable(); UI.renderAlerts(); }
      if (view === 'diagnostic') { UI.renderDiagnosticHeader(); UI.renderSensors(); UI.renderPrediction(); }
      if (view === 'repair') { UI.renderDiagnosticHeader(); loadRepair(); }

      window.scrollTo({ top: 0, behavior: 'smooth' });
    },

    /** Selects a machine and jumps to its diagnostic page. */
    diagnose(machineId) {
      STATE.selectedId = machineId;
      STATE.checklist = [];                 // new asset → fresh work order
      this.go('diagnostic');
      UI.renderFleetTable();                // keep the row highlight in sync
    },
  };

  let repairLoaded = false;
  async function loadRepair() {
    // Re-fetch whenever the work order was reset by a machine change, not just
    // on first entry — otherwise the hub renders an empty checklist.
    if (repairLoaded && STATE.checklist.length) { UI.renderChecklist(); return; }
    const plan = await API.fetchRepairPlan(STATE.selectedId);
    UI.renderRepair(plan);
    repairLoaded = true;
  }

  /* ════════════════════════════════════════════════════════════════════════
     EVENTS
     ════════════════════════════════════════════════════════════════════ */
  function bindEvents() {

    // Delegated click handling for everything data-attribute driven.
    document.addEventListener('click', (e) => {
      const diagBtn = e.target.closest('[data-diagnose]');
      if (diagBtn) { e.stopPropagation(); ROUTER.diagnose(diagBtn.dataset.diagnose); return; }

      const row = e.target.closest('.fleet-row');
      if (row) { ROUTER.diagnose(row.dataset.machine); return; }

      const alertRow = e.target.closest('[data-alert-machine]');
      if (alertRow) { ROUTER.diagnose(alertRow.dataset.alertMachine); return; }

      const navEl = e.target.closest('[data-view]');
      if (navEl && !navEl.classList.contains('view')) { ROUTER.go(navEl.dataset.view); return; }

      const filterBtn = e.target.closest('[data-filter]');
      if (filterBtn) {
        STATE.statusFilter = filterBtn.dataset.filter;
        $$('[data-filter]').forEach((b) => b.classList.toggle('is-active', b === filterBtn));
        UI.renderFleetTable();
        return;
      }

      const toggle = e.target.closest('[data-toggle]');
      if (toggle) {
        const idx = Number(toggle.dataset.toggle);
        const step = STATE.checklist[idx];
        step.done = !step.done;

        // Un-checking a safety step re-locks everything downstream.
        if (idx < 2 && !step.done) {
          STATE.checklist.slice(2).forEach((s) => { s.done = false; });
        }
        UI.syncChecklist();

        if (idx === 1 && STATE.checklist[0].done && step.done) {
          UI.toast('LOTO verified — remaining steps unlocked.', 'Healthy');
        }
        if (STATE.checklist.every((s) => s.done)) {
          UI.toast('All steps complete. Ready for work-order sign-off.', 'Healthy');
        }
        return;
      }
    });

    // Search
    $('#fleet-search')?.addEventListener('input', (e) => {
      STATE.searchTerm = e.target.value;
      UI.renderFleetTable();
    });

    // Machine switcher on the diagnostic page
    $('#diag-select')?.addEventListener('change', (e) => {
      STATE.selectedId = e.target.value;
      STATE.checklist = [];
      repairLoaded = false;
      UI.renderDiagnosticHeader();
      UI.renderSensors();
      UI.renderPrediction();
    });

    // Clear alert feed
    $('#clear-alerts')?.addEventListener('click', () => {
      STATE.alerts = [];
      UI.renderAlerts();
      UI.renderHeader();
    });

    // Work-order sign-off
    $('#btn-signoff')?.addEventListener('click', async () => {
      const done = STATE.checklist.filter((s) => s.done).length;
      if (done < STATE.checklist.length) {
        UI.toast(`Cannot sign off — ${STATE.checklist.length - done} step(s) outstanding.`, 'Warning');
        return;
      }
      const res = await API.submitSignoff('WO-2026-0814', {
        machine_id: STATE.selectedId,
        technician: 'JG-4471',
        steps_completed: done,
      });
      UI.toast(res.queued_offline
        ? 'Sign-off queued locally — will sync when the Flask backend is reachable.'
        : 'Work order WO-2026-0814 signed off.', 'Healthy');
    });

    // Keyboard shortcuts: 1/2/3 switch views, / focuses search
    document.addEventListener('keydown', (e) => {
      if (e.target.matches('input, select, textarea')) {
        if (e.key === 'Escape') e.target.blur();
        return;
      }
      if (e.key === '/') { e.preventDefault(); $('#fleet-search')?.focus(); }
      if (e.key === '1') ROUTER.go('fleet');
      if (e.key === '2') ROUTER.go('diagnostic');
      if (e.key === '3') ROUTER.go('repair');
    });
  }

  /* ════════════════════════════════════════════════════════════════════════
     LIVE LOOP — simulated sensor stream
     ══════════════════════════════════════════════════════════════════════
     Every CONFIG.TELEMETRY_INTERVAL_MS the loop asks the API layer for a
     fresh frame per machine (falling back to the mock walk), recomputes
     health + prediction, then repaints only the active view.
     ════════════════════════════════════════════════════════════════════ */
  function startLiveLoop() {
    let busy = false;                        // prevents overlapping ticks

    const tick = async () => {
      if (busy) return;
      busy = true;
      try {
        // Fetch every channel frame concurrently so one slow endpoint can't
        // push a tick past its interval.
        await Promise.all(STATE.machines.map((m) => API.fetchTelemetryData(m.id)));

        for (const machine of STATE.machines) {
          // Strain penalty: how far torque and tool wear sit above their
          // baseline, bounded so a long demo can't drive every asset to zero.
          const torqueStrain = Math.max(0, machine.telemetry.torque / machine.base.torque - 1) * 40;
          const wearStrain   = Math.max(0, machine.telemetry.toolWear / machine.wearLimit) * 12;
          const penalty      = Math.min(18, torqueStrain + wearStrain);

          // Mean-revert toward (baseline − penalty) rather than integrating decay.
          const target = Math.min(99, Math.max(4, machine.baseHealth - penalty));
          machine.health += (target - machine.health) * 0.18 + (Math.random() - 0.5) * 0.5;
          machine.health = Math.min(99, Math.max(4, machine.health));
          machine.status = statusFromHealth(machine.health);
          machine.hours += 1 / 60;

          // Surface automatic tool changes emitted by the mock generator.
          if (machine.toolChanged) {
            machine.toolChanged = false;
            STATE.alerts.unshift({
              id: ++STATE.alertSeq, severity: 'Info', machineId: machine.id,
              title: 'Tool change completed',
              detail: `Wear counter reset after reaching the ${Math.round(machine.wearLimit)} min limit.`,
              action: 'No action required', ts: new Date(),
            });
          }

          // Keep the prediction gauge coupled to the live health score.
          const probTarget = Math.min(99, Math.max(2, 100 - machine.health + (Math.random() - 0.5) * 3));
          machine.prediction.probability += (probTarget - machine.prediction.probability) * 0.25;
        }

        // Occasionally emit a new anomaly into the feed.
        if (Math.random() < CONFIG.ALERT_CHANCE) {
          const alert = MOCK.nextAnomaly(STATE.machines, ++STATE.alertSeq);
          STATE.alerts.unshift(alert);
          if (alert.severity === 'Critical') {
            UI.toast(`<b>${alert.machineId}</b> — ${alert.title}`, 'Critical');
          }
        }
        STATE.alerts = STATE.alerts.slice(0, 40);

        UI.renderHeader();
        TWIN.tickHud();
        if (STATE.view === 'fleet') { UI.renderKPIs(); UI.renderFleetTable(); UI.renderAlerts(); }
        if (STATE.view === 'diagnostic') { UI.renderSensors(); UI.renderPrediction(); UI.renderDiagnosticHeader(); }
      } finally {
        busy = false;
      }
    };

    setInterval(tick, CONFIG.TELEMETRY_INTERVAL_MS);
  }

  /* ════════════════════════════════════════════════════════════════════════
     BOOT
     ════════════════════════════════════════════════════════════════════ */
  async function boot() {
    refreshIcons();
    UI.renderApiBadge(false);

    const [fleet, alerts] = await Promise.all([API.fetchFleet(), API.fetchAlerts()]);

    STATE.machines = fleet.map(MOCK.hydrate);
    STATE.alerts = alerts;
    // Land on the worst asset — that's what a technician opens the console for.
    STATE.selectedId = [...STATE.machines].sort((a, b) => a.health - b.health)[0].id;

    UI.renderHeader();
    UI.renderKPIs();
    UI.renderFleetTable();
    UI.renderAlerts();
    UI.renderDiagnosticHeader();

    bindEvents();
    TWIN.init();
    startLiveLoop();

    UI.toast('Mock telemetry stream active — Flask backend not detected.', 'Warning');
  }

  document.readyState === 'loading'
    ? document.addEventListener('DOMContentLoaded', boot)
    : boot();
})();
