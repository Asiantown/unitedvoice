#!/usr/bin/env node
/**
 * Debug Server Events - Monitor all events sent to/from server
 */

const { io } = require('socket.io-client');

async function debugServerEvents() {
    console.log('🔍 Monitoring Server Events');
    console.log('=' * 40);

    const socket = io('http://127.0.0.1:8000', {
        transports: ['websocket', 'polling'],
        timeout: 10000
    });

    let eventCount = 0;
    
    // Log all outgoing events
    const originalEmit = socket.emit;
    socket.emit = function(...args) {
        eventCount++;
        console.log(`📤 [OUT ${eventCount}] Client sending: ${args[0]}`);
        if (args[1]) {
            console.log(`   Data keys: ${Object.keys(args[1]).join(', ')}`);
            if (args[1].audio) {
                console.log(`   Audio data length: ${args[1].audio.length}`);
            }
        }
        return originalEmit.apply(this, args);
    };

    // Log all incoming events
    socket.onAny((eventName, ...args) => {
        eventCount++;
        console.log(`📥 [IN  ${eventCount}] Server sent: ${eventName}`);
        if (args[0]) {
            if (typeof args[0] === 'object') {
                console.log(`   Data keys: ${Object.keys(args[0]).join(', ')}`);
                if (args[0].text) {
                    console.log(`   Text: "${args[0].text.substring(0, 50)}..."`);
                }
                if (args[0].audio) {
                    console.log(`   Audio data: ${!!args[0].audio ? 'present' : 'absent'}`);
                }
            } else {
                console.log(`   Data: ${args[0]}`);
            }
        }
    });

    socket.on('connect', () => {
        console.log('✅ Connected to server');
    });

    socket.on('disconnect', (reason) => {
        console.log(`❌ Disconnected: ${reason}`);
    });

    // Wait and see what automatic events happen
    console.log('\n⏱️  Waiting 5 seconds to monitor automatic events...\n');
    
    await new Promise(resolve => setTimeout(resolve, 5000));

    console.log(`\n📊 Total events captured: ${eventCount}`);
    
    socket.disconnect();
    console.log('🔌 Disconnected');
}

debugServerEvents().catch(console.error);