const STALE_MS = 3000;
const MAX_LINES = 300;

const lastSeen = { mosquitto: 0, ros2_sim: 0, backend: 0, dashboard: 0 };
let mosquittoConnected = null; // null = unknown, true/false once we hear from backend
let dashboardFrameCount = 0;
let dashboardLastPoint = "";

function appendLine(source, text, cls) {
  const tail = document.getElementById(`tail-${source}`);
  if (!tail) return;
  const div = document.createElement("div");
  div.className = "line" + (cls ? ` ${cls}` : "");
  const time = new Date().toLocaleTimeString();
  div.textContent = `[${time}] ${text}`;
  tail.appendChild(div);
  while (tail.children.length > MAX_LINES) tail.removeChild(tail.firstChild);
  tail.scrollTop = tail.scrollHeight;
}

function setStats(source, text) {
  const el = document.getElementById(`stats-${source}`);
  if (el) el.textContent = text;
}

function refreshDots() {
  const now = Date.now();
  for (const source of ["ros2_sim", "backend", "dashboard"]) {
    const dot = document.getElementById(`dot-${source}`);
    if (dot) dot.classList.toggle("live", now - lastSeen[source] < STALE_MS);
  }
  const mosquittoDot = document.getElementById("dot-mosquitto");
  if (mosquittoDot) {
    mosquittoDot.classList.toggle("live", mosquittoConnected === true && now - lastSeen.mosquitto < STALE_MS);
  }
}

setInterval(() => {
  setStats("dashboard", `displayed=${dashboardFrameCount}/s last_point=${dashboardLastPoint || "-"}`);
  dashboardFrameCount = 0;
  refreshDots();
}, 1000);

connect((frame) => {
  const now = Date.now();
  dashboardFrameCount++;
  lastSeen.dashboard = now;
  if (frame.point_id) dashboardLastPoint = frame.point_id;

  if (frame.type === "log") {
    const source = frame.source;
    lastSeen[source] = now;

    if (source === "ros2_sim") {
      const line = `sent=${frame.rate}/s last_topic=${frame.last_topic} pose=(x=${frame.pose_x.toFixed(2)},y=${frame.pose_y.toFixed(2)})`;
      setStats("ros2_sim", line);
      appendLine("ros2_sim", line);
      return;
    }
    if (source === "backend") {
      setStats(
        "backend",
        `rx=${frame.rx}/s -> processed -> tx=${frame.tx}/s last_topic=${frame.last_topic}\nmqtt_connected=${frame.mqtt_connected}`
      );
      appendLine("backend", `rx=${frame.rx}/s -> processed -> tx=${frame.tx}/s last_topic=${frame.last_topic}`);

      // Mosquitto has no periodic heartbeat of its own -- derive its live
      // status from what the backend reports about its connection every
      // second, so the panel doesn't just sit on "waiting for first
      // message" when the browser connects after the one-off connect event.
      const nowConnected = !!frame.mqtt_connected;
      if (mosquittoConnected !== nowConnected) {
        appendLine("mosquitto", `now ${nowConnected ? "connected" : "disconnected"} (via backend)`, "event");
      }
      mosquittoConnected = nowConnected;
      lastSeen.mosquitto = now;
      setStats("mosquitto", `connected=${nowConnected} (reported by backend every 1s)`);
      return;
    }
    if (source === "mosquitto") {
      mosquittoConnected = frame.event === "connected";
      lastSeen.mosquitto = now;
      setStats("mosquitto", `backend reports: ${frame.event}`);
      appendLine("mosquitto", `backend ${frame.event} to broker`, "event");
      return;
    }
    return;
  }

  if (frame.type === "snapshot") {
    appendLine("dashboard", "received snapshot (initial state + alerts)", "event");
    return;
  }

  if (frame.type === "detector") {
    appendLine("backend", `detector ${frame.point_id} -> ${frame.state} (${frame.detail ?? ""})`, frame.state);
    appendLine("dashboard", `detector update ${frame.point_id} -> ${frame.state}`, frame.state);
    return;
  }

  if (frame.type === "alert") {
    const a = frame.alert;
    const sev = (a.severity || "").toLowerCase();
    appendLine("backend", `emitted alert [${a.severity}] ${a.point_id}: ${a.message}`, sev);
    appendLine("dashboard", `displaying alert [${a.severity}] ${a.point_id}: ${a.message}`, sev);
    return;
  }

  // frame.type === "telemetry": too high-volume for a line-per-message tail;
  // it's already reflected in the rate counters above.
});
