'use client';

import { useState } from 'react';
import { Mic, Wifi, WifiOff } from 'lucide-react';

export default function VoiceSimplePage() {
  const [isRecording, setIsRecording] = useState(false);
  const [isConnected] = useState(false);
  const [messages] = useState<Array<{text: string, sender: 'user' | 'agent', id: string}>>([]);

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-black to-gray-900 text-white">
      <div className="max-w-6xl mx-auto p-8">
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-5xl font-bold mb-4 bg-gradient-to-r from-blue-400 to-purple-600 bg-clip-text text-transparent">
            United Voice Agent (Simple)
          </h1>
          <p className="text-gray-400 text-lg">Simplified version for debugging</p>
          
          {/* Connection Status */}
          <div className="flex items-center justify-center gap-2 mt-4">
            {isConnected ? (
              <Wifi className="w-5 h-5 text-green-500" />
            ) : (
              <WifiOff className="w-5 h-5 text-red-500" />
            )}
            <span className={`px-3 py-1 rounded-full text-sm font-medium ${
              isConnected 
                ? 'bg-green-500/20 text-green-400 border border-green-500/30' 
                : 'bg-red-500/20 text-red-400 border border-red-500/30'
            }`}>
              Testing Mode
            </span>
          </div>
        </div>

        {/* Main Content */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Orb Section */}
          <div className="flex flex-col items-center justify-center">
            <div className="relative">
              {/* Animated Orb Background */}
              <div className={`w-64 h-64 rounded-full bg-gradient-to-r from-blue-500 to-purple-600 opacity-20 blur-3xl absolute -inset-4 ${
                isRecording ? 'animate-pulse' : 'animate-pulse'
              }`} />
              
              {/* Main Orb */}
              <div className={`relative w-64 h-64 rounded-full bg-gradient-to-br from-blue-600 to-purple-700 shadow-2xl flex items-center justify-center transition-all duration-300 ${
                isRecording ? 'scale-110 animate-pulse' : 'hover:scale-105'
              }`}>
                <button
                  onClick={() => setIsRecording(!isRecording)}
                  className={`p-8 rounded-full transition-all ${
                    isRecording 
                      ? 'bg-red-600/30 backdrop-blur' 
                      : 'bg-white/10 backdrop-blur hover:bg-white/20'
                  }`}
                >
                  <Mic className="w-16 h-16 text-white" />
                </button>
              </div>
            </div>
            
            <p className="mt-8 text-gray-400 text-center">
              {isRecording ? 'Recording...' : 'Click to test recording state'}
            </p>
          </div>

          {/* Messages Section */}
          <div className="bg-gray-900/50 backdrop-blur rounded-2xl p-6 border border-gray-800">
            <h2 className="text-xl font-semibold mb-4 text-gray-300">Test Messages</h2>
            <div className="h-96 overflow-y-auto space-y-4 pr-2">
              {messages.length === 0 ? (
                <div className="space-y-4">
                  <p className="text-gray-500 text-center py-8">This is a test page to debug the voice interface...</p>
                  
                  {/* Sample messages */}
                  <div className="flex justify-end">
                    <div className="max-w-xs px-4 py-3 rounded-2xl bg-gradient-to-r from-blue-600 to-blue-700 text-white">
                      <p className="text-sm">Sample user message</p>
                    </div>
                  </div>
                  
                  <div className="flex justify-start">
                    <div className="max-w-xs px-4 py-3 rounded-2xl bg-gray-800 text-gray-100 border border-gray-700">
                      <p className="text-sm">Sample agent response</p>
                    </div>
                  </div>
                </div>
              ) : (
                messages.map((msg) => (
                  <div key={msg.id} className={`flex ${msg.sender === 'user' ? 'justify-end' : 'justify-start'}`}>
                    <div className={`max-w-xs px-4 py-3 rounded-2xl ${
                      msg.sender === 'user' 
                        ? 'bg-gradient-to-r from-blue-600 to-blue-700 text-white' 
                        : 'bg-gray-800 text-gray-100 border border-gray-700'
                    }`}>
                      <p className="text-sm">{msg.text}</p>
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>

        {/* Instructions */}
        <div className="mt-8 text-center text-gray-500 text-sm">
          <p>This is a simplified version for testing. Click the microphone to test state changes.</p>
        </div>
      </div>
    </div>
  );
}