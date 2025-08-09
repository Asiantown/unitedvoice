#!/usr/bin/env node

const puppeteer = require('puppeteer');

async function simpleTest() {
    console.log('🚀 Testing Voice Interface (Fixed Version)...\n');
    
    let browser, page;
    
    try {
        browser = await puppeteer.launch({
            headless: false,
            args: [
                '--use-fake-ui-for-media-stream',
                '--use-fake-device-for-media-stream',
                '--allow-running-insecure-content',
                '--disable-web-security'
            ]
        });

        page = await browser.newPage();
        
        const context = browser.defaultBrowserContext();
        await context.overridePermissions('http://localhost:3000', ['microphone']);

        let errorCount = 0;
        let warningCount = 0;
        
        page.on('console', msg => {
            const text = msg.text();
            const type = msg.type();
            
            if (type === 'error') {
                // Filter out expected/acceptable errors
                if (text.includes('404 (Not Found)') && 
                    (text.includes('icon-') || text.includes('manifest.json'))) {
                    return; // Ignore missing icon/manifest errors
                }
                errorCount++;
                console.log(`❌ [ERROR] ${text}`);
            } else if (type === 'warn') {
                // Filter out acceptable warnings
                if (text.includes('React DevTools') || 
                    text.includes('Audio context initialization failed')) {
                    return; // Ignore expected warnings
                }
                warningCount++;
                console.log(`⚠️  [WARN] ${text}`);
            } else if (type === 'info') {
                console.log(`ℹ️  [INFO] ${text}`);
            }
        });

        console.log('📄 Loading page...');
        await page.goto('http://localhost:3000/voice', { 
            waitUntil: 'domcontentloaded',
            timeout: 20000 
        });

        console.log('✅ Page loaded');

        // Wait for React to initialize
        await new Promise(resolve => setTimeout(resolve, 2000));

        // Check for critical elements
        const tests = [
            {
                name: 'Voice Orb Element',
                check: () => page.$('[data-testid="voice-orb"]')
            },
            {
                name: 'Canvas Elements (3D)',
                check: () => page.$$eval('canvas', els => els.length > 0)
            },
            {
                name: 'Microphone Button',
                check: () => page.$('button')
            },
            {
                name: 'Connection Status',
                check: () => page.evaluate(() => {
                    const elements = Array.from(document.querySelectorAll('*'));
                    return elements.some(el => 
                        el.textContent && (
                            el.textContent.includes('Connected') ||
                            el.textContent.includes('Connecting')
                        )
                    );
                })
            }
        ];

        console.log('\n📋 Running Tests:');
        for (const test of tests) {
            try {
                const result = await test.check();
                console.log(`${result ? '✅' : '❌'} ${test.name}: ${result ? 'PASS' : 'FAIL'}`);
            } catch (error) {
                console.log(`❌ ${test.name}: ERROR - ${error.message}`);
            }
        }

        // Wait a bit more to see if more errors occur
        await new Promise(resolve => setTimeout(resolve, 3000));

        console.log(`\n📊 Summary:`);
        console.log(`❌ Errors: ${errorCount}`);
        console.log(`⚠️  Warnings: ${warningCount}`);
        
        if (errorCount === 0 && warningCount === 0) {
            console.log('🎉 No critical issues found!');
        } else if (errorCount === 0) {
            console.log('✅ No errors, only warnings');
        } else {
            console.log('⚠️  Issues found - check console output');
        }

        console.log('\n🎯 Manual test instructions:');
        console.log('1. Check if the 3D orb is visible and animated');
        console.log('2. Try holding spacebar - should start recording');
        console.log('3. Check WebSocket connection status');
        console.log('4. Try clicking the microphone button');
        console.log('\nBrowser will stay open for 30 seconds...');
        
        await new Promise(resolve => setTimeout(resolve, 30000));

    } catch (error) {
        console.error('❌ Test failed:', error.message);
    } finally {
        if (browser) {
            await browser.close();
        }
    }
}

simpleTest().catch(console.error);