const HISTORY_LEN = 60;
const JOINT_IDS = [0, 1, 2, 3];
const WHEEL_IDS = ["fl", "fr", "rl", "rr"];
const ARM_JOINT_NAMES = ["waist", "shoulder", "elbow", "wrist_angle", "wrist_rotate", "gripper"];

const lineCharts = {}; // point_id -> {chart, wrapEl}

function makeLineChart(canvasId, wrapId, label, color) {
  const ctx = document.getElementById(canvasId).getContext("2d");
  const chart = new Chart(ctx, {
    type: "line",
    data: {
      labels: Array(HISTORY_LEN).fill(""),
      datasets: [
        {
          label,
          data: Array(HISTORY_LEN).fill(null),
          borderColor: color,
          borderWidth: 1.5,
          pointRadius: 0,
          tension: 0.25,
        },
      ],
    },
    options: {
      animation: false,
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        x: { display: false },
        y: { ticks: { color: "#666", font: { size: 9 } }, grid: { color: "#eee" } },
      },
      plugins: { legend: { display: false } },
    },
  });
  return { chart, wrapEl: document.getElementById(wrapId) };
}

function pushPoint(entry, value) {
  const data = entry.chart.data.datasets[0].data;
  data.push(value);
  data.shift();
  entry.chart.update("none");
}

function idFor(pointId) {
  return `val-${pointId.replace(/\//g, "-")}`;
}

function setValue(id, text, state) {
  const el = document.getElementById(id);
  if (!el) return;
  el.textContent = text;
  el.classList.remove("warning", "fault");
  if (state === "warning") el.classList.add("warning");
  if (state === "fault") el.classList.add("fault");
}

function initCharts() {
  JOINT_IDS.forEach((j) => {
    lineCharts[`joints/${j}/position`] = makeLineChart(`chart-joint-${j}-position`, `wrap-joint-${j}-position`, "position", "#0a7d32");
    lineCharts[`joints/${j}/torque`] = makeLineChart(`chart-joint-${j}-torque`, `wrap-joint-${j}-torque`, "torque", "#1d6fb8");
  });

  lineCharts["imu/orientation"] = makeLineChart("chart-imu", "wrap-imu", "roll", "#0a7d32");

  WHEEL_IDS.forEach((w) => {
    lineCharts[`wheels/${w}/slip`] = makeLineChart(`chart-wheel-${w}-slip`, `wrap-wheel-${w}-slip`, "slip", "#946800");
  });

  ARM_JOINT_NAMES.forEach((name) => {
    lineCharts[`arm/${name}/position`] = makeLineChart(`chart-arm-${name}-position`, `wrap-arm-${name}-position`, "position", "#7a3b96");
  });
}

function handleTelemetry(frame) {
  const { point_id, payload, state } = frame;
  const entry = lineCharts[point_id];

  if (point_id === "imu/orientation" && entry) {
    pushPoint(entry, payload.value.roll);
    setValue(idFor(point_id), payload.value.roll.toFixed(2), state);
    return;
  }

  if (entry) {
    const v = typeof payload.value === "number" ? payload.value : null;
    if (v !== null) {
      pushPoint(entry, v);
      setValue(idFor(point_id), v.toFixed(3), state);
    }
  }

  if (point_id.startsWith("wheels/") && point_id.endsWith("/speed")) {
    const wid = point_id.split("/")[1];
    updateWheelSpeed(wid, payload.value);
  }

  if (point_id.startsWith("arm/") && (point_id.endsWith("/effort") || point_id.endsWith("/error"))) {
    const v = typeof payload.value === "number" ? payload.value : null;
    if (v !== null) setValue(idFor(point_id), v.toFixed(3), state);
  }

  if (point_id === "comms/heartbeat") {
    updateHeartbeatDot(point_id, state);
  }
}

function updateCameraFrame(frame) {
  const img = document.getElementById("camera-frame-img");
  if (img && frame.data) img.src = `data:image/${frame.format || "png"};base64,${frame.data}`;
  const ts = document.getElementById("val-camera-frame-ts");
  if (ts && frame.ts) ts.textContent = new Date(frame.ts * 1000).toLocaleTimeString();
}

function updateWheelSpeed(wid, value) {
  const el = document.getElementById(`wheel-${wid}-speed`);
  if (el && value) el.textContent = `cmd ${value.commanded.toFixed(2)} / act ${value.actual.toFixed(2)} rad/s`;
}

function updateHeartbeatDot(pointId, state) {
  const statusEl = document.querySelector("#hb-comms .hb-status");
  if (!statusEl) return;
  statusEl.classList.remove("warning", "fault");
  if (state === "warning") statusEl.classList.add("warning");
  if (state === "fault") statusEl.classList.add("fault");
  statusEl.textContent = state === "normal" ? "live" : state;
}
