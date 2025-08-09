const io = require('socket.io-client');
let events = [];
const socket = io('http://localhost:8000');

function logEvent(name, data) {
  const timestamp = new Date().toISOString();
  events.push({ timestamp, name, data });
  console.log(`[${timestamp}] ${name}:`, data ? JSON.stringify(data).substring(0, 100) + '...' : 'no data');
}

socket.on('connect', (data) => logEvent('connect', { id: socket.id }));
socket.on('connected', (data) => logEvent('connected', data));
socket.on('agent_response', (data) => logEvent('agent_response', { hasText: !!data.text, hasAudio: !!data.audio, intent: data.intent }));
socket.on('disconnect', (data) => logEvent('disconnect', data));
socket.on('connect_error', (err) => logEvent('connect_error', err.message));
socket.on('status_update', (data) => logEvent('status_update', data));
socket.on('error', (data) => logEvent('error', data));

setTimeout(() => {
  console.log(`\n📊 Summary: ${events.length} events received`);
  console.log('Event sequence:', events.map(e => e.name).join(' -> '));
  socket.disconnect();
  process.exit(0);
}, 5000);