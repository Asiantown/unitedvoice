#!/usr/bin/env node

const puppeteer = require('puppeteer');

async function quickTest() {
    console.log('🎤 Running Quick Voice Interface Test...\n');
    
    let browser, page;
    
    try {
        browser = await puppeteer.launch({
            headless: false,
            args: [
                '--use-fake-ui-for-media-stream',
                '--use-fake-device-for-media-stream',
                '--allow-running-insecure-content',
                '--disable-web-security',
                '--autoplay-policy=no-user-gesture-required'
            ]
        });

        page = await browser.newPage();
        
        const context = browser.defaultBrowserContext();
        await context.overridePermissions('http://localhost:3000', ['microphone']);

        const messages = [];
        page.on('console', msg => {
            messages.push({
                type: msg.type(),
                text: msg.text(),
                timestamp: new Date().toISOString()
            });
            console.log(`[${msg.type().toUpperCase()}] ${msg.text()}`);
        });

        console.log('📄 Loading voice page...');
        await page.goto('http://localhost:3000/voice', { 
            waitUntil: 'networkidle0',
            timeout: 30000 
        });

        console.log('✅ Page loaded successfully');

        // Wait a bit for React to initialize
        await page.waitForTimeout(3000);

        // Check for voice orb
        const hasVoiceOrb = await page.$('[data-testid="voice-orb"]');
        console.log(hasVoiceOrb ? '✅ Voice orb found' : '❌ Voice orb not found');

        // Check for canvas elements
        const canvases = await page.$$eval('canvas', canvases => canvases.length);
        console.log(`✅ Found ${canvases} canvas element(s)`);

        // Check connection status
        await page.waitForTimeout(5000);
        const connectionText = await page.evaluate(() => {
            const elements = document.querySelectorAll('*');
            for (let el of elements) {
                if (el.textContent && (
                    el.textContent.includes('Connected') ||
                    el.textContent.includes('Connecting') ||
                    el.textContent.includes('Connection failed')
                )) {
                    return el.textContent.trim();
                }
            }
            return 'No connection status found';
        });
        console.log('📡 Connection status:', connectionText);

        // Test spacebar interaction
        console.log('⌨️  Testing spacebar...');
        await page.keyboard.down('Space');
        await page.waitForTimeout(1000);
        await page.keyboard.up('Space');
        
        // Keep browser open for manual testing
        console.log('\n🎯 Browser is open for manual testing. Press Ctrl+C to close.');
        console.log('📍 Try the following manual tests:');
        console.log('   1. Hold spacebar to record');
        console.log('   2. Click and hold the microphone button');
        console.log('   3. Check WebSocket connection');
        console.log('   4. Test audio playback');
        
        // Wait for manual intervention
        await new Promise(resolve => {
            process.on('SIGINT', () => {
                console.log('\n👋 Closing test...');
                resolve();
            });
        });

    } catch (error) {
        console.error('❌ Test failed:', error.message);
    } finally {
        if (browser) {
            await browser.close();
        }
    }
}

quickTest().catch(console.error);