'use client';

import React, { useState } from 'react';
import { useDeviceDetection } from '@/hooks/useDeviceDetection';

/**
 * Test component to verify mobile touch detection functionality
 * This can be temporarily added to test the implementation
 */
export const TouchTestComponent: React.FC = () => {
  const { deviceInfo, getControlInstructions } = useDeviceDetection();
  const [touchCount, setTouchCount] = useState(0);
  const [lastTouchEvent, setLastTouchEvent] = useState<string>('');

  const instructions = getControlInstructions();

  const handleTestTouch = (eventType: string) => {
    setTouchCount(prev => prev + 1);
    setLastTouchEvent(`${eventType} at ${new Date().toLocaleTimeString()}`);
  };

  return (
    <div className="p-6 max-w-md mx-auto bg-card rounded-lg shadow-lg">
      <h3 className="text-lg font-semibold mb-4">Touch Detection Test</h3>
      
      <div className="space-y-2 text-sm mb-4">
        <div><strong>Device Type:</strong> {deviceInfo.isMobile ? 'Mobile' : deviceInfo.isTablet ? 'Tablet' : 'Desktop'}</div>
        <div><strong>Touch Device:</strong> {deviceInfo.isTouchDevice ? 'Yes' : 'No'}</div>
        <div><strong>Should Use Touch:</strong> {deviceInfo.shouldUseTouchControls ? 'Yes' : 'No'}</div>
        <div><strong>Platform:</strong> {deviceInfo.platform}</div>
      </div>

      <div className="space-y-2 text-sm mb-4">
        <div><strong>Primary Instruction:</strong> {instructions.primary}</div>
        {instructions.secondary && <div><strong>Secondary:</strong> {instructions.secondary}</div>}
        {instructions.keyboardHint && <div><strong>Keyboard Hint:</strong> {instructions.keyboardHint}</div>}
      </div>

      <button
        className="w-full p-4 bg-blue-600 hover:bg-blue-700 text-white rounded-lg touch-button touch-target"
        onTouchStart={() => handleTestTouch('Touch Start')}
        onTouchEnd={() => handleTestTouch('Touch End')}
        onTouchCancel={() => handleTestTouch('Touch Cancel')}
        onClick={() => handleTestTouch('Click')}
      >
        Test Touch/Click
      </button>

      <div className="mt-4 text-sm">
        <div><strong>Touch Count:</strong> {touchCount}</div>
        <div><strong>Last Event:</strong> {lastTouchEvent}</div>
      </div>
    </div>
  );
};