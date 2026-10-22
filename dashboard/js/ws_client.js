const BACKEND_PORT = 8000;
const BACKEND_HOST = window.location.hostname && window.location.protocol !== "file:"
  ? `${window.location.hostname}:${BACKEND_PORT}`
  : `localhost:${BACKEND_PORT}`;
const WS_URL = `ws://${BACKEND_HOST}/ws`;

let socket = null;
let reconnectDelay = 1000;

function connect(onFrame) {
  socket = new WebSocket(WS_URL);

  socket.onopen = () => {
    reconnectDelay = 1000;
    setConnectionStatus(true);
  };

  socket.onclose = () => {
    setConnectionStatus(false);
    setTimeout(() => connect(onFrame), reconnectDelay);
    reconnectDelay = Math.min(reconnectDelay * 1.5, 15000);
  };

  socket.onerror = () => socket.close();

  socket.onmessage = (event) => {
    try {
      const frame = JSON.parse(event.data);
      onFrame(frame);
    } catch (e) {
      console.error("bad frame", e);
    }
  };
}

function setConnectionStatus(connected) {
  const el = document.getElementById("connection-status");
  if (!el) return;
  el.classList.toggle("connected", connected);
  el.textContent = connected ? "connected" : "disconnected";
}
