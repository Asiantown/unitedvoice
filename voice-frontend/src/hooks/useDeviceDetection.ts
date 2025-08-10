import { useState, useEffect } from 'react';
import { getDeviceInfo, isTouchDevice, isMobileDevice, shouldUseTouchControls } from '@/lib/utils';

interface DeviceInfo {
  isMobile: boolean;
  isTablet: boolean;
  isDesktop: boolean;
  isTouchDevice: boolean;
  shouldUseTouchControls: boolean;
  platform: string;
  userAgent: string;
}

interface UseDeviceDetectionReturn {
  deviceInfo: DeviceInfo;
  getControlInstructions: () => {
    primary: string;
    secondary?: string;
    keyboardHint?: string;
  };
}

/**
 * Hook for detecting device type and providing appropriate UI instructions
 * Handles mobile/desktop detection and provides context-aware control instructions
 */
export const useDeviceDetection = (): UseDeviceDetectionReturn => {
  const [deviceInfo, setDeviceInfo] = useState<DeviceInfo>(() => {
    // Initial state - will be updated in useEffect
    const info = getDeviceInfo();
    return {
      ...info,
      isTouchDevice: false,
      shouldUseTouchControls: false,
    };
  });

  useEffect(() => {
    // Update device info after component mounts (client-side only)
    const info = getDeviceInfo();
    const touchDevice = isTouchDevice();
    const useTouchControls = shouldUseTouchControls();
    
    console.log('[DeviceDetection] Device info:', {
      ...info,
      isTouchDevice: touchDevice,
      shouldUseTouchControls: useTouchControls,
      userAgent: navigator.userAgent
    });
    
    setDeviceInfo({
      ...info,
      isTouchDevice: touchDevice,
      shouldUseTouchControls: useTouchControls,
    });

    // Listen for orientation changes on mobile devices
    const handleOrientationChange = () => {
      // Small delay to allow for orientation change to complete
      setTimeout(() => {
        const updatedInfo = getDeviceInfo();
        setDeviceInfo(prev => ({
          ...updatedInfo,
          isTouchDevice: isTouchDevice(),
          shouldUseTouchControls: shouldUseTouchControls(),
        }));
      }, 100);
    };

    // Add event listeners for orientation changes
    window.addEventListener('orientationchange', handleOrientationChange);
    window.addEventListener('resize', handleOrientationChange);

    return () => {
      window.removeEventListener('orientationchange', handleOrientationChange);
      window.removeEventListener('resize', handleOrientationChange);
    };
  }, []);

  /**
   * Gets appropriate control instructions based on device type
   */
  const getControlInstructions = () => {
    if (deviceInfo.shouldUseTouchControls) {
      return {
        primary: 'Touch and hold the microphone to talk',
        secondary: 'Release to stop recording',
      };
    } else {
      return {
        primary: 'Press and hold Space or click and hold to talk',
        secondary: 'Click to toggle recording mode',
        keyboardHint: 'Space',
      };
    }
  };

  return {
    deviceInfo,
    getControlInstructions,
  };
};