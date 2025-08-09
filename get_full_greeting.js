#!/usr/bin/env node
/**
 * Capture the full greeting message
 */

const { io } = require('socket.io-client');

async function captureFullGreeting() {
    const socket = io('http://127.0.0.1:8000', {
        transports: ['websocket', 'polling'],
        timeout: 5000
    });

    socket.on('connect', () => {
        console.log('Connected to server');
    });

    socket.on('connected', (data) => {
        console.log('Server connected event:', data);
    });

    socket.on('agent_response', (data) => {
        console.log('\n📝 FULL GREETING MESSAGE:');
        console.log('=' * 50);
        console.log(`Text: "${data.text}"`);
        console.log(`Has Audio: ${!!data.audio}`);
        console.log(`Intent: ${data.intent}`);
        console.log(`Conversation State: ${JSON.stringify(data.conversation_state, null, 2)}`);
        console.log('=' * 50);
        
        // Disconnect after getting the message
        socket.disconnect();
    });

    socket.on('error', (data) => {
        console.error('Server error:', data);
        socket.disconnect();
    });

    // Wait for message or timeout
    setTimeout(() => {
        console.log('Timeout - disconnecting');
        socket.disconnect();
    }, 5000);
}

captureFullGreeting().catch(console.error);