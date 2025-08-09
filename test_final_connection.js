#!/usr/bin/env node
/**
 * Final WebSocket Connection Test
 * Tests the complete connection and audio flow
 */

const io = require('socket.io-client');
const fs = require('fs');

console.log('🚀 Final WebSocket Connection Test');
console.log('==================================\n');

// Connect to the WebSocket server
const socket = io('http://localhost:8000', {
  transports: ['polling', 'websocket'],
  upgrade: true,
  reconnection: false,
  timeout: 10000
});

let testResults = {
  connection: false,
  greeting: false,
  audioSent: false,
  transcription: false,
  agentResponse: false
};

// Connection events
socket.on('connect', () => {
  console.log('✅ Connected to WebSocket server');
  console.log('   Socket ID:', socket.id);
  console.log('   Transport:', socket.io.engine.transport.name);
  testResults.connection = true;
});

socket.on('connected', (data) => {
  console.log('✅ Received server greeting');
  console.log('   Message:', data.message);
  testResults.greeting = true;
});

socket.on('agent_response', (data) => {
  console.log('✅ Received agent response');
  console.log('   Text:', data.text?.substring(0, 100) + '...');
  if (data.audio) {
    console.log('   Audio: Included');
  }
  testResults.agentResponse = true;
  
  // Test sending audio after connection
  setTimeout(() => sendTestAudio(), 1000);
});

socket.on('transcription', (data) => {
  console.log('✅ Received transcription');
  console.log('   Text:', data.text);
  console.log('   Confidence:', data.confidence);
  testResults.transcription = true;
});

socket.on('status_update', (data) => {
  console.log('📊 Status update:', data.status, '-', data.message);
});

socket.on('error', (error) => {
  console.log('❌ Server error:', error.message || error);
});

socket.on('connect_error', (error) => {
  console.log('❌ Connection error:', error.message);
  console.log('   Type:', error.type);
  process.exit(1);
});

// Function to send test audio
function sendTestAudio() {
  console.log('\n📤 Sending test audio data...');
  
  // Create a simple test audio (base64 encoded)
  const testAudioBase64 = Buffer.from('test audio data').toString('base64');
  
  socket.emit('audio_data', {
    audio: testAudioBase64,
    format: 'webm',
    timestamp: new Date().toISOString(),
    size: 1024
  });
  
  testResults.audioSent = true;
  console.log('   Audio sent successfully');
}

// Test health check
socket.on('connect', () => {
  setTimeout(() => {
    console.log('\n🏥 Sending health check...');
    socket.emit('health_check');
  }, 500);
});

socket.on('health_response', (data) => {
  console.log('✅ Health check response received');
  console.log('   Status:', data.status);
  console.log('   Active sessions:', data.active_sessions);
});

// Final report after 5 seconds
setTimeout(() => {
  console.log('\n==================================');
  console.log('📊 FINAL TEST RESULTS:');
  console.log('==================================');
  
  Object.entries(testResults).forEach(([test, passed]) => {
    const status = passed ? '✅' : '❌';
    const label = test.charAt(0).toUpperCase() + test.slice(1).replace(/([A-Z])/g, ' $1');
    console.log(`${status} ${label}: ${passed ? 'PASSED' : 'FAILED'}`);
  });
  
  const passedTests = Object.values(testResults).filter(v => v).length;
  const totalTests = Object.values(testResults).length;
  const successRate = (passedTests / totalTests * 100).toFixed(0);
  
  console.log('\n📈 Success Rate:', `${passedTests}/${totalTests} (${successRate}%)`);
  
  if (successRate === '100') {
    console.log('\n🎉 ALL TESTS PASSED! WebSocket connection is working perfectly!');
  } else if (successRate >= '60') {
    console.log('\n⚠️  PARTIAL SUCCESS - Some features need attention');
  } else {
    console.log('\n❌ TESTS FAILED - Connection issues detected');
  }
  
  socket.disconnect();
  process.exit(successRate === '100' ? 0 : 1);
}, 5000);