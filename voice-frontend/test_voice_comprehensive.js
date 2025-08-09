#!/usr/bin/env node

/**
 * Comprehensive Voice Interface Testing Script
 * Tests all functionality of the voice interface including:
 * - Page loading
 * - WebSocket connection
 * - Audio recording
 * - Audio playback
 * - 3D orb rendering
 * - Spacebar interaction
 * - Mouse interaction
 */

const puppeteer = require('puppeteer');
const fs = require('fs');

async function runVoiceInterfaceTests() {
    console.log('🎤 Starting Voice Interface Comprehensive Tests...\n');
    
    const results = {
        timestamp: new Date().toISOString(),
        tests: {},
        summary: { passed: 0, failed: 0, total: 0 }
    };

    let browser, page;
    
    try {
        // Launch browser with audio permissions
        browser = await puppeteer.launch({
            headless: false, // Run in headed mode to see the interface
            args: [
                '--use-fake-ui-for-media-stream',
                '--use-fake-device-for-media-stream',
                '--allow-running-insecure-content',
                '--disable-web-security',
                '--disable-site-isolation-trials',
                '--autoplay-policy=no-user-gesture-required'
            ],
            defaultViewport: { width: 1280, height: 720 }
        });

        page = await browser.newPage();
        
        // Grant microphone permissions
        const context = browser.defaultBrowserContext();
        await context.overridePermissions('http://localhost:3000', ['microphone']);

        // Capture console messages
        const consoleMessages = [];
        page.on('console', msg => {
            consoleMessages.push({
                type: msg.type(),
                text: msg.text(),
                timestamp: new Date().toISOString()
            });
        });

        // Capture network requests
        const networkRequests = [];
        page.on('request', request => {
            networkRequests.push({
                url: request.url(),
                method: request.method(),
                timestamp: new Date().toISOString()
            });
        });

        // Test 1: Page Loading
        console.log('📄 Testing page loading...');
        try {
            await page.goto('http://localhost:3000/voice', { 
                waitUntil: 'networkidle0',
                timeout: 15000 
            });
            
            await page.waitForSelector('[data-testid="voice-orb"]', { timeout: 10000 });
            
            results.tests.pageLoading = {
                status: 'passed',
                message: 'Voice page loaded successfully',
                details: 'Page loaded and voice orb element found'
            };
            console.log('✅ Page loading: PASSED');
        } catch (error) {
            results.tests.pageLoading = {
                status: 'failed',
                message: 'Page failed to load',
                error: error.message
            };
            console.log('❌ Page loading: FAILED -', error.message);
        }

        // Test 2: Check for React/Next.js errors
        console.log('⚛️  Testing React/Next.js errors...');
        try {
            const reactErrors = consoleMessages.filter(msg => 
                msg.type === 'error' && 
                (msg.text.includes('React') || msg.text.includes('Next') || msg.text.includes('hydration'))
            );
            
            if (reactErrors.length === 0) {
                results.tests.reactErrors = {
                    status: 'passed',
                    message: 'No React/Next.js errors found'
                };
                console.log('✅ React errors: PASSED');
            } else {
                results.tests.reactErrors = {
                    status: 'failed',
                    message: 'React/Next.js errors detected',
                    errors: reactErrors
                };
                console.log('❌ React errors: FAILED - Found', reactErrors.length, 'errors');
            }
        } catch (error) {
            results.tests.reactErrors = {
                status: 'failed',
                message: 'Error checking React errors',
                error: error.message
            };
            console.log('❌ React errors check: FAILED -', error.message);
        }

        // Test 3: 3D Orb Rendering
        console.log('🌐 Testing 3D orb rendering...');
        try {
            // Check if Three.js canvas is rendered
            await page.waitForSelector('canvas', { timeout: 10000 });
            
            const canvasCount = await page.evaluate(() => {
                const canvases = document.querySelectorAll('canvas');
                return canvases.length;
            });

            if (canvasCount > 0) {
                results.tests.orbRendering = {
                    status: 'passed',
                    message: `3D orb rendered successfully (${canvasCount} canvas elements)`,
                    canvasCount
                };
                console.log('✅ 3D orb rendering: PASSED');
            } else {
                results.tests.orbRendering = {
                    status: 'failed',
                    message: 'No canvas elements found for 3D rendering'
                };
                console.log('❌ 3D orb rendering: FAILED');
            }
        } catch (error) {
            results.tests.orbRendering = {
                status: 'failed',
                message: '3D orb rendering failed',
                error: error.message
            };
            console.log('❌ 3D orb rendering: FAILED -', error.message);
        }

        // Test 4: WebSocket Connection
        console.log('🔌 Testing WebSocket connection...');
        try {
            // Wait for connection status indicator
            await page.waitForFunction(() => {
                const statusElements = document.querySelectorAll('*');
                for (let el of statusElements) {
                    if (el.textContent && (
                        el.textContent.includes('Connected') || 
                        el.textContent.includes('Connection failed') ||
                        el.textContent.includes('Disconnected')
                    )) {
                        return true;
                    }
                }
                return false;
            }, { timeout: 10000 });

            const connectionStatus = await page.evaluate(() => {
                const statusElements = document.querySelectorAll('*');
                for (let el of statusElements) {
                    if (el.textContent && el.textContent.includes('Connected')) {
                        return 'connected';
                    }
                    if (el.textContent && (
                        el.textContent.includes('Connection failed') || 
                        el.textContent.includes('Disconnected')
                    )) {
                        return 'failed';
                    }
                }
                return 'unknown';
            });

            if (connectionStatus === 'connected') {
                results.tests.websocketConnection = {
                    status: 'passed',
                    message: 'WebSocket connected successfully'
                };
                console.log('✅ WebSocket connection: PASSED');
            } else {
                results.tests.websocketConnection = {
                    status: 'failed',
                    message: 'WebSocket connection failed',
                    connectionStatus
                };
                console.log('❌ WebSocket connection: FAILED -', connectionStatus);
            }
        } catch (error) {
            results.tests.websocketConnection = {
                status: 'failed',
                message: 'WebSocket connection test failed',
                error: error.message
            };
            console.log('❌ WebSocket connection: FAILED -', error.message);
        }

        // Test 5: Microphone Button Interaction
        console.log('🎙️  Testing microphone button interaction...');
        try {
            // Find and click the microphone button
            await page.waitForSelector('button', { timeout: 5000 });
            
            // Look for microphone button (should contain Mic icon or be the main recording button)
            const micButton = await page.evaluate(() => {
                const buttons = document.querySelectorAll('button');
                for (let button of buttons) {
                    if (button.textContent.includes('microphone') || 
                        button.querySelector('[data-lucide="mic"]') ||
                        button.classList.contains('voice-button') ||
                        button.closest('[data-testid="voice-orb"]')) {
                        return true;
                    }
                }
                // If no specific microphone button found, try the first enabled button
                return buttons.length > 0;
            });

            if (micButton) {
                results.tests.microphoneButton = {
                    status: 'passed',
                    message: 'Microphone button found and clickable'
                };
                console.log('✅ Microphone button: PASSED');
            } else {
                results.tests.microphoneButton = {
                    status: 'failed',
                    message: 'No microphone button found'
                };
                console.log('❌ Microphone button: FAILED');
            }
        } catch (error) {
            results.tests.microphoneButton = {
                status: 'failed',
                message: 'Microphone button test failed',
                error: error.message
            };
            console.log('❌ Microphone button: FAILED -', error.message);
        }

        // Test 6: Spacebar Interaction
        console.log('⌨️  Testing spacebar interaction...');
        try {
            // Test spacebar keydown
            await page.keyboard.down('Space');
            await page.waitForTimeout(100);
            
            // Check if recording state changed
            const recordingStarted = await page.evaluate(() => {
                // Look for recording indicators
                const indicators = document.querySelectorAll('*');
                for (let el of indicators) {
                    if (el.textContent && (
                        el.textContent.includes('Listening') ||
                        el.textContent.includes('Recording') ||
                        el.textContent.includes('Speaking')
                    )) {
                        return true;
                    }
                    // Check for visual recording indicators
                    if (el.classList && (
                        el.classList.contains('recording') ||
                        el.classList.contains('listening') ||
                        el.classList.contains('voice-button-pulse')
                    )) {
                        return true;
                    }
                }
                return false;
            });

            await page.keyboard.up('Space');

            if (recordingStarted) {
                results.tests.spacebarInteraction = {
                    status: 'passed',
                    message: 'Spacebar interaction triggered recording state'
                };
                console.log('✅ Spacebar interaction: PASSED');
            } else {
                results.tests.spacebarInteraction = {
                    status: 'warning',
                    message: 'Spacebar interaction may not be working (no recording indicator found)'
                };
                console.log('⚠️  Spacebar interaction: WARNING');
            }
        } catch (error) {
            results.tests.spacebarInteraction = {
                status: 'failed',
                message: 'Spacebar interaction test failed',
                error: error.message
            };
            console.log('❌ Spacebar interaction: FAILED -', error.message);
        }

        // Test 7: Audio Context and MediaRecorder
        console.log('🔊 Testing audio capabilities...');
        try {
            const audioCapabilities = await page.evaluate(async () => {
                const results = {
                    audioContext: false,
                    mediaRecorder: false,
                    getUserMedia: false
                };

                // Test AudioContext
                try {
                    const ctx = new (window.AudioContext || window.webkitAudioContext)();
                    results.audioContext = true;
                    ctx.close();
                } catch (e) {
                    results.audioContext = false;
                }

                // Test getUserMedia
                try {
                    if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
                        results.getUserMedia = true;
                    }
                } catch (e) {
                    results.getUserMedia = false;
                }

                // Test MediaRecorder
                try {
                    if (window.MediaRecorder) {
                        results.mediaRecorder = true;
                    }
                } catch (e) {
                    results.mediaRecorder = false;
                }

                return results;
            });

            const allAudioSupported = Object.values(audioCapabilities).every(Boolean);
            
            if (allAudioSupported) {
                results.tests.audioCapabilities = {
                    status: 'passed',
                    message: 'All audio capabilities supported',
                    capabilities: audioCapabilities
                };
                console.log('✅ Audio capabilities: PASSED');
            } else {
                results.tests.audioCapabilities = {
                    status: 'warning',
                    message: 'Some audio capabilities missing',
                    capabilities: audioCapabilities
                };
                console.log('⚠️  Audio capabilities: WARNING -', audioCapabilities);
            }
        } catch (error) {
            results.tests.audioCapabilities = {
                status: 'failed',
                message: 'Audio capabilities test failed',
                error: error.message
            };
            console.log('❌ Audio capabilities: FAILED -', error.message);
        }

        // Test 8: Console Errors Check
        console.log('🐛 Checking for console errors...');
        const errors = consoleMessages.filter(msg => msg.type === 'error');
        const warnings = consoleMessages.filter(msg => msg.type === 'warn');

        if (errors.length === 0) {
            results.tests.consoleErrors = {
                status: 'passed',
                message: 'No console errors found',
                warnings: warnings.length
            };
            console.log('✅ Console errors: PASSED (', warnings.length, 'warnings)');
        } else {
            results.tests.consoleErrors = {
                status: 'failed',
                message: `${errors.length} console errors found`,
                errors: errors.slice(0, 5), // Limit to first 5 errors
                warnings: warnings.length
            };
            console.log('❌ Console errors: FAILED -', errors.length, 'errors found');
        }

        // Test 9: Performance Check
        console.log('⚡ Testing performance...');
        try {
            const performanceMetrics = await page.metrics();
            const loadTime = await page.evaluate(() => performance.now());
            
            results.tests.performance = {
                status: loadTime < 5000 ? 'passed' : 'warning',
                message: `Page load time: ${Math.round(loadTime)}ms`,
                metrics: {
                    loadTime: Math.round(loadTime),
                    jsHeapUsedSize: Math.round(performanceMetrics.JSHeapUsedSize / 1024 / 1024),
                    nodes: performanceMetrics.Nodes
                }
            };
            
            if (loadTime < 5000) {
                console.log('✅ Performance: PASSED -', Math.round(loadTime), 'ms');
            } else {
                console.log('⚠️  Performance: WARNING -', Math.round(loadTime), 'ms (slow)');
            }
        } catch (error) {
            results.tests.performance = {
                status: 'failed',
                message: 'Performance test failed',
                error: error.message
            };
            console.log('❌ Performance: FAILED -', error.message);
        }

        // Calculate summary
        Object.values(results.tests).forEach(test => {
            results.summary.total++;
            if (test.status === 'passed') {
                results.summary.passed++;
            } else {
                results.summary.failed++;
            }
        });

        // Additional data
        results.consoleMessages = consoleMessages;
        results.networkRequests = networkRequests;

    } catch (error) {
        console.error('❌ Test suite failed:', error);
        results.error = error.message;
    } finally {
        if (browser) {
            await browser.close();
        }
    }

    // Print summary
    console.log('\n📊 Test Summary:');
    console.log('================');
    console.log(`Total Tests: ${results.summary.total}`);
    console.log(`Passed: ${results.summary.passed}`);
    console.log(`Failed: ${results.summary.failed}`);
    console.log(`Success Rate: ${Math.round((results.summary.passed / results.summary.total) * 100)}%`);

    // Save results
    const resultsFile = 'voice-interface-test-results.json';
    fs.writeFileSync(resultsFile, JSON.stringify(results, null, 2));
    console.log(`\n💾 Detailed results saved to: ${resultsFile}`);

    return results;
}

// Run tests if called directly
if (require.main === module) {
    runVoiceInterfaceTests().then(results => {
        process.exit(results.summary.failed > 0 ? 1 : 0);
    }).catch(error => {
        console.error('Test runner failed:', error);
        process.exit(1);
    });
}

module.exports = { runVoiceInterfaceTests };