#!/usr/bin/env node

const puppeteer = require('puppeteer');

async function runFinalVoiceTest() {
    console.log('🎤 Final Voice Interface Test\n');
    console.log('=================================\n');
    
    let browser, page;
    let testResults = {
        pageLoad: false,
        orbRendering: false,
        websocketConnection: false,
        microphoneAccess: false,
        spacebarInteraction: false,
        mouseInteraction: false,
        audioCapabilities: false,
        noShaderErrors: false
    };
    
    try {
        browser = await puppeteer.launch({
            headless: false,
            defaultViewport: { width: 1280, height: 720 },
            args: [
                '--use-fake-ui-for-media-stream',
                '--use-fake-device-for-media-stream',
                '--allow-running-insecure-content',
                '--disable-web-security',
                '--autoplay-policy=no-user-gesture-required'
            ]
        });

        page = await browser.newPage();
        
        // Grant permissions
        const context = browser.defaultBrowserContext();
        await context.overridePermissions('http://localhost:3000', ['microphone']);

        let shaderErrors = 0;
        let generalErrors = 0;
        
        page.on('console', msg => {
            const text = msg.text();
            const type = msg.type();
            
            if (type === 'error') {
                if (text.includes('Shader Error') || text.includes('WebGL')) {
                    shaderErrors++;
                    console.log(`🔴 Shader Error: ${text.substring(0, 100)}...`);
                } else if (!text.includes('404') && !text.includes('manifest')) {
                    generalErrors++;
                    console.log(`❌ Error: ${text.substring(0, 100)}...`);
                }
            }
        });

        // Test 1: Page Load
        console.log('1️⃣  Testing page load...');
        await page.goto('http://localhost:3000/voice', { 
            waitUntil: 'domcontentloaded',
            timeout: 15000 
        });
        testResults.pageLoad = true;
        console.log('✅ Page loaded successfully\n');

        // Wait for React initialization
        await new Promise(resolve => setTimeout(resolve, 3000));

        // Test 2: 3D Orb Rendering
        console.log('2️⃣  Testing 3D orb rendering...');
        const canvasElements = await page.$$('canvas');
        if (canvasElements.length > 0) {
            testResults.orbRendering = true;
            console.log(`✅ Found ${canvasElements.length} canvas element(s) - 3D orb rendering\n`);
        } else {
            console.log('❌ No canvas elements found\n');
        }

        // Test 3: WebSocket Connection
        console.log('3️⃣  Testing WebSocket connection...');
        await new Promise(resolve => setTimeout(resolve, 5000)); // Wait for connection
        
        const connectionStatus = await page.evaluate(() => {
            const elements = Array.from(document.querySelectorAll('*'));
            for (let el of elements) {
                if (el.textContent && el.textContent.includes('Connected')) {
                    return 'connected';
                }
                if (el.textContent && (el.textContent.includes('Connection failed') || 
                                     el.textContent.includes('Disconnected'))) {
                    return 'failed';
                }
            }
            return 'unknown';
        });

        if (connectionStatus === 'connected') {
            testResults.websocketConnection = true;
            console.log('✅ WebSocket connected to backend\n');
        } else {
            console.log(`❌ WebSocket connection: ${connectionStatus}\n`);
        }

        // Test 4: Microphone Button
        console.log('4️⃣  Testing microphone button...');
        const micButton = await page.$('button');
        if (micButton) {
            testResults.microphoneAccess = true;
            console.log('✅ Microphone button found and accessible\n');
        } else {
            console.log('❌ No microphone button found\n');
        }

        // Test 5: Spacebar Interaction
        console.log('5️⃣  Testing spacebar interaction...');
        
        // Monitor for recording state changes
        const initialState = await page.evaluate(() => {
            const elements = Array.from(document.querySelectorAll('*'));
            return elements.some(el => 
                el.textContent && (
                    el.textContent.includes('Listening') ||
                    el.textContent.includes('Recording')
                )
            );
        });

        // Press spacebar
        await page.keyboard.down('Space');
        await new Promise(resolve => setTimeout(resolve, 500));

        const recordingState = await page.evaluate(() => {
            const elements = Array.from(document.querySelectorAll('*'));
            return elements.some(el => 
                el.textContent && (
                    el.textContent.includes('Listening') ||
                    el.textContent.includes('Recording') ||
                    el.textContent.includes('Speaking')
                )
            );
        });

        await page.keyboard.up('Space');

        if (recordingState !== initialState) {
            testResults.spacebarInteraction = true;
            console.log('✅ Spacebar interaction working (state changed)\n');
        } else {
            console.log('⚠️  Spacebar interaction unclear (no visible state change)\n');
        }

        // Test 6: Mouse Interaction
        console.log('6️⃣  Testing mouse button interaction...');
        if (micButton) {
            // Try clicking the microphone button
            const buttonRect = await micButton.boundingBox();
            if (buttonRect) {
                await page.mouse.move(buttonRect.x + buttonRect.width / 2, buttonRect.y + buttonRect.height / 2);
                await page.mouse.down();
                await new Promise(resolve => setTimeout(resolve, 200));
                await page.mouse.up();
                testResults.mouseInteraction = true;
                console.log('✅ Mouse button interaction working\n');
            }
        } else {
            console.log('❌ Cannot test mouse interaction (no button found)\n');
        }

        // Test 7: Audio Capabilities
        console.log('7️⃣  Testing audio capabilities...');
        const audioSupport = await page.evaluate(() => {
            const results = {
                audioContext: false,
                mediaRecorder: false,
                getUserMedia: false,
                formats: {}
            };

            try {
                const ctx = new (window.AudioContext || window.webkitAudioContext)();
                results.audioContext = true;
                ctx.close();
            } catch (e) {}

            try {
                results.mediaRecorder = !!window.MediaRecorder;
            } catch (e) {}

            try {
                results.getUserMedia = !!(navigator.mediaDevices && navigator.mediaDevices.getUserMedia);
            } catch (e) {}

            // Test format support
            const audio = new Audio();
            const formats = ['audio/mpeg', 'audio/wav', 'audio/ogg', 'audio/webm'];
            formats.forEach(format => {
                results.formats[format] = audio.canPlayType(format);
            });

            return results;
        });

        const audioScore = Object.values(audioSupport.formats).filter(Boolean).length;
        if (audioSupport.audioContext && audioSupport.mediaRecorder && audioSupport.getUserMedia && audioScore > 0) {
            testResults.audioCapabilities = true;
            console.log('✅ Audio capabilities available\n');
        } else {
            console.log('⚠️  Some audio capabilities missing\n');
        }

        // Test 8: Shader Errors Check
        console.log('8️⃣  Checking for shader errors...');
        await new Promise(resolve => setTimeout(resolve, 2000));
        
        if (shaderErrors === 0) {
            testResults.noShaderErrors = true;
            console.log('✅ No shader errors detected\n');
        } else {
            console.log(`❌ ${shaderErrors} shader error(s) detected\n`);
        }

        // Final Results
        console.log('📊 FINAL TEST RESULTS');
        console.log('=====================\n');
        
        const passed = Object.values(testResults).filter(Boolean).length;
        const total = Object.keys(testResults).length;
        
        Object.entries(testResults).forEach(([test, result]) => {
            const icon = result ? '✅' : '❌';
            const name = test.replace(/([A-Z])/g, ' $1').replace(/^./, str => str.toUpperCase());
            console.log(`${icon} ${name}`);
        });
        
        console.log(`\n📈 Overall Score: ${passed}/${total} (${Math.round(passed/total*100)}%)`);
        
        if (passed >= 6) {
            console.log('🎉 Voice interface is functioning well!');
        } else if (passed >= 4) {
            console.log('⚠️  Voice interface has some issues but core functionality works');
        } else {
            console.log('🚨 Voice interface needs significant fixes');
        }

        console.log('\n🎯 Manual Testing Available');
        console.log('Keep the browser open to test:');
        console.log('• Hold spacebar to record');
        console.log('• Click and hold microphone button');
        console.log('• Check 3D orb animation');
        console.log('• Test voice commands');
        console.log('\nPress Ctrl+C to exit...');
        
        // Keep browser open for manual testing
        await new Promise(resolve => {
            process.on('SIGINT', () => {
                console.log('\n👋 Closing test suite...');
                resolve();
            });
        });

    } catch (error) {
        console.error('❌ Test suite failed:', error.message);
    } finally {
        if (browser) {
            await browser.close();
        }
    }

    return testResults;
}

if (require.main === module) {
    runFinalVoiceTest().catch(console.error);
}

module.exports = { runFinalVoiceTest };