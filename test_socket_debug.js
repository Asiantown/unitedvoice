const io = require('socket.io-client');

console.log('Testing WebSocket connection with detailed debugging...');

const socket = io('http://localhost:8000', {
  transports: ['polling', 'websocket'], // Try polling first
  timeout: 10000,
  reconnection: false,
  debug: true
});

console.log('Socket created, waiting for events...');

socket.on('connect', () => {
  console.log('✅ CONNECTED!');
  console.log('Socket ID:', socket.id);
  console.log('Transport:', socket.io.engine.transport.name);
});

socket.on('connect_error', (error) => {
  console.log('❌ Connection error details:');
  console.log('  Message:', error.message);
  console.log('  Type:', error.type);
  console.log('  Stack:', error.stack);
});

socket.io.on('packet', (packet) => {
  console.log('📦 Packet received:', packet);
});

socket.io.on('data', (data) => {
  console.log('📊 Data received:', data);
});

// Try manual connection
console.log('Attempting to connect...');
socket.connect();

// Also test with curl
const { exec } = require('child_process');
exec('curl -s "http://localhost:8000/socket.io/?EIO=4&transport=polling"', (error, stdout, stderr) => {
  if (error) {
    console.log('curl test failed:', error);
  } else {
    console.log('curl test successful, response:', stdout.substring(0, 100));
  }
});

setTimeout(() => {
  console.log('Final socket state:', socket.connected ? 'CONNECTED' : 'NOT CONNECTED');
  process.exit(socket.connected ? 0 : 1);
}, 5000);