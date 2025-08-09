#!/usr/bin/env node
/**
 * Test connection to minimal debug server
 */

const { io } = require('socket.io-client');

async function testMinimalConnection() {
    console.log('🧪 Testing Minimal Debug Server Connection');
    console.log('=' * 50);

    const socket = io('http://127.0.0.1:8001', {
        transports: ['websocket', 'polling'],
        timeout: 5000
    });

    const events = [];
    const startTime = Date.now();

    function logEvent(type, data = null) {
        const timestamp = Date.now() - startTime;
        events.push({ timestamp, type, data });
        console.log(`[${timestamp}ms] ${type}${data ? ': ' + JSON.stringify(data).substring(0, 80) + '...' : ''}`);
    }

    socket.on('connect', () => logEvent('socket.connect'));
    socket.on('connected', (data) => logEvent('server.connected', data));
    socket.on('agent_response', (data) => logEvent('server.agent_response', data));
    socket.on('error', (data) => logEvent('server.error', data));
    socket.on('disconnect', (reason) => logEvent('socket.disconnect', { reason }));

    // Wait 5 seconds to see automatic events
    await new Promise(resolve => setTimeout(resolve, 5000));

    // Check for automatic agent responses
    const autoResponses = events.filter(e => e.type === 'server.agent_response');
    
    console.log(`\n📊 Results:`);
    console.log(`   Total events: ${events.length}`);
    console.log(`   Automatic responses: ${autoResponses.length}`);
    
    if (autoResponses.length > 0) {
        console.log('❌ ISSUE: Minimal server also sends automatic greetings!');
        console.log('   This suggests the issue is NOT in our voice agent code.');
    } else {
        console.log('✅ SUCCESS: Minimal server has no automatic greetings.');
        console.log('   The issue is in the voice agent initialization.');
    }

    socket.disconnect();
}

testMinimalConnection().catch(console.error);