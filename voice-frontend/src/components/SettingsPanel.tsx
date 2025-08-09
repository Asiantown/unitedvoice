'use client';

import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { 
  Volume2, 
  Mic, 
  Moon, 
  Sun, 
  Monitor,
  Keyboard, 
  Info, 
  Maximize,
  Minimize,
  ChevronDown,
  ChevronUp,
  Settings,
  Headphones
} from 'lucide-react';

import { Button } from '@/components/ui/button';

interface SettingsPanelProps {
  isFullscreen?: boolean;
  onToggleFullscreen?: () => void;
  onClose?: () => void;
  className?: string;
}

interface AudioDevice {
  deviceId: string;
  label: string;
  kind: 'audioinput' | 'audiooutput';
}

interface KeyboardShortcut {
  keys: string[];
  description: string;
  category: 'voice' | 'navigation' | 'general';
}

const keyboardShortcuts: KeyboardShortcut[] = [
  { keys: ['Space'], description: 'Hold to talk', category: 'voice' },
  { keys: ['Click & Hold'], description: 'Mouse hold to talk', category: 'voice' },
  { keys: ['Enter'], description: 'Toggle recording mode', category: 'voice' },
  { keys: ['Esc'], description: 'Stop recording / Close settings', category: 'voice' },
  { keys: ['⌘', ','], description: 'Open settings', category: 'navigation' },
  { keys: ['F11'], description: 'Toggle fullscreen', category: 'navigation' },
  { keys: ['⌘', 'K'], description: 'Clear conversation', category: 'general' },
];

export const SettingsPanel: React.FC<SettingsPanelProps> = ({
  isFullscreen = false,
  onToggleFullscreen,
  onClose,
  className = ''
}) => {
  const [audioInputDevices, setAudioInputDevices] = useState<AudioDevice[]>([]);
  const [audioOutputDevices, setAudioOutputDevices] = useState<AudioDevice[]>([]);
  const [selectedInputDevice, setSelectedInputDevice] = useState<string>('default');
  const [selectedOutputDevice, setSelectedOutputDevice] = useState<string>('default');
  const [theme, setTheme] = useState<'light' | 'dark' | 'system'>('system');
  const [expandedSections, setExpandedSections] = useState<string[]>(['audio', 'shortcuts']);

  // Load audio devices
  useEffect(() => {
    const loadAudioDevices = async () => {
      try {
        const devices = await navigator.mediaDevices.enumerateDevices();
        
        const inputDevices = devices
          .filter(device => device.kind === 'audioinput')
          .map(device => ({
            deviceId: device.deviceId,
            label: device.label || `Microphone ${device.deviceId.slice(0, 8)}`,
            kind: 'audioinput' as const
          }));

        const outputDevices = devices
          .filter(device => device.kind === 'audiooutput')
          .map(device => ({
            deviceId: device.deviceId,
            label: device.label || `Speaker ${device.deviceId.slice(0, 8)}`,
            kind: 'audiooutput' as const
          }));

        setAudioInputDevices(inputDevices);
        setAudioOutputDevices(outputDevices);
      } catch (error) {
        console.error('Failed to enumerate audio devices:', error);
      }
    };

    loadAudioDevices();

    // Listen for device changes
    navigator.mediaDevices.addEventListener('devicechange', loadAudioDevices);
    return () => {
      navigator.mediaDevices.removeEventListener('devicechange', loadAudioDevices);
    };
  }, []);

  // Load saved preferences
  useEffect(() => {
    const savedInputDevice = localStorage.getItem('voice-input-device');
    const savedOutputDevice = localStorage.getItem('voice-output-device');
    const savedTheme = localStorage.getItem('voice-theme') as 'light' | 'dark' | 'system';

    if (savedInputDevice) setSelectedInputDevice(savedInputDevice);
    if (savedOutputDevice) setSelectedOutputDevice(savedOutputDevice);
    if (savedTheme) setTheme(savedTheme);
  }, []);

  const handleInputDeviceChange = (deviceId: string) => {
    setSelectedInputDevice(deviceId);
    localStorage.setItem('voice-input-device', deviceId);
    // In a real implementation, you'd notify the audio system about the device change
  };

  const handleOutputDeviceChange = (deviceId: string) => {
    setSelectedOutputDevice(deviceId);
    localStorage.setItem('voice-output-device', deviceId);
    // In a real implementation, you'd change the audio output device
  };

  const handleThemeChange = (newTheme: 'light' | 'dark' | 'system') => {
    setTheme(newTheme);
    localStorage.setItem('voice-theme', newTheme);
    
    // Apply theme immediately
    const root = document.documentElement;
    if (newTheme === 'system') {
      const systemPrefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
      root.classList.toggle('dark', systemPrefersDark);
    } else {
      root.classList.toggle('dark', newTheme === 'dark');
    }
  };

  const toggleSection = (sectionId: string) => {
    setExpandedSections(prev => 
      prev.includes(sectionId)
        ? prev.filter(id => id !== sectionId)
        : [...prev, sectionId]
    );
  };

  const getShortcutsByCategory = (category: string) => {
    return keyboardShortcuts.filter(shortcut => shortcut.category === category);
  };

  const renderSection = (
    id: string,
    title: string,
    icon: React.ReactNode,
    children: React.ReactNode
  ) => {
    const isExpanded = expandedSections.includes(id);
    
    return (
      <div className="border-b border-border last:border-b-0">
        <button
          onClick={() => toggleSection(id)}
          className="w-full flex items-center justify-between p-4 hover:bg-muted/30 transition-colors"
        >
          <div className="flex items-center gap-3">
            {icon}
            <span className="font-medium text-foreground">{title}</span>
          </div>
          {isExpanded ? (
            <ChevronUp className="w-4 h-4 text-foreground-muted" />
          ) : (
            <ChevronDown className="w-4 h-4 text-foreground-muted" />
          )}
        </button>
        
        {isExpanded && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.2 }}
            className="px-4 pb-4"
          >
            {children}
          </motion.div>
        )}
      </div>
    );
  };

  return (
    <div className={`flex flex-col h-full ${className}`}>
      <div className="flex-1 overflow-auto">
        {/* Audio Settings */}
        {renderSection('audio', 'Audio Settings', <Volume2 className="w-4 h-4" />, (
          <div className="space-y-4">
            {/* Input Device */}
            <div>
              <label className="flex items-center gap-2 text-sm font-medium text-foreground mb-2">
                <Mic className="w-3 h-3" />
                Microphone
              </label>
              <select
                value={selectedInputDevice}
                onChange={(e) => handleInputDeviceChange(e.target.value)}
                className="w-full p-2 bg-muted border border-border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-accent-blue"
              >
                <option value="default">Default</option>
                {audioInputDevices.map(device => (
                  <option key={device.deviceId} value={device.deviceId}>
                    {device.label}
                  </option>
                ))}
              </select>
            </div>

            {/* Output Device */}
            <div>
              <label className="flex items-center gap-2 text-sm font-medium text-foreground mb-2">
                <Headphones className="w-3 h-3" />
                Audio Output
              </label>
              <select
                value={selectedOutputDevice}
                onChange={(e) => handleOutputDeviceChange(e.target.value)}
                className="w-full p-2 bg-muted border border-border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-accent-blue"
              >
                <option value="default">Default</option>
                {audioOutputDevices.map(device => (
                  <option key={device.deviceId} value={device.deviceId}>
                    {device.label}
                  </option>
                ))}
              </select>
            </div>
          </div>
        ))}

        {/* Appearance Settings */}
        {renderSection('appearance', 'Appearance', <Settings className="w-4 h-4" />, (
          <div className="space-y-4">
            <div>
              <label className="text-sm font-medium text-foreground mb-3 block">Theme</label>
              <div className="grid grid-cols-3 gap-2">
                {[
                  { value: 'light', label: 'Light', icon: Sun },
                  { value: 'dark', label: 'Dark', icon: Moon },
                  { value: 'system', label: 'System', icon: Monitor },
                ].map(({ value, label, icon: Icon }) => (
                  <button
                    key={value}
                    onClick={() => handleThemeChange(value as any)}
                    className={`p-3 rounded-lg border text-xs font-medium transition-colors ${
                      theme === value
                        ? 'bg-accent-blue text-white border-accent-blue'
                        : 'bg-muted border-border hover:bg-muted/80'
                    }`}
                  >
                    <Icon className="w-4 h-4 mx-auto mb-1" />
                    {label}
                  </button>
                ))}
              </div>
            </div>

            {/* Fullscreen Toggle */}
            <div className="flex items-center justify-between">
              <span className="text-sm font-medium text-foreground">Fullscreen Mode</span>
              <Button
                variant="outline"
                size="sm"
                onClick={onToggleFullscreen}
                className="gap-2"
              >
                {isFullscreen ? (
                  <>
                    <Minimize className="w-3 h-3" />
                    Exit
                  </>
                ) : (
                  <>
                    <Maximize className="w-3 h-3" />
                    Enter
                  </>
                )}
              </Button>
            </div>
          </div>
        ))}

        {/* Keyboard Shortcuts */}
        {renderSection('shortcuts', 'Keyboard Shortcuts', <Keyboard className="w-4 h-4" />, (
          <div className="space-y-4">
            {['voice', 'navigation', 'general'].map(category => (
              <div key={category}>
                <h4 className="text-xs font-semibold text-foreground-muted uppercase tracking-wide mb-2">
                  {category.charAt(0).toUpperCase() + category.slice(1)}
                </h4>
                <div className="space-y-2">
                  {getShortcutsByCategory(category).map((shortcut, index) => (
                    <div key={index} className="flex items-center justify-between text-sm">
                      <span className="text-foreground-muted">{shortcut.description}</span>
                      <div className="flex items-center gap-1">
                        {shortcut.keys.map((key, keyIndex) => (
                          <React.Fragment key={keyIndex}>
                            <kbd className="px-2 py-1 bg-muted border border-border rounded text-xs font-mono">
                              {key}
                            </kbd>
                            {keyIndex < shortcut.keys.length - 1 && (
                              <span className="text-foreground-muted">+</span>
                            )}
                          </React.Fragment>
                        ))}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        ))}

        {/* About */}
        {renderSection('about', 'About', <Info className="w-4 h-4" />, (
          <div className="space-y-3">
            <div>
              <h4 className="text-sm font-medium text-foreground mb-1">United Voice Agent</h4>
              <p className="text-xs text-foreground-muted">Version 1.0.0</p>
            </div>
            
            <div>
              <h4 className="text-sm font-medium text-foreground mb-1">Features</h4>
              <ul className="text-xs text-foreground-muted space-y-1">
                <li>• Real-time speech recognition</li>
                <li>• Natural voice synthesis</li>
                <li>• Flight booking assistance</li>
                <li>• 3D voice visualization</li>
              </ul>
            </div>

            <div>
              <h4 className="text-sm font-medium text-foreground mb-1">Support</h4>
              <p className="text-xs text-foreground-muted">
                For technical support, contact your system administrator.
              </p>
            </div>
          </div>
        ))}
      </div>

      {/* Footer Actions */}
      <div className="border-t border-border p-4">
        <Button
          variant="outline"
          className="w-full"
          onClick={() => {
            localStorage.clear();
            window.location.reload();
          }}
        >
          Reset All Settings
        </Button>
      </div>
    </div>
  );
};