#!/usr/bin/env node
/**
 * Debug Connection Timing
 * Monitor exactly when messages are sent after connection
 */

const { io } = require('socket.io-client');

async function debugConnectionTiming() {
    console.log('🔍 Debugging Connection Timing');
    console.log('=' * 40);

    const socket = io('http://127.0.0.1:8000', {
        transports: ['websocket', 'polling'],
        timeout: 5000
    });

    const startTime = Date.now();
    const events = [];

    function logEvent(eventType, data = null) {
        const timestamp = Date.now() - startTime;
        const event = {
            time: timestamp,
            type: eventType,
            data: data
        };
        events.push(event);
        console.log(`[${timestamp}ms] ${eventType}${data ? ': ' + JSON.stringify(data).substring(0, 100) + '...' : ''}`);
    }

    socket.on('connect', () => {
        logEvent('socket.connect');
    });

    socket.on('connected', (data) => {
        logEvent('server.connected', data);
    });

    socket.on('agent_response', (data) => {
        logEvent('server.agent_response', { text: data.text?.substring(0, 50) + '...', hasAudio: !!data.audio });
    });

    socket.on('transcription', (data) => {
        logEvent('server.transcription', data);
    });

    socket.on('status_update', (data) => {
        logEvent('server.status_update', data);
    });

    socket.on('error', (data) => {
        logEvent('server.error', data);
    });

    socket.on('disconnect', (reason) => {
        logEvent('socket.disconnect', { reason });
    });

    // Wait for 5 seconds to see all automatic events
    await new Promise(resolve => setTimeout(resolve, 5000));

    console.log('\n📊 Event Summary:');
    console.log('=' * 30);
    
    events.forEach((event, index) => {
        console.log(`${index + 1}. [${event.time}ms] ${event.type}`);
        if (event.data && typeof event.data === 'object') {
            Object.keys(event.data).forEach(key => {
                console.log(`   ${key}: ${JSON.stringify(event.data[key]).substring(0, 80)}...`);
            });
        }
    });

    // Check if any agent responses were sent without audio input
    const autoResponses = events.filter(e => e.type === 'server.agent_response');
    console.log(`\n🤖 Automatic responses: ${autoResponses.length}`);
    
    if (autoResponses.length > 0) {
        console.log('⚠️  ISSUE: Automatic greetings detected!');
        autoResponses.forEach((resp, i) => {
            console.log(`   ${i + 1}. At ${resp.time}ms: ${resp.data?.text || 'No text'}`);
        });
    } else {
        console.log('✅ No automatic responses (good!)');
    }

    socket.disconnect();
    console.log('\n🔌 Disconnected');
}

debugConnectionTiming().catch(console.error);