const io = require('socket.io-client');

console.log('Testing WebSocket connection to localhost:8000...');

const socket = io('http://localhost:8000', {
  transports: ['websocket', 'polling'],
  timeout: 5000,
  reconnection: false
});

let connected = false;

socket.on('connect', () => {
  connected = true;
  console.log('✅ Connected successfully!');
  console.log('Session ID:', socket.id);
});

socket.on('connected', (data) => {
  console.log('✅ Received "connected" event:', data);
});

socket.on('agent_response', (data) => {
  console.log('✅ Received agent greeting:', data.text?.substring(0, 50) + '...');
});

socket.on('connect_error', (error) => {
  console.log('❌ Connection error:', error.message);
  console.log('Error type:', error.type);
  process.exit(1);
});

socket.on('disconnect', () => {
  console.log('Disconnected from server');
});

// Give it 3 seconds to connect and receive messages
setTimeout(() => {
  if (connected) {
    console.log('✅ Test successful - WebSocket is working!');
    socket.disconnect();
    process.exit(0);
  } else {
    console.log('❌ Test failed - Could not connect within 3 seconds');
    process.exit(1);
  }
}, 3000);