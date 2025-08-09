#!/usr/bin/env node
/**
 * WebSocket Connection Test using Node.js Socket.IO client
 * This matches the frontend technology stack better
 */

const { io } = require('socket.io-client');
const fs = require('fs');

class WebSocketTester {
    constructor(serverUrl = 'http://127.0.0.1:8000') {
        this.serverUrl = serverUrl;
        this.socket = null;
        this.connected = false;
        this.messagesReceived = [];
        this.errorsReceived = [];
        this.statusUpdates = [];
    }

    async connectToServer() {
        return new Promise((resolve) => {
            console.log(`🔌 Connecting to ${this.serverUrl}...`);
            
            this.socket = io(this.serverUrl, {
                transports: ['websocket', 'polling'],
                timeout: 10000,
                forceNew: true
            });

            this.socket.on('connect', () => {
                console.log('✅ Connected to WebSocket server');
                this.connected = true;
                resolve(true);
            });

            this.socket.on('disconnect', (reason) => {
                console.log(`❌ Disconnected: ${reason}`);
                this.connected = false;
            });

            this.socket.on('connect_error', (error) => {
                console.error(`❌ Connection error: ${error.message}`);
                resolve(false);
            });

            this.socket.on('connected', (data) => {
                console.log(`🔗 Server connection confirmed:`, data);
                this.messagesReceived.push({ type: 'connected', data, timestamp: new Date().toISOString() });
            });

            this.socket.on('agent_response', (data) => {
                console.log(`🤖 Agent response received: ${data.text?.substring(0, 100)}...`);
                this.messagesReceived.push({ type: 'agent_response', data, timestamp: new Date().toISOString() });
            });

            this.socket.on('transcription', (data) => {
                console.log(`📝 Transcription received: ${data.text}`);
                this.messagesReceived.push({ type: 'transcription', data, timestamp: new Date().toISOString() });
            });

            this.socket.on('status_update', (data) => {
                console.log(`📊 Status update: ${data.status} - ${data.message}`);
                this.statusUpdates.push({ data, timestamp: new Date().toISOString() });
            });

            this.socket.on('error', (data) => {
                console.error(`❌ Server error:`, data);
                this.errorsReceived.push({ data, timestamp: new Date().toISOString() });
            });

            this.socket.on('health_response', (data) => {
                console.log(`🏥 Health response:`, data);
                this.messagesReceived.push({ type: 'health_response', data, timestamp: new Date().toISOString() });
            });

            // Timeout after 10 seconds
            setTimeout(() => {
                if (!this.connected) {
                    console.log('⏰ Connection timeout');
                    resolve(false);
                }
            }, 10000);
        });
    }

    async testConnection() {
        console.log('🧪 Test 1: Basic Connection (No Auto-Greeting)');
        console.log('=' * 50);

        const startTime = Date.now();
        this.messagesReceived = [];
        
        const connected = await this.connectToServer();
        
        if (!connected) {
            return {
                test: 'connection',
                status: 'FAILED',
                reason: 'Could not connect to server',
                duration: (Date.now() - startTime) / 1000
            };
        }

        // Wait for any potential automatic messages
        await new Promise(resolve => setTimeout(resolve, 3000));

        const autoGreetings = this.messagesReceived.filter(msg => msg.type === 'agent_response');
        
        const result = {
            test: 'connection',
            status: autoGreetings.length === 0 ? 'PASSED' : 'FAILED',
            reason: autoGreetings.length === 0 ? 'No automatic greeting sent' : `Received ${autoGreetings.length} automatic greeting(s)`,
            duration: (Date.now() - startTime) / 1000,
            connected: connected,
            messagesReceived: this.messagesReceived.length,
            autoGreetings: autoGreetings.length
        };

        console.log(`✅ Connection test result: ${result.status} - ${result.reason}`);
        return result;
    }

    async testHealthCheck() {
        console.log('\n🧪 Test 2: Health Check');
        console.log('=' * 30);

        const startTime = Date.now();
        const initialCount = this.messagesReceived.length;

        // Send health check
        this.socket.emit('health_check');
        
        // Wait for response
        await new Promise(resolve => setTimeout(resolve, 2000));

        const healthResponses = this.messagesReceived.slice(initialCount).filter(msg => msg.type === 'health_response');

        const result = {
            test: 'health_check',
            status: healthResponses.length > 0 ? 'PASSED' : 'FAILED',
            reason: healthResponses.length > 0 ? 'Health check responded' : 'No health check response',
            duration: (Date.now() - startTime) / 1000,
            responses: healthResponses.length
        };

        if (healthResponses.length > 0) {
            result.healthData = healthResponses[0].data;
            console.log(`   Active Sessions: ${result.healthData.active_sessions}`);
        }

        console.log(`✅ Health check test result: ${result.status} - ${result.reason}`);
        return result;
    }

    async testUserConversation() {
        console.log('\n🧪 Test 3: User-Initiated Conversation');
        console.log('=' * 40);

        const startTime = Date.now();
        const initialCount = this.messagesReceived.length;

        // Create mock audio data (base64 encoded)
        const mockAudioData = Buffer.from('fake audio data for testing').toString('base64');
        
        console.log('🎤 Sending mock audio data...');
        this.socket.emit('audio_data', {
            audio: mockAudioData,
            format: 'webm',
            timestamp: new Date().toISOString()
        });

        // Wait for processing
        await new Promise(resolve => setTimeout(resolve, 8000));

        const newMessages = this.messagesReceived.slice(initialCount);
        const transcriptions = newMessages.filter(msg => msg.type === 'transcription');
        const agentResponses = newMessages.filter(msg => msg.type === 'agent_response');

        const result = {
            test: 'user_conversation',
            status: 'PASSED',
            reason: 'Conversation flow completed',
            duration: (Date.now() - startTime) / 1000,
            transcriptionsReceived: transcriptions.length,
            agentResponsesReceived: agentResponses.length,
            duplicateTranscriptions: transcriptions.length > 1,
            duplicateResponses: agentResponses.length > 1,
            statusUpdatesReceived: this.statusUpdates.length,
            errorsReceived: this.errorsReceived.length
        };

        // Check for issues
        const issues = [];
        if (transcriptions.length > 1) issues.push(`Duplicate transcriptions (${transcriptions.length})`);
        if (agentResponses.length > 1) issues.push(`Duplicate responses (${agentResponses.length})`);
        if (this.errorsReceived.length > 0) issues.push(`Errors received (${this.errorsReceived.length})`);

        if (issues.length > 0) {
            result.status = issues.length > 1 ? 'FAILED' : 'WARNING';
            result.reason = `Issues found: ${issues.join(', ')}`;
        }

        // Add sample data
        if (transcriptions.length > 0) {
            result.sampleTranscription = transcriptions[0].data;
        }
        if (agentResponses.length > 0) {
            result.sampleResponse = {
                text: agentResponses[0].data.text?.substring(0, 100) || '',
                hasAudio: 'audio' in agentResponses[0].data
            };
        }

        console.log(`✅ Conversation test result: ${result.status} - ${result.reason}`);
        return result;
    }

    async disconnect() {
        if (this.socket && this.connected) {
            this.socket.disconnect();
            console.log('🔌 Disconnected from server');
        }
    }

    async runAllTests() {
        console.log('🚀 Starting WebSocket Flow Tests');
        console.log('=' * 50);

        const overallStart = Date.now();
        
        // Test 1: Connection
        const test1Result = await this.testConnection();
        
        if (test1Result.status === 'FAILED') {
            return {
                overallStatus: 'FAILED',
                overallReason: 'Could not establish connection',
                tests: [test1Result],
                duration: (Date.now() - overallStart) / 1000
            };
        }

        // Test 2: Health Check
        const test2Result = await this.testHealthCheck();

        // Test 3: User Conversation
        const test3Result = await this.testUserConversation();

        await this.disconnect();

        // Compile results
        const allTests = [test1Result, test2Result, test3Result];
        
        const failedTests = allTests.filter(t => t.status === 'FAILED');
        const warningTests = allTests.filter(t => t.status === 'WARNING');
        
        let overallStatus = 'PASSED';
        let overallReason = 'All tests passed';
        
        if (failedTests.length > 0) {
            overallStatus = 'FAILED';
            overallReason = `${failedTests.length} test(s) failed`;
        } else if (warningTests.length > 0) {
            overallStatus = 'WARNING';
            overallReason = `${warningTests.length} test(s) have warnings`;
        }

        return {
            overallStatus,
            overallReason,
            tests: allTests,
            totalMessagesReceived: this.messagesReceived.length,
            totalErrorsReceived: this.errorsReceived.length,
            totalStatusUpdates: this.statusUpdates.length,
            duration: (Date.now() - overallStart) / 1000,
            testSummary: {
                passed: allTests.filter(t => t.status === 'PASSED').length,
                warnings: warningTests.length,
                failed: failedTests.length,
                total: allTests.length
            }
        };
    }
}

async function main() {
    console.log('🧪 United Voice Agent - WebSocket Flow Test (Node.js)');
    console.log('=' * 60);

    const tester = new WebSocketTester();

    try {
        const results = await tester.runAllTests();

        // Print results
        console.log('\n' + '=' * 60);
        console.log('📊 FINAL RESULTS');
        console.log('=' * 60);
        
        console.log(`📊 Overall Status: ${results.overallStatus}`);
        console.log(`🔍 Reason: ${results.overallReason}`);
        console.log(`⏱️  Total Duration: ${results.duration.toFixed(2)}s`);
        console.log(`📈 Test Summary: ${results.testSummary.passed}/${results.testSummary.total} passed`);
        
        if (results.testSummary.warnings > 0) {
            console.log(`⚠️  Warnings: ${results.testSummary.warnings}`);
        }
        if (results.testSummary.failed > 0) {
            console.log(`❌ Failed: ${results.testSummary.failed}`);
        }

        console.log(`\n📝 Total Messages: ${results.totalMessagesReceived}`);
        console.log(`❌ Total Errors: ${results.totalErrorsReceived}`);
        console.log(`📊 Status Updates: ${results.totalStatusUpdates}`);

        console.log('\n' + '=' * 60);
        console.log('📋 DETAILED TEST RESULTS');
        console.log('=' * 60);

        results.tests.forEach((test, index) => {
            console.log(`\n${index + 1}. ${test.test.toUpperCase()}`);
            console.log(`   Status: ${test.status}`);
            console.log(`   Duration: ${test.duration.toFixed(2)}s`);
            console.log(`   Reason: ${test.reason}`);

            if (test.test === 'connection') {
                console.log(`   Connected: ${test.connected}`);
                console.log(`   Auto-greetings: ${test.autoGreetings}`);
            } else if (test.test === 'health_check') {
                console.log(`   Responses: ${test.responses}`);
                if (test.healthData) {
                    console.log(`   Active Sessions: ${test.healthData.active_sessions}`);
                }
            } else if (test.test === 'user_conversation') {
                console.log(`   Transcriptions: ${test.transcriptionsReceived}`);
                console.log(`   Agent Responses: ${test.agentResponsesReceived}`);
                console.log(`   Duplicate Trans: ${test.duplicateTranscriptions}`);
                console.log(`   Duplicate Resp: ${test.duplicateResponses}`);
                if (test.sampleResponse) {
                    console.log(`   Has Audio: ${test.sampleResponse.hasAudio}`);
                }
            }
        });

        // Save results
        const resultsFile = `/Users/ryanyin/united-voice-agent/websocket_test_results_${Math.floor(Date.now() / 1000)}.json`;
        fs.writeFileSync(resultsFile, JSON.stringify(results, null, 2));
        console.log(`\n💾 Detailed results saved to: ${resultsFile}`);

        return results.overallStatus === 'PASSED';

    } catch (error) {
        console.error(`❌ Test execution failed: ${error.message}`);
        return false;
    }
}

// Check if socket.io-client is available
try {
    require('socket.io-client');
} catch (error) {
    console.error('❌ socket.io-client not found. Install with: npm install socket.io-client');
    process.exit(1);
}

if (require.main === module) {
    main().then(success => {
        process.exit(success ? 0 : 1);
    }).catch(error => {
        console.error(`❌ Unexpected error: ${error.message}`);
        process.exit(1);
    });
}

module.exports = { WebSocketTester };