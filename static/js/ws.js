// WebSocket client with auto-reconnect

let ws = null;
let roomCode = null;
let onMessage = null;
let reconnectTimer = null;

export function connect(code, messageHandler) {
  roomCode = code;
  onMessage = messageHandler;
  _connect();
}

function _connect() {
  const proto = location.protocol === 'https:' ? 'wss:' : 'ws:';
  ws = new WebSocket(`${proto}//${location.host}/ws/${roomCode}`);

  ws.onopen = () => {
    console.log('[WS] connected');
    if (reconnectTimer) {
      clearTimeout(reconnectTimer);
      reconnectTimer = null;
    }
  };

  ws.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data);
      if (onMessage) onMessage(data);
    } catch (e) {
      console.error('[WS] parse error:', e);
    }
  };

  ws.onclose = () => {
    console.log('[WS] disconnected');
    reconnectTimer = setTimeout(_connect, 2000);
  };

  ws.onerror = (e) => {
    console.error('[WS] error:', e);
    ws.close();
  };
}

export function send(data) {
  if (ws && ws.readyState === WebSocket.OPEN) {
    ws.send(JSON.stringify(data));
  }
}
