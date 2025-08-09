'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';

export default function TestPage() {
  const [backendStatus, setBackendStatus] = useState('Checking...');
  const [micPermission, setMicPermission] = useState('Not checked');
  const [spacePressed, setSpacePressed] = useState(false);
  const [mousePressed, setMousePressed] = useState(false);

  // Check backend
  useEffect(() => {
    fetch('http://localhost:8000/health')
      .then(res => res.json())
      .then(() => setBackendStatus('✅ Backend is running'))
      .catch(() => setBackendStatus('❌ Backend not available'));
  }, []);

  // Check microphone
  const testMicrophone = async () => {
    try {
      await navigator.mediaDevices.getUserMedia({ audio: true });
      setMicPermission('✅ Microphone access granted');
    } catch {
      setMicPermission('❌ Microphone access denied');
    }
  };

  // Test spacebar
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.code === 'Space') {
        e.preventDefault();
        setSpacePressed(true);
      }
    };
    const handleKeyUp = (e: KeyboardEvent) => {
      if (e.code === 'Space') {
        e.preventDefault();
        setSpacePressed(false);
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    window.addEventListener('keyup', handleKeyUp);
    return () => {
      window.removeEventListener('keydown', handleKeyDown);
      window.removeEventListener('keyup', handleKeyUp);
    };
  }, []);

  return (
    <div className="min-h-screen bg-black text-white p-8">
      <h1 className="text-3xl font-bold mb-8">Voice Agent Test Suite</h1>
      
      <div className="space-y-4 max-w-2xl">
        <div className="bg-gray-900 p-4 rounded">
          <h2 className="font-bold mb-2">Backend Status</h2>
          <p>{backendStatus}</p>
        </div>

        <div className="bg-gray-900 p-4 rounded">
          <h2 className="font-bold mb-2">Microphone Permission</h2>
          <p>{micPermission}</p>
          <button 
            onClick={testMicrophone}
            className="mt-2 px-4 py-2 bg-blue-600 rounded hover:bg-blue-700"
          >
            Test Microphone
          </button>
        </div>

        <div className="bg-gray-900 p-4 rounded">
          <h2 className="font-bold mb-2">Spacebar Test</h2>
          <p>Press and hold spacebar: {spacePressed ? '✅ PRESSED' : '⭕ Released'}</p>
        </div>

        <div className="bg-gray-900 p-4 rounded">
          <h2 className="font-bold mb-2">Mouse Button Test</h2>
          <button
            onMouseDown={() => setMousePressed(true)}
            onMouseUp={() => setMousePressed(false)}
            onMouseLeave={() => setMousePressed(false)}
            className={`px-8 py-4 rounded-lg font-bold transition-all ${
              mousePressed ? 'bg-red-600 scale-110' : 'bg-gray-700 hover:bg-gray-600'
            }`}
          >
            {mousePressed ? '✅ HOLDING' : 'Click and Hold Me'}
          </button>
        </div>

        <div className="bg-gray-900 p-4 rounded">
          <h2 className="font-bold mb-2">Quick Links</h2>
          <div className="space-x-4">
            <Link href="/voice" className="text-blue-400 hover:underline">Voice Interface →</Link>
            <Link href="/" className="text-blue-400 hover:underline">Home →</Link>
          </div>
        </div>
      </div>
    </div>
  );
}

TestPage.displayName = 'TestPage';