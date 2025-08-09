#!/usr/bin/env node
/**
 * Node.js Socket.IO WebSocket Test Script
 * Tests connection to United Voice Agent WebSocket server
 */

const { io } = require('socket.io-client');
const fs = require('fs');

// Test configuration
const SERVER_URL = 'http://localhost:8000';
const TEST_TIMEOUT = 30000; // 30 seconds
const RECONNECTION_ATTEMPTS = 3;

class WebSocketTester {
    constructor() {
        this.testResults = [];
        this.socket = null;
        this.isConnected = false;
        this.receivedGreeting = false;
        this.receivedConnectedEvent = false;
    }

    log(level, message, data = null) {
        const timestamp = new Date().toISOString();
        const logEntry = {
            timestamp,
            level,
            message,
            data
        };
        
        console.log(`[${timestamp}] ${level.toUpperCase()}: ${message}`);
        if (data) {
            console.log('Data:', JSON.stringify(data, null, 2));
        }
        
        this.testResults.push(logEntry);
    }

    async runComprehensiveTests() {
        console.log('🚀 Starting comprehensive WebSocket tests...');
        console.log('=' .repeat(60));
        
        try {
            // Test 1: Basic Connection
            await this.testBasicConnection();
            
            // Test 2: Event Handling
            await this.testEventHandling();
            
            // Test 3: Message Exchange
            await this.testMessageExchange();
            
            // Test 4: Health Check
            await this.testHealthCheck();
            
            // Test 5: Session State
            await this.testSessionState();
            
            // Test 6: Error Handling
            await this.testErrorHandling();
            
            // Test 7: Disconnection
            await this.testDisconnection();
            
        } catch (error) {
            this.log('error', 'Test suite failed', { error: error.message });
        } finally {
            this.cleanup();
            this.generateReport();
        }
    }

    async testBasicConnection() {
        return new Promise((resolve, reject) => {
            this.log('info', 'Testing basic connection...');
            
            const timeout = setTimeout(() => {
                this.log('error', 'Connection timeout after 10 seconds');
                reject(new Error('Connection timeout'));
            }, 10000);
            
            this.socket = io(SERVER_URL, {
                timeout: 5000,
                reconnectionAttempts: RECONNECTION_ATTEMPTS,
                transports: ['websocket', 'polling']
            });

            this.socket.on('connect', () => {
                this.isConnected = true;
                this.log('success', 'Successfully connected to WebSocket server', {
                    socketId: this.socket.id,
                    transport: this.socket.io.engine.transport.name
                });
                clearTimeout(timeout);
                resolve();
            });

            this.socket.on('connect_error', (error) => {
                this.log('error', 'Connection error', { 
                    error: error.message,
                    description: error.description 
                });
                clearTimeout(timeout);
                reject(error);
            });

            this.socket.on('disconnect', (reason) => {
                this.log('warning', 'Disconnected from server', { reason });
                this.isConnected = false;
            });
        });
    }

    async testEventHandling() {
        return new Promise((resolve) => {
            this.log('info', 'Testing event handling...');
            
            let eventsReceived = 0;
            const expectedEvents = ['connected', 'agent_response'];
            
            const timeout = setTimeout(() => {
                this.log('warning', `Event handling test completed. Received ${eventsReceived}/${expectedEvents.length} expected events`);
                resolve();
            }, 5000);

            // Listen for 'connected' event
            this.socket.on('connected', (data) => {
                this.receivedConnectedEvent = true;
                eventsReceived++;
                this.log('success', 'Received "connected" event', data);
                
                if (eventsReceived >= expectedEvents.length) {
                    clearTimeout(timeout);
                    resolve();
                }
            });

            // Listen for agent response (greeting)
            this.socket.on('agent_response', (data) => {
                this.receivedGreeting = true;
                eventsReceived++;
                this.log('success', 'Received "agent_response" event', {
                    text: data.text ? data.text.substring(0, 100) + '...' : 'No text',
                    intent: data.intent,
                    hasAudio: !!data.audio,
                    timestamp: data.timestamp
                });
                
                if (eventsReceived >= expectedEvents.length) {
                    clearTimeout(timeout);
                    resolve();
                }
            });

            // Listen for other events
            this.socket.on('status_update', (data) => {
                this.log('info', 'Received status update', data);
            });

            this.socket.on('error', (data) => {
                this.log('error', 'Received error event', data);
            });
        });
    }

    async testMessageExchange() {
        return new Promise((resolve) => {
            this.log('info', 'Testing message exchange...');
            
            // Test sending audio data with mock base64 audio
            const mockAudioData = {
                audio: Buffer.from('mock audio data').toString('base64'),
                format: 'webm',
                timestamp: new Date().toISOString()
            };

            let responseReceived = false;
            const timeout = setTimeout(() => {
                if (!responseReceived) {
                    this.log('warning', 'No response received for audio data test');
                }
                resolve();
            }, 10000);

            // Listen for transcription response
            this.socket.on('transcription', (data) => {
                this.log('success', 'Received transcription', data);
            });

            // Listen for agent response
            this.socket.on('agent_response', (data) => {
                if (!this.receivedGreeting) {
                    return; // Skip greeting response
                }
                responseReceived = true;
                this.log('success', 'Received agent response to audio', {
                    hasText: !!data.text,
                    hasAudio: !!data.audio,
                    intent: data.intent
                });
                clearTimeout(timeout);
                resolve();
            });

            // Send mock audio data
            this.log('info', 'Sending mock audio data...');
            this.socket.emit('audio_data', mockAudioData);
        });
    }

    async testHealthCheck() {
        return new Promise((resolve) => {
            this.log('info', 'Testing health check...');
            
            const timeout = setTimeout(() => {
                this.log('warning', 'Health check timeout');
                resolve();
            }, 5000);

            this.socket.on('health_response', (data) => {
                this.log('success', 'Received health response', data);
                clearTimeout(timeout);
                resolve();
            });

            this.socket.emit('health_check');
        });
    }

    async testSessionState() {
        return new Promise((resolve) => {
            this.log('info', 'Testing session state...');
            
            const timeout = setTimeout(() => {
                this.log('warning', 'Session state test timeout');
                resolve();
            }, 5000);

            this.socket.on('session_state', (data) => {
                this.log('success', 'Received session state', data);
                clearTimeout(timeout);
                resolve();
            });

            this.socket.emit('get_session_state');
        });
    }

    async testErrorHandling() {
        return new Promise((resolve) => {
            this.log('info', 'Testing error handling...');
            
            let errorReceived = false;
            const timeout = setTimeout(() => {
                if (!errorReceived) {
                    this.log('info', 'No error event received (this might be expected)');
                }
                resolve();
            }, 5000);

            this.socket.on('error', (data) => {
                errorReceived = true;
                this.log('info', 'Received error event (expected for invalid data)', data);
                clearTimeout(timeout);
                resolve();
            });

            // Send invalid audio data to trigger error
            this.socket.emit('audio_data', { invalid: 'data' });
        });
    }

    async testDisconnection() {
        return new Promise((resolve) => {
            this.log('info', 'Testing graceful disconnection...');
            
            this.socket.on('disconnect', (reason) => {
                this.log('success', 'Successfully disconnected', { reason });
                resolve();
            });

            setTimeout(() => {
                this.socket.disconnect();
            }, 1000);
        });
    }

    cleanup() {
        if (this.socket && this.socket.connected) {
            this.socket.disconnect();
        }
    }

    generateReport() {
        console.log('\n' + '=' .repeat(60));
        console.log('📊 WEBSOCKET TEST REPORT');
        console.log('=' .repeat(60));
        
        const summary = {
            totalTests: 7,
            connectionSuccessful: this.isConnected || this.receivedConnectedEvent,
            receivedConnectedEvent: this.receivedConnectedEvent,
            receivedGreeting: this.receivedGreeting,
            errorsEncountered: this.testResults.filter(r => r.level === 'error').length,
            warningsEncountered: this.testResults.filter(r => r.level === 'warning').length,
            totalLogEntries: this.testResults.length
        };

        console.log('Summary:');
        console.log(`✅ Connection Established: ${summary.connectionSuccessful ? 'YES' : 'NO'}`);
        console.log(`✅ Received 'connected' Event: ${summary.receivedConnectedEvent ? 'YES' : 'NO'}`);
        console.log(`✅ Received Greeting: ${summary.receivedGreeting ? 'YES' : 'NO'}`);
        console.log(`⚠️  Errors: ${summary.errorsEncountered}`);
        console.log(`⚠️  Warnings: ${summary.warningsEncountered}`);
        
        // Write detailed results to file
        const reportPath = '/Users/ryanyin/united-voice-agent/websocket_test_node_results.json';
        const report = {
            timestamp: new Date().toISOString(),
            summary,
            detailedResults: this.testResults
        };
        
        fs.writeFileSync(reportPath, JSON.stringify(report, null, 2));
        console.log(`\n📄 Detailed report saved to: ${reportPath}`);
        
        // Overall assessment
        const overallSuccess = summary.connectionSuccessful && 
                               summary.receivedConnectedEvent && 
                               summary.errorsEncountered === 0;
        
        console.log(`\n🎯 Overall Assessment: ${overallSuccess ? 'PASS ✅' : 'NEEDS ATTENTION ⚠️'}`);
        
        if (!overallSuccess) {
            console.log('\n🔧 Issues to investigate:');
            if (!summary.connectionSuccessful) console.log('  • WebSocket connection failed');
            if (!summary.receivedConnectedEvent) console.log('  • Server did not send "connected" event');
            if (summary.errorsEncountered > 0) console.log('  • Connection errors occurred');
        }
    }
}

// Install required packages if not available
function checkDependencies() {
    try {
        require('socket.io-client');
        return true;
    } catch (error) {
        console.log('❌ Missing socket.io-client dependency');
        console.log('Please install it with: npm install socket.io-client');
        return false;
    }
}

// Main execution
if (require.main === module) {
    if (!checkDependencies()) {
        process.exit(1);
    }
    
    const tester = new WebSocketTester();
    tester.runComprehensiveTests().then(() => {
        console.log('\n✅ Test suite completed');
        process.exit(0);
    }).catch((error) => {
        console.error('\n❌ Test suite failed:', error.message);
        process.exit(1);
    });
}

module.exports = WebSocketTester;