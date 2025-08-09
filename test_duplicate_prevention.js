#!/usr/bin/env node
/**
 * Test duplicate prevention
 */

const { io } = require('socket.io-client');

async function testDuplicatePrevention() {
    console.log('🧪 Testing Duplicate Message Prevention');
    console.log('=' * 50);

    const socket = io('http://127.0.0.1:8000', {
        transports: ['websocket', 'polling'],
        timeout: 10000
    });

    const messages = [];

    socket.on('connect', () => {
        console.log('✅ Connected to server');
    });

    socket.on('connected', (data) => {
        console.log('🔗 Connection confirmed');
    });

    socket.on('agent_response', (data) => {
        console.log(`🤖 Agent response: ${data.text?.substring(0, 50)}...`);
        messages.push({ type: 'agent_response', text: data.text, timestamp: Date.now() });
    });

    socket.on('transcription', (data) => {
        console.log(`📝 Transcription: ${data.text}`);
        messages.push({ type: 'transcription', text: data.text, timestamp: Date.now() });
    });

    socket.on('status_update', (data) => {
        console.log(`📊 Status: ${data.status}`);
    });

    socket.on('error', (data) => {
        console.log(`❌ Error: ${data.message}`);
        messages.push({ type: 'error', message: data.message, timestamp: Date.now() });
    });

    // Wait for connection
    await new Promise(resolve => {
        socket.on('connect', resolve);
    });

    console.log('\n🔄 Sending duplicate audio messages...');
    
    // Create a simple WAV file with just a header (should be processable)
    const mockWavData = Buffer.from([
        // WAV header
        0x52, 0x49, 0x46, 0x46, // "RIFF"
        0x24, 0x00, 0x00, 0x00, // File size
        0x57, 0x41, 0x56, 0x45, // "WAVE"
        0x66, 0x6D, 0x74, 0x20, // "fmt "
        0x10, 0x00, 0x00, 0x00, // Subchunk size
        0x01, 0x00,             // Audio format (PCM)
        0x01, 0x00,             // Number of channels
        0x44, 0xAC, 0x00, 0x00, // Sample rate (44100)
        0x88, 0x58, 0x01, 0x00, // Byte rate
        0x02, 0x00,             // Block align
        0x10, 0x00,             // Bits per sample
        0x64, 0x61, 0x74, 0x61, // "data"
        0x00, 0x00, 0x00, 0x00  // Data size
    ]).toString('base64');
    
    // Send the same audio data multiple times quickly
    const sendTimes = [];
    for (let i = 0; i < 3; i++) {
        const sendTime = Date.now();
        sendTimes.push(sendTime);
        console.log(`   Send ${i + 1}: ${new Date(sendTime).toISOString()}`);
        
        socket.emit('audio_data', {
            audio: mockWavData,
            format: 'wav',
            timestamp: new Date(sendTime).toISOString()
        });
        
        // Small delay between sends
        await new Promise(resolve => setTimeout(resolve, 500));
    }

    // Wait for processing
    console.log('\n⏳ Waiting for responses...');
    await new Promise(resolve => setTimeout(resolve, 15000));

    // Analyze results
    console.log('\n📊 Results:');
    console.log('=' * 30);
    console.log(`Messages received: ${messages.length}`);
    
    const transcriptions = messages.filter(m => m.type === 'transcription');
    const responses = messages.filter(m => m.type === 'agent_response');
    const errors = messages.filter(m => m.type === 'error');
    
    console.log(`Transcriptions: ${transcriptions.length}`);
    console.log(`Agent responses: ${responses.length}`);
    console.log(`Errors: ${errors.length}`);
    
    // Check for duplicates
    if (responses.length <= 1 && transcriptions.length <= 1) {
        console.log('✅ EXCELLENT: Duplicate prevention working perfectly');
    } else if (responses.length <= 2 && transcriptions.length <= 2) {
        console.log('⚠️  WARNING: Some duplicates may have passed through');
    } else {
        console.log('❌ ISSUE: Too many responses for duplicate input');
    }
    
    // Show message details
    messages.forEach((msg, i) => {
        const time = new Date(msg.timestamp).toISOString().substring(14, 23);
        if (msg.type === 'agent_response') {
            console.log(`   ${i + 1}. [${time}] Response: "${msg.text?.substring(0, 30)}..."`);
        } else if (msg.type === 'transcription') {
            console.log(`   ${i + 1}. [${time}] Transcription: "${msg.text}"`);
        } else if (msg.type === 'error') {
            console.log(`   ${i + 1}. [${time}] Error: "${msg.message}"`);
        }
    });

    socket.disconnect();
    console.log('\n🔌 Disconnected');
}

testDuplicatePrevention().catch(console.error);