let activeAlerts = {}; // point_id -> alert

function renderBanner() {
  const banner = document.getElementById("alert-banner");
  const values = Object.values(activeAlerts);
  const critical = values.filter((a) => a.severity === "CRITICAL");
  const warning = values.filter((a) => a.severity === "WARNING");

  banner.classList.remove("ok", "warning", "critical");
  document.body.classList.toggle("safe-state-active", critical.length > 0);

  if (critical.length > 0) {
    banner.classList.add("critical");
    banner.textContent = `SAFE STATE TRIGGERED — ${critical.length} critical alert(s): ${critical.map((a) => a.point_id).join(", ")}`;
  } else if (warning.length > 0) {
    banner.classList.add("warning");
    banner.textContent = `${warning.length} warning(s): ${warning.map((a) => a.point_id).join(", ")}`;
  } else {
    banner.classList.add("ok");
    banner.textContent = "All systems normal";
  }
}

function addLogRow(alert) {
  const tbody = document.querySelector("#alert-log tbody");
  if (!tbody) return;
  const tr = document.createElement("tr");
  tr.className = alert.severity;
  const time = new Date(alert.ts * 1000).toLocaleTimeString();
  tr.innerHTML = `<td>${time}</td><td>${alert.severity}</td><td>${alert.point_id}</td><td>${alert.message}</td>`;
  tbody.prepend(tr);
  while (tbody.children.length > 100) tbody.removeChild(tbody.lastChild);
}

function handleAlert(frame) {
  const alert = frame.alert;
  activeAlerts[alert.point_id] = alert;
  addLogRow(alert);
  renderBanner();
}

function handleSnapshot(frame) {
  const alertsSnap = frame.alerts;
  if (!alertsSnap) return;
  activeAlerts = {};
  for (const a of alertsSnap.active_alerts) activeAlerts[a.point_id] = a;
  for (const a of [...alertsSnap.log].reverse()) addLogRow(a);
  renderBanner();
}

function clearAlertIfNormal(pointId, state) {
  if (state === "normal" && activeAlerts[pointId]) {
    delete activeAlerts[pointId];
    renderBanner();
  }
}
