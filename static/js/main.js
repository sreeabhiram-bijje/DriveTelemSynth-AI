/**
 * DriveTelemSynth AI 2.0
 * Multi-Vehicle Driving Simulation and Intelligent Insurance Analytics Platform
 */

(() => {
  "use strict";

  // -------------------------------------------------------------
  // Global Color Palette & Presets
  // -------------------------------------------------------------
  const VEHICLE_COLORS = ["#10b981", "#0ea5e9", "#f43f5e", "#a855f7", "#f59e0b"];
  const DEFAULT_PRESETS = [
    {
      vehicle_id: "VEH-001",
      vehicle_name: "Vehicle A (Eco Commuter)",
      vehicle_category: "Slow",
      target_speed: 35,
      driving_behaviour: "Safe",
      color: "#10b981",
    },
    {
      vehicle_id: "VEH-002",
      vehicle_name: "Vehicle B (Family SUV)",
      vehicle_category: "Medium",
      target_speed: 65,
      driving_behaviour: "Moderate",
      color: "#0ea5e9",
    },
    {
      vehicle_id: "VEH-003",
      vehicle_name: "Vehicle C (Express Coupe)",
      vehicle_category: "High",
      target_speed: 110,
      driving_behaviour: "Aggressive",
      color: "#f43f5e",
    },
    {
      vehicle_id: "VEH-004",
      vehicle_name: "Vehicle D (City Hatchback)",
      vehicle_category: "Slow",
      target_speed: 40,
      driving_behaviour: "Safe",
      color: "#a855f7",
    },
    {
      vehicle_id: "VEH-005",
      vehicle_name: "Vehicle E (Commercial Van)",
      vehicle_category: "Medium",
      target_speed: 75,
      driving_behaviour: "Moderate",
      color: "#f59e0b",
    },
  ];

  // Global State
  let activeVehicles = JSON.parse(JSON.stringify(DEFAULT_PRESETS.slice(0, 3)));
  let roadSpeedLimit = 80;
  let activeCharts = {};

  // -------------------------------------------------------------
  // Simulation Studio Engine
  // -------------------------------------------------------------
  const sim = {
    canvas: document.getElementById("simulation-canvas"),
    ctx: null,
    isRunning: false,
    isPaused: false,
    animFrameId: null,
    startTime: 0,
    elapsedMs: 0,
    lastFrameTime: 0,
    roadScrollX: 0,
    vehicles: [],

    init() {
      if (!this.canvas) return;
      this.ctx = this.canvas.getContext("2d");
      this.syncWithFleet(activeVehicles, roadSpeedLimit);
      this.bindControls();
      this.render();
    },

    syncWithFleet(fleetList, speedLimit) {
      this.vehicles = fleetList.map((v, idx) => ({
        id: v.vehicle_id,
        name: v.vehicle_name,
        category: v.vehicle_category,
        speed: Number(v.target_speed || v.average_speed || 50),
        color: v.color || VEHICLE_COLORS[idx % VEHICLE_COLORS.length],
        x: 40 + idx * 80,
        lane: idx,
      }));
      if (speedLimit) roadSpeedLimit = speedLimit;
      this.renderLegend();
      this.renderSpeedSliders();
      this.updateSummary();
      this.render();
    },

    bindControls() {
      const btnStart = document.getElementById("sim-btn-start");
      const btnPause = document.getElementById("sim-btn-pause");
      const btnResume = document.getElementById("sim-btn-resume");
      const btnReset = document.getElementById("sim-btn-reset");
      const btnSpeedsToggle = document.getElementById("sim-btn-speeds-toggle");
      const btnSync = document.getElementById("sim-btn-sync");
      const speedPanel = document.getElementById("sim-speed-panel");

      if (btnStart) btnStart.addEventListener("click", () => this.start());
      if (btnPause) btnPause.addEventListener("click", () => this.pause());
      if (btnResume) btnResume.addEventListener("click", () => this.resume());
      if (btnReset) btnReset.addEventListener("click", () => this.reset());

      if (btnSpeedsToggle) {
        btnSpeedsToggle.addEventListener("click", () => {
          speedPanel.hidden = !speedPanel.hidden;
        });
      }

      if (btnSync) {
        btnSync.addEventListener("click", () => {
          this.syncWithFleet(activeVehicles, roadSpeedLimit);
        });
      }
    },

    setStatus(status) {
      const pill = document.getElementById("sim-status-pill");
      const text = document.getElementById("sim-status-text");
      const btnStart = document.getElementById("sim-btn-start");
      const btnPause = document.getElementById("sim-btn-pause");
      const btnResume = document.getElementById("sim-btn-resume");

      pill.className = `sim-status-pill pill-${status.toLowerCase()}`;
      text.textContent = status.toUpperCase();

      if (status === "running") {
        btnStart.disabled = true;
        btnPause.disabled = false;
        btnResume.disabled = true;
      } else if (status === "paused") {
        btnStart.disabled = true;
        btnPause.disabled = true;
        btnResume.disabled = false;
      } else {
        btnStart.disabled = false;
        btnPause.disabled = true;
        btnResume.disabled = true;
      }
    },

    start() {
      if (this.isRunning) return;
      this.isRunning = true;
      this.isPaused = false;
      this.startTime = performance.now() - this.elapsedMs;
      this.lastFrameTime = performance.now();
      this.setStatus("running");
      this.loop(performance.now());
    },

    pause() {
      if (!this.isRunning || this.isPaused) return;
      this.isPaused = true;
      cancelAnimationFrame(this.animFrameId);
      this.setStatus("paused");
      this.updateSummary();
    },

    resume() {
      if (!this.isRunning || !this.isPaused) return;
      this.isPaused = false;
      this.lastFrameTime = performance.now();
      this.setStatus("running");
      this.loop(performance.now());
    },

    reset() {
      this.isRunning = false;
      this.isPaused = false;
      cancelAnimationFrame(this.animFrameId);
      this.elapsedMs = 0;
      this.startTime = 0;
      this.roadScrollX = 0;
      document.getElementById("sim-timer").textContent = "00:00.0";
      this.vehicles.forEach((v, idx) => {
        v.x = 40 + idx * 80;
      });
      this.setStatus("stopped");
      this.render();
      this.updateSummary();
    },

    loop(timestamp) {
      if (!this.isRunning || this.isPaused) return;

      const deltaMs = Math.min(timestamp - this.lastFrameTime, 100);
      this.lastFrameTime = timestamp;
      this.elapsedMs = timestamp - this.startTime;

      // Update timer UI (mm:ss.s)
      const totalSec = this.elapsedMs / 1000;
      const mins = Math.floor(totalSec / 60);
      const secs = (totalSec % 60).toFixed(1).padStart(4, "0");
      document.getElementById("sim-timer").textContent = `${String(mins).padStart(2, "0")}:${secs}`;

      // Move road markings based on reference speed
      const baseSpeedKmh = roadSpeedLimit || 80;
      this.roadScrollX = (this.roadScrollX + (baseSpeedKmh * deltaMs * 0.008)) % 60;

      // Update vehicles positions based on their relative speed
      const canvasWidth = this.canvas.width;
      this.vehicles.forEach((v) => {
        // Pixel velocity directly proportional to vehicle km/h speed
        const speedPixelsPerSec = (v.speed / 100) * 180;
        v.x += (speedPixelsPerSec * deltaMs) / 1000;

        // Wrap around smoothly
        if (v.x > canvasWidth + 70) {
          v.x = -80;
        }
      });

      this.render();
      this.animFrameId = requestAnimationFrame((t) => this.loop(t));
    },

    render() {
      const ctx = this.ctx;
      if (!ctx) return;
      const w = this.canvas.width;
      const h = this.canvas.height;
      const numLanes = Math.max(2, this.vehicles.length);
      const laneHeight = h / numLanes;

      // 1. Draw Asphalt Background
      ctx.fillStyle = "#151820";
      ctx.fillRect(0, 0, w, h);

      // 2. Draw Shoulders (Top & Bottom)
      ctx.fillStyle = "#1e293b";
      ctx.fillRect(0, 0, w, 8);
      ctx.fillRect(0, h - 8, w, 8);

      // Solid edge boundary lines
      ctx.strokeStyle = "#ffffff";
      ctx.lineWidth = 2.5;
      ctx.beginPath();
      ctx.moveTo(0, 8);
      ctx.lineTo(w, 8);
      ctx.moveTo(0, h - 8);
      ctx.lineTo(w, h - 8);
      ctx.stroke();

      // 3. Draw Dashed Lane Dividers with motion
      ctx.strokeStyle = "#cbd5e1";
      ctx.lineWidth = 2;
      ctx.setLineDash([26, 22]);
      ctx.lineDashOffset = -this.roadScrollX;

      for (let i = 1; i < numLanes; i++) {
        const y = i * laneHeight;
        ctx.beginPath();
        ctx.moveTo(0, y);
        ctx.lineTo(w, y);
        ctx.stroke();
      }
      ctx.setLineDash([]); // Reset line dash

      // 4. Draw Road Speed Limit Markers on pavement
      ctx.fillStyle = "rgba(255, 255, 255, 0.07)";
      ctx.font = "bold 26px 'JetBrains Mono', monospace";
      ctx.textAlign = "center";
      for (let xPos = 250 - this.roadScrollX * 3; xPos < w + 200; xPos += 450) {
        ctx.fillText(`LIMIT ${roadSpeedLimit}`, xPos, h / 2 + 8);
      }

      // 5. Draw Vehicles
      this.vehicles.forEach((v) => {
        const laneY = v.lane * laneHeight;
        const carY = laneY + laneHeight / 2;
        this.drawCar(ctx, v.x, carY, v.color, v.name, v.speed);
      });
    },

    drawCar(ctx, x, y, color, name, speed) {
      const carLen = 58;
      const carWid = 26;

      ctx.save();
      ctx.translate(x, y);

      // Headlight beams glow
      ctx.fillStyle = "rgba(254, 240, 138, 0.12)";
      ctx.beginPath();
      ctx.moveTo(carLen / 2, -10);
      ctx.lineTo(carLen / 2 + 55, -22);
      ctx.lineTo(carLen / 2 + 55, 22);
      ctx.lineTo(carLen / 2, 10);
      ctx.closePath();
      ctx.fill();

      // Taillight red glow
      ctx.fillStyle = "rgba(239, 68, 68, 0.22)";
      ctx.beginPath();
      ctx.arc(-carLen / 2 - 4, -8, 7, 0, Math.PI * 2);
      ctx.arc(-carLen / 2 - 4, 8, 7, 0, Math.PI * 2);
      ctx.fill();

      // Wheels (4 black rubber tires)
      ctx.fillStyle = "#020617";
      ctx.fillRect(-carLen / 2 + 7, -carWid / 2 - 3, 11, 4);
      ctx.fillRect(carLen / 2 - 18, -carWid / 2 - 3, 11, 4);
      ctx.fillRect(-carLen / 2 + 7, carWid / 2 - 1, 11, 4);
      ctx.fillRect(carLen / 2 - 18, carWid / 2 - 1, 11, 4);

      // Car Body Shadow
      ctx.shadowColor = "rgba(0,0,0,0.45)";
      ctx.shadowBlur = 8;
      ctx.shadowOffsetX = 1;
      ctx.shadowOffsetY = 3;

      // Car Main Body
      ctx.fillStyle = color;
      ctx.beginPath();
      ctx.roundRect(-carLen / 2, -carWid / 2, carLen, carWid, [6, 12, 12, 6]);
      ctx.fill();
      ctx.shadowColor = "transparent";

      // Roof / Cabin
      ctx.fillStyle = "#0f172a";
      ctx.beginPath();
      ctx.roundRect(-carLen / 2 + 13, -carWid / 2 + 3.5, 28, carWid - 7, [4, 7, 7, 4]);
      ctx.fill();

      // Windshield & Rear Windows
      ctx.fillStyle = "#38bdf8";
      ctx.fillRect(carLen / 2 - 20, -carWid / 2 + 5, 4, carWid - 10); // front
      ctx.fillStyle = "#1e293b";
      ctx.fillRect(-carLen / 2 + 15, -carWid / 2 + 5, 3, carWid - 10); // rear

      // Headlights (front right)
      ctx.fillStyle = "#fef08a";
      ctx.fillRect(carLen / 2 - 2, -carWid / 2 + 2, 2.5, 4);
      ctx.fillRect(carLen / 2 - 2, carWid / 2 - 6, 2.5, 4);

      // Taillights (rear left)
      ctx.fillStyle = "#ef4444";
      ctx.fillRect(-carLen / 2, -carWid / 2 + 2, 2.5, 4);
      ctx.fillRect(-carLen / 2, carWid / 2 - 6, 2.5, 4);

      // Speeding Indicator Aura (if exceeding road limit)
      if (speed > roadSpeedLimit) {
        ctx.strokeStyle = "#f43f5e";
        ctx.lineWidth = 1.5;
        ctx.strokeRect(-carLen / 2 - 2, -carWid / 2 - 2, carLen + 4, carWid + 4);
      }

      // Vehicle Tag Label & Speed drawn directly above vehicle
      ctx.fillStyle = "#f8fafc";
      ctx.font = "bold 9px 'DM Sans', sans-serif";
      ctx.textAlign = "center";
      ctx.fillText(`${name.split(" ")[0]} · ${speed} km/h`, 0, -carWid / 2 - 7);

      ctx.restore();
    },

    renderLegend() {
      const container = document.getElementById("sim-legend-container");
      if (!container) return;
      container.innerHTML = this.vehicles
        .map(
          (v) => `
        <div class="sim-legend-card">
          <span class="legend-car-icon" style="background:${v.color}"></span>
          <div class="legend-info">
            <strong>${v.name}</strong>
            <span>${v.category} Category · Lane ${v.lane + 1}</span>
          </div>
          <span class="legend-speed-badge">${v.speed} km/h</span>
        </div>
      `
        )
        .join("");
    },

    renderSpeedSliders() {
      const container = document.getElementById("sim-speed-sliders");
      if (!container) return;
      container.innerHTML = this.vehicles
        .map(
          (v, idx) => `
        <div class="speed-slider-item">
          <div class="speed-slider-label">
            <span style="color:${v.color}">● ${v.name}</span>
            <strong id="slider-val-${idx}">${v.speed} km/h</strong>
          </div>
          <input type="range" min="15" max="160" value="${v.speed}" data-idx="${idx}" class="sim-speed-range">
        </div>
      `
        )
        .join("");

      container.querySelectorAll(".sim-speed-range").forEach((input) => {
        input.addEventListener("input", (e) => {
          const idx = Number(e.target.dataset.idx);
          const newSpeed = Number(e.target.value);
          this.vehicles[idx].speed = newSpeed;
          document.getElementById(`slider-val-${idx}`).textContent = `${newSpeed} km/h`;
          this.renderLegend();
          this.updateSummary();
          this.render();
        });
      });
    },

    updateSummary() {
      if (!this.vehicles.length) return;
      const speeds = this.vehicles.map((v) => v.speed);
      const minSpeed = Math.min(...speeds);
      const maxSpeed = Math.max(...speeds);
      const fastestV = this.vehicles.find((v) => v.speed === maxSpeed);
      const slowestV = this.vehicles.find((v) => v.speed === minSpeed);
      const ratio = minSpeed > 0 ? (maxSpeed / minSpeed).toFixed(2) : "1.0";

      document.getElementById("sim-sum-limit").textContent = `${roadSpeedLimit} km/h`;
      document.getElementById("sim-sum-fastest").textContent = `${fastestV.name} (${maxSpeed} km/h)`;
      document.getElementById("sim-sum-slowest").textContent = `${slowestV.name} (${minSpeed} km/h)`;
      document.getElementById("sim-sum-ratio").textContent = `${ratio}x speed spread`;
    },
  };

  // -------------------------------------------------------------
  // Dynamic Vehicle Setup Form Rendering
  // -------------------------------------------------------------
  function renderVehicleSetupCards(numVehicles) {
    const grid = document.getElementById("vehicle-cards-grid");
    if (!grid) return;

    activeVehicles = DEFAULT_PRESETS.slice(0, numVehicles);

    grid.innerHTML = activeVehicles
      .map(
        (v, i) => `
      <div class="vehicle-setup-card" style="border-left-color:${v.color}">
        <div class="v-card-top">
          <span class="v-id-tag">${v.vehicle_id}</span>
          <span class="v-category-badge" style="color:${v.color}">${v.vehicle_category.toUpperCase()}</span>
        </div>
        <label class="field">
          <span class="field-label">Vehicle Name</span>
          <div class="input-wrap">
            <input type="text" id="v-name-${i}" value="${v.vehicle_name}" required>
          </div>
        </label>
        <div class="v-field-group">
          <label class="field">
            <span class="field-label">Category</span>
            <div class="select-wrap">
              <select id="v-cat-${i}">
                <option value="Slow" ${v.vehicle_category === "Slow" ? "selected" : ""}>Slow</option>
                <option value="Medium" ${v.vehicle_category === "Medium" ? "selected" : ""}>Medium</option>
                <option value="High" ${v.vehicle_category === "High" ? "selected" : ""}>High</option>
              </select>
              <span class="select-chevron">⌄</span>
            </div>
          </label>
          <label class="field">
            <span class="field-label">Target Speed (km/h)</span>
            <div class="input-wrap">
              <input type="number" id="v-speed-${i}" min="15" max="175" value="${v.target_speed}" required>
              <span class="input-suffix">km/h</span>
            </div>
          </label>
        </div>
        <label class="field">
          <span class="field-label">Driving Behaviour</span>
          <div class="select-wrap">
            <select id="v-behav-${i}">
              <option value="Safe" ${v.driving_behaviour === "Safe" ? "selected" : ""}>Safe (Defensive)</option>
              <option value="Moderate" ${v.driving_behaviour === "Moderate" ? "selected" : ""}>Moderate (Mixed)</option>
              <option value="Aggressive" ${v.driving_behaviour === "Aggressive" ? "selected" : ""}>Aggressive (Fast/Spur)</option>
            </select>
            <span class="select-chevron">⌄</span>
          </div>
        </label>
      </div>
    `
      )
      .join("");

    sim.syncWithFleet(activeVehicles, roadSpeedLimit);
  }

  // -------------------------------------------------------------
  // Chart.js Visualizations Manager
  // -------------------------------------------------------------
  function destroyCharts() {
    Object.values(activeCharts).forEach((chart) => {
      if (chart && typeof chart.destroy === "function") chart.destroy();
    });
    activeCharts = {};
  }

  function renderComparativeCharts(vehicles, fleetSummary, roadLimit) {
    destroyCharts();

    const vNames = vehicles.map((v) => v.vehicle_name.split(" ")[0]);
    const vColors = vehicles.map((v) => v.color || "#0ea5e9");
    const riskScores = vehicles.map((v) => v.risk_score);
    const avgSpeeds = vehicles.map((v) => v.average_speed);
    const harshBraking = vehicles.map((v) => v.harsh_braking_events);
    const harshAccel = vehicles.map((v) => v.harsh_acceleration_events);
    const premiums = vehicles.map((v) => v.final_simulated_premium);

    // Chart 1: Average Speed vs Limit
    activeCharts.speed = new Chart(document.getElementById("chart-avg-speed"), {
      type: "bar",
      data: {
        labels: vNames,
        datasets: [
          {
            label: "Average Speed",
            data: avgSpeeds,
            backgroundColor: vColors,
            borderRadius: 5,
            barThickness: 24,
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { display: false },
          tooltip: {
            callbacks: {
              afterLabel: (ctx) => `Road Speed Limit: ${roadLimit} km/h`,
            },
          },
        },
        scales: {
          y: {
            beginAtZero: true,
            grid: { color: "#1e2e44" },
            ticks: { color: "#94a3b8", font: { size: 9 } },
          },
          x: { grid: { display: false }, ticks: { color: "#cbd5e1", font: { size: 9.5 } } },
        },
      },
    });

    // Chart 2: Risk Scores Comparison
    activeCharts.risk = new Chart(document.getElementById("chart-risk-scores"), {
      type: "bar",
      data: {
        labels: vNames,
        datasets: [
          {
            label: "Risk Score",
            data: riskScores,
            backgroundColor: riskScores.map((s) => (s < 35 ? "#10b981" : s < 65 ? "#f59e0b" : "#f43f5e")),
            borderRadius: 5,
            barThickness: 24,
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { display: false } },
        scales: {
          y: {
            beginAtZero: true,
            max: 100,
            grid: { color: "#1e2e44" },
            ticks: { color: "#94a3b8", font: { size: 9 } },
          },
          x: { grid: { display: false }, ticks: { color: "#cbd5e1", font: { size: 9.5 } } },
        },
      },
    });

    // Chart 3: Simulated Insurance Premium
    activeCharts.premium = new Chart(document.getElementById("chart-premiums"), {
      type: "bar",
      data: {
        labels: vNames,
        datasets: [
          {
            label: "Simulated Premium (₹)",
            data: premiums,
            backgroundColor: ["#38bdf8", "#818cf8", "#f472b6", "#c084fc", "#fbbf24"].slice(0, vNames.length),
            borderRadius: 5,
            barThickness: 24,
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { display: false },
          tooltip: {
            callbacks: {
              label: (ctx) => `₹${ctx.raw.toLocaleString()} (Base: ₹${fleetSummary.base_premium.toLocaleString()})`,
            },
          },
        },
        scales: {
          y: {
            beginAtZero: true,
            grid: { color: "#1e2e44" },
            ticks: { color: "#94a3b8", font: { size: 9 } },
          },
          x: { grid: { display: false }, ticks: { color: "#cbd5e1", font: { size: 9.5 } } },
        },
      },
    });

    // Chart 4: Harsh Driving Events (Braking vs Acceleration)
    activeCharts.events = new Chart(document.getElementById("chart-events-compare"), {
      type: "bar",
      data: {
        labels: vNames,
        datasets: [
          {
            label: "Harsh Accel / Trip",
            data: harshAccel,
            backgroundColor: "#38bdf8",
            borderRadius: 4,
            barThickness: 12,
          },
          {
            label: "Harsh Braking / Trip",
            data: harshBraking,
            backgroundColor: "#f43f5e",
            borderRadius: 4,
            barThickness: 12,
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            labels: { color: "#94a3b8", font: { size: 9 } },
          },
        },
        scales: {
          y: {
            beginAtZero: true,
            grid: { color: "#1e2e44" },
            ticks: { color: "#94a3b8", font: { size: 9 } },
          },
          x: { grid: { display: false }, ticks: { color: "#cbd5e1", font: { size: 9.5 } } },
        },
      },
    });

    // Chart 5: Fleet Risk Tier Distribution Doughnut
    activeCharts.dist = new Chart(document.getElementById("chart-fleet-distribution"), {
      type: "doughnut",
      data: {
        labels: ["Low Risk (<35)", "Medium Risk (35-64)", "High Risk (65+)"],
        datasets: [
          {
            data: [
              fleetSummary.low_risk_vehicles,
              fleetSummary.medium_risk_vehicles,
              fleetSummary.high_risk_vehicles,
            ],
            backgroundColor: ["#10b981", "#f59e0b", "#f43f5e"],
            borderColor: "#111d30",
            borderWidth: 3,
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        cutout: "68%",
        plugins: {
          legend: { position: "bottom", labels: { color: "#94a3b8", font: { size: 9 } } },
        },
      },
    });

    // Chart 6: Multi-Axis Radar Profile
    activeCharts.radar = new Chart(document.getElementById("chart-behaviour-radar"), {
      type: "radar",
      data: {
        labels: ["Speed Index", "Harsh Braking", "Harsh Accel", "Night Drive", "Speeding"],
        datasets: vehicles.map((v) => ({
          label: v.vehicle_name.split(" ")[0],
          data: [
            Math.min(100, (v.average_speed / 130) * 100),
            Math.min(100, v.harsh_braking_events * 25),
            Math.min(100, v.harsh_acceleration_events * 25),
            v.night_driving_ratio * 100,
            v.speeding_ratio * 100,
          ],
          borderColor: v.color || "#0ea5e9",
          backgroundColor: `${v.color || "#0ea5e9"}25`,
          borderWidth: 2,
        })),
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { labels: { color: "#94a3b8", font: { size: 8.5 } } },
        },
        scales: {
          r: {
            grid: { color: "#1e2e44" },
            angleLines: { color: "#1e2e44" },
            pointLabels: { color: "#cbd5e1", font: { size: 9 } },
            ticks: { display: false, max: 100 },
          },
        },
      },
    });
  }

  // -------------------------------------------------------------
  // Render Comparison Table, Insurance, Recommendations & Previews
  // -------------------------------------------------------------
  function renderComparisonTable(rankings) {
    const tbody = document.getElementById("comparison-body");
    if (!tbody) return;
    tbody.replaceChildren();

    rankings.forEach((v) => {
      const tr = document.createElement("tr");
      const rankMedal = v.safety_rank === 1 ? "🥇 #1" : v.safety_rank === 2 ? "🥈 #2" : v.safety_rank === 3 ? "🥉 #3" : `#${v.safety_rank}`;
      const riskClass = v.risk_classification.toLowerCase();

      tr.innerHTML = `
        <td class="rank-badge">${rankMedal}</td>
        <td><strong style="color:${v.color}">● ${v.vehicle_name}</strong> <small class="id-cell">(${v.vehicle_id})</small></td>
        <td>${v.vehicle_category}</td>
        <td><strong>${v.average_speed}</strong> km/h</td>
        <td>${v.maximum_speed} km/h</td>
        <td>${v.total_distance.toLocaleString()} km</td>
        <td>${v.harsh_braking_events}</td>
        <td>${v.harsh_acceleration_events}</td>
        <td>${(v.speeding_ratio * 100).toFixed(1)}%</td>
        <td>${(v.night_driving_ratio * 100).toFixed(1)}%</td>
        <td><strong>${v.risk_score}</strong>/100</td>
        <td><span class="risk-pill risk-${riskClass}">${v.risk_classification}</span></td>
        <td><span class="ins-tier-badge tier-${v.status_tag}">${v.insurance_category}</span></td>
        <td><strong>₹${v.final_simulated_premium.toLocaleString()}</strong> <small class="text-mint">(-${v.discount_percentage}%)</small></td>
      `;
      tbody.appendChild(tr);
    });
  }

  function renderBestDriverAnalysis(analysis) {
    if (!analysis) return;
    document.getElementById("best-driver-name").textContent = `${analysis.safest_vehicle_name} (${analysis.safest_vehicle_id})`;
    document.getElementById("best-driver-score-pill").textContent = `Risk Score: ${analysis.safest_risk_score}/100`;
    document.getElementById("best-driver-reason").textContent = analysis.safety_reason;
    document.getElementById("best-driver-ins-tier").textContent = analysis.best_insurance_category;
    document.getElementById("highest-risk-vehicle-tag").textContent = `${analysis.highest_risk_vehicle_name} (${analysis.highest_risk_score}/100)`;
    document.getElementById("best-driver-discount").textContent = `20% Safe-Driving Discount`;
  }

  function renderInsuranceCards(vehicles) {
    const container = document.getElementById("insurance-cards-grid");
    if (!container) return;
    container.innerHTML = vehicles
      .map(
        (v) => `
      <div class="insurance-card" style="border-top-color:${v.status_color}">
        <div class="ins-top">
          <div>
            <div class="ins-v-name" style="color:${v.color}">● ${v.vehicle_name}</div>
            <div class="ins-v-id">${v.vehicle_id} · ${v.vehicle_category} Category</div>
          </div>
          <span class="ins-tier-badge tier-${v.status_tag}">${v.insurance_category}</span>
        </div>

        <div class="ins-pricing-box">
          <div class="price-row"><span>Base Premium:</span> <strong>₹${v.base_premium.toLocaleString()}</strong></div>
          <div class="price-row"><span>Safe Driver Discount:</span> <strong style="color:${v.status_color}">-${v.discount_percentage}% (₹${v.discount_amount.toLocaleString()})</strong></div>
          <div class="price-row final"><span>Simulated Premium:</span> <strong style="color:#f8fafc">₹${v.final_simulated_premium.toLocaleString()}</strong></div>
        </div>

        <p class="ins-explanation">${v.decision_explanation}</p>
      </div>
    `
      )
      .join("");
  }

  function renderRecommendations(vehicles) {
    const container = document.getElementById("recommendations-container");
    if (!container) return;
    container.innerHTML = vehicles
      .map(
        (v) => `
      <div class="rec-card">
        <div class="rec-v-header">
          <strong style="color:${v.color}">● ${v.vehicle_name}</strong>
          <span class="v-id-tag">Risk: ${v.risk_score}/100</span>
        </div>
        ${v.recommendations
          .map(
            (r) => `
          <div class="rec-item">
            <span class="rec-badge ${r.severity}">${r.category.toUpperCase()}</span>
            <div class="rec-text">${r.recommendation}</div>
          </div>
        `
          )
          .join("")}
      </div>
    `
      )
      .join("");
  }

  function renderTripPreview(previewTrips) {
    const tbody = document.getElementById("mv-preview-body");
    if (!tbody) return;
    tbody.replaceChildren();

    previewTrips.forEach((row) => {
      const tr = document.createElement("tr");
      tr.innerHTML = `
        <td class="id-cell">${row.vehicle_id}</td>
        <td>${row.vehicle_name || row.vehicle_id}</td>
        <td class="id-cell">${row.trip_id}</td>
        <td class="id-cell">${row.driver_id}</td>
        <td>${row.distance_km}</td>
        <td>${row.duration_minutes}</td>
        <td>${row.average_speed_kmh}</td>
        <td>${row.maximum_speed_kmh}</td>
        <td>${row.harsh_acceleration_count}</td>
        <td>${row.harsh_braking_count}</td>
        <td>${(row.speeding_ratio * 100).toFixed(1)}%</td>
        <td>${(row.night_driving_ratio * 100).toFixed(1)}%</td>
        <td><strong>${row.risk_score}</strong></td>
        <td><span class="risk-pill risk-${row.risk_label.toLowerCase()}">${row.risk_label}</span></td>
      `;
      tbody.appendChild(tr);
    });

    document.getElementById("mv-preview-count").textContent = `Showing ${previewTrips.length} preview records`;
  }

  function updateOverviewKpis(fleetSummary) {
    document.getElementById("kpi-total-vehicles").textContent = fleetSummary.total_vehicles;
    document.getElementById("kpi-total-trips").textContent = `Total synthetic trips: ${fleetSummary.total_records.toLocaleString()}`;
    document.getElementById("kpi-fleet-risk").textContent = fleetSummary.fleet_average_risk;
    document.getElementById("kpi-preferred-count").textContent = fleetSummary.preferred_insurance_count;
    document.getElementById("kpi-risk-split").textContent = `${fleetSummary.low_risk_vehicles} / ${fleetSummary.medium_risk_vehicles} / ${fleetSummary.high_risk_vehicles}`;
    document.getElementById("mv-result-meta").textContent = `Road Limit: ${fleetSummary.road_speed_limit} km/h · Base: ₹${fleetSummary.base_premium.toLocaleString()}`;
  }

  // -------------------------------------------------------------
  // Form Submission & API Integration
  // -------------------------------------------------------------
  const mvForm = document.getElementById("multi-vehicle-form");
  const numVehiclesSelect = document.getElementById("mv-num-vehicles");
  const btnResetPresets = document.getElementById("btn-reset-presets");
  const mvError = document.getElementById("mv-error-message");
  const mvGenerateBtn = document.getElementById("mv-generate-btn");
  const dlCsv = document.getElementById("mv-download-csv");
  const dlJson = document.getElementById("mv-download-json");

  if (numVehiclesSelect) {
    numVehiclesSelect.addEventListener("change", (e) => {
      renderVehicleSetupCards(Number(e.target.value));
    });
  }

  if (btnResetPresets) {
    btnResetPresets.addEventListener("click", () => {
      renderVehicleSetupCards(Number(numVehiclesSelect.value));
    });
  }

  function setMvLoading(loading) {
    mvGenerateBtn.disabled = loading;
    mvGenerateBtn.classList.toggle("is-loading", loading);
    mvGenerateBtn.querySelector(".button-label").textContent = loading
      ? "Synthesizing Fleet Telematics & Scoring..."
      : "Generate Fleet Telematics & Assess Insurance";
  }

  if (mvForm) {
    mvForm.addEventListener("submit", async (e) => {
      e.preventDefault();
      mvError.hidden = true;
      mvError.textContent = "";
      setMvLoading(true);

      const numV = Number(numVehiclesSelect.value);
      const customVehicles = [];

      for (let i = 0; i < numV; i++) {
        customVehicles.push({
          vehicle_id: activeVehicles[i].vehicle_id,
          vehicle_name: document.getElementById(`v-name-${i}`).value.trim(),
          vehicle_category: document.getElementById(`v-cat-${i}`).value,
          target_speed: Number(document.getElementById(`v-speed-${i}`).value),
          driving_behaviour: document.getElementById(`v-behav-${i}`).value,
          color: activeVehicles[i].color,
        });
      }

      const payload = {
        num_vehicles: numV,
        road_speed_limit: Number(document.getElementById("mv-road-speed-limit").value),
        base_premium: Number(document.getElementById("mv-base-premium").value),
        records_per_vehicle: Number(document.getElementById("mv-records-per-vehicle").value),
        seed: Number(document.getElementById("mv-seed").value),
        vehicles: customVehicles,
      };

      try {
        const response = await fetch("/api/generate-multiple", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload),
        });

        const data = await response.json();
        if (!response.ok) throw new Error(data.error || "Generation error.");

        // Update active vehicles state & Simulation Studio
        activeVehicles = data.vehicles;
        roadSpeedLimit = data.road_speed_limit;
        sim.syncWithFleet(activeVehicles, roadSpeedLimit);

        // Update UI Analytics & Visualizations
        updateOverviewKpis(data.fleet_summary);
        renderBestDriverAnalysis(data.comparison.best_driver_analysis);
        renderComparisonTable(data.comparison.rankings);
        renderComparativeCharts(data.vehicles, data.fleet_summary, data.road_speed_limit);
        renderInsuranceCards(data.vehicles);
        renderRecommendations(data.vehicles);
        renderTripPreview(data.preview);

        // Configure Export Links
        dlCsv.href = data.download_url;
        dlCsv.classList.remove("disabled");
        dlCsv.removeAttribute("aria-disabled");

        dlJson.href = data.download_json_url;
        dlJson.classList.remove("disabled");
        dlJson.removeAttribute("aria-disabled");
      } catch (err) {
        mvError.textContent = err.message || "Failed to generate multi-vehicle telematics.";
        mvError.hidden = false;
      } finally {
        setMvLoading(false);
      }
    });
  }

  // -------------------------------------------------------------
  // Legacy Single Scenario Form (Backwards Compatible)
  // -------------------------------------------------------------
  const singleForm = document.getElementById("generation-form");
  if (singleForm) {
    const singleScenarioSelect = document.getElementById("scenario");
    const singleCustomSettings = document.getElementById("custom-settings");

    if (singleScenarioSelect && singleCustomSettings) {
      singleScenarioSelect.addEventListener("change", () => {
        singleCustomSettings.hidden = singleScenarioSelect.value !== "Custom Risk";
      });
    }

    singleForm.addEventListener("submit", async (e) => {
      e.preventDefault();
      const errBox = document.getElementById("error-message");
      if (errBox) errBox.hidden = true;
      const btn = singleForm.querySelector(".generate-button");
      btn.disabled = true;

      const payload = {
        records: Number(document.getElementById("records").value),
        scenario: singleScenarioSelect.value,
        seed: Number(document.getElementById("seed").value),
      };

      if (payload.scenario === "Custom Risk") {
        payload.custom_settings = {
          average_speed_min: Number(document.getElementById("speed-min").value),
          average_speed_max: Number(document.getElementById("speed-max").value),
          risk_intensity: Number(document.getElementById("risk-intensity").value),
          night_ratio: Number(document.getElementById("night-ratio").value),
        };
      }

      try {
        const res = await fetch("/api/generate", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload),
        });
        const json = await res.json();
        if (!res.ok) throw new Error(json.error || "Single generation failed.");
        alert(`Successfully generated ${json.summary.kpis.records} trips for ${json.scenario}! Download URL: ${json.download_url}`);
      } catch (err) {
        if (errBox) {
          errBox.textContent = err.message;
          errBox.hidden = false;
        }
      } finally {
        btn.disabled = false;
      }
    });
  }

  // -------------------------------------------------------------
  // Initial Page Boot
  // -------------------------------------------------------------
  renderVehicleSetupCards(3);
  sim.init();

  // Auto-generate initial multi-vehicle demonstration dataset
  if (mvForm) {
    mvForm.dispatchEvent(new Event("submit"));
  }
})();
