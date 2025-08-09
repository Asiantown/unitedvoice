'use client';

import React, { useRef, useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import WaveSurfer from 'wavesurfer.js';

interface AudioWaveformProps {
  isRecording: boolean;
  audioLevel?: number;
  audioData?: Float32Array | null;
  width?: number;
  height?: number;
  barCount?: number;
  className?: string;
  theme?: 'blue' | 'purple' | 'gradient';
  style?: 'bars' | 'wave' | 'dots';
}

export const AudioWaveform: React.FC<AudioWaveformProps> = ({
  isRecording,
  audioLevel = 0,
  audioData = null,
  width = 200,
  height = 60,
  barCount = 24,
  className = '',
  theme = 'gradient',
  style = 'bars'
}) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const waveSurferRef = useRef<WaveSurfer | null>(null);
  const animationRef = useRef<number | null>(null);
  const [animationTime, setAnimationTime] = useState(0);
  const animationFrameRef = useRef<number | null>(null);

  // Theme colors
  const themes = {
    blue: {
      primary: '#3B82F6',
      secondary: '#60A5FA',
      gradient: ['#3B82F6', '#60A5FA', '#93C5FD']
    },
    purple: {
      primary: '#A855F7',
      secondary: '#C084FC',
      gradient: ['#A855F7', '#C084FC', '#DDD6FE']
    },
    gradient: {
      primary: '#3B82F6',
      secondary: '#A855F7',
      gradient: ['#3B82F6', '#8B5CF6', '#A855F7', '#EC4899']
    }
  };

  const currentTheme = themes[theme];

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    // Set canvas size
    canvas.width = width;
    canvas.height = height;

    const animate = () => {
      setAnimationTime(prev => prev + 0.016); // ~60fps
      
      ctx.clearRect(0, 0, width, height);

      if (!isRecording) {
        // Idle state - subtle breathing effect
        drawIdleState(ctx, width, height, animationTime, currentTheme);
      } else {
        // Active recording state
        switch (style) {
          case 'bars':
            drawBars(ctx, width, height, audioLevel, barCount, animationTime, currentTheme);
            break;
          case 'wave':
            drawWave(ctx, width, height, audioData || generateMockWaveform(audioLevel), currentTheme);
            break;
          case 'dots':
            drawDots(ctx, width, height, audioLevel, animationTime, currentTheme);
            break;
        }
      }

      animationRef.current = requestAnimationFrame(animate);
    };

    animate();

    return () => {
      if (animationRef.current) {
        cancelAnimationFrame(animationRef.current);
      }
    };
  }, [isRecording, audioLevel, audioData, width, height, barCount, theme, style, animationTime]);

  const drawIdleState = (
    ctx: CanvasRenderingContext2D,
    w: number,
    h: number,
    time: number,
    theme: typeof currentTheme
  ) => {
    const centerX = w / 2;
    const centerY = h / 2;
    
    // Create gradient
    const gradient = ctx.createRadialGradient(centerX, centerY, 0, centerX, centerY, w / 4);
    gradient.addColorStop(0, `${theme.primary}40`);
    gradient.addColorStop(1, `${theme.primary}10`);
    
    ctx.fillStyle = gradient;
    
    // Gentle pulsing circle
    const radius = 15 + Math.sin(time * 2) * 3;
    ctx.beginPath();
    ctx.arc(centerX, centerY, radius, 0, Math.PI * 2);
    ctx.fill();
    
    // Subtle dots around the center
    for (let i = 0; i < 6; i++) {
      const angle = (i / 6) * Math.PI * 2 + time;
      const dotRadius = 25 + Math.sin(time * 3 + i) * 5;
      const x = centerX + Math.cos(angle) * dotRadius;
      const y = centerY + Math.sin(angle) * dotRadius;
      
      ctx.fillStyle = `${theme.secondary}30`;
      ctx.beginPath();
      ctx.arc(x, y, 2, 0, Math.PI * 2);
      ctx.fill();
    }
  };

  const drawBars = (
    ctx: CanvasRenderingContext2D,
    w: number,
    h: number,
    level: number,
    count: number,
    time: number,
    theme: typeof currentTheme
  ) => {
    const barWidth = (w - (count - 1) * 2) / count;
    const maxHeight = h * 0.8;
    
    // Create gradient
    const gradient = ctx.createLinearGradient(0, h, 0, 0);
    theme.gradient.forEach((color, index) => {
      gradient.addColorStop(index / (theme.gradient.length - 1), color);
    });
    
    ctx.fillStyle = gradient;
    
    for (let i = 0; i < count; i++) {
      // Create varied heights based on audio level and some randomness
      const baseHeight = level * maxHeight;
      const variation = Math.sin(time * 4 + i * 0.5) * 0.3 + Math.random() * 0.2;
      const barHeight = Math.max(2, baseHeight * (0.5 + variation));
      
      const x = i * (barWidth + 2);
      const y = (h - barHeight) / 2;
      
      // Add rectangle (rounded rect not universally supported)
      ctx.beginPath();
      ctx.rect(x, y, barWidth, barHeight);
      ctx.fill();
      
      // Add glow effect
      ctx.shadowBlur = 4;
      ctx.shadowColor = theme.primary;
      ctx.fill();
      ctx.shadowBlur = 0;
    }
  };

  const drawWave = (
    ctx: CanvasRenderingContext2D,
    w: number,
    h: number,
    data: Float32Array,
    theme: typeof currentTheme
  ) => {
    if (!data || data.length === 0) return;
    
    // Create gradient
    const gradient = ctx.createLinearGradient(0, 0, w, 0);
    theme.gradient.forEach((color, index) => {
      gradient.addColorStop(index / (theme.gradient.length - 1), color);
    });
    
    ctx.strokeStyle = gradient;
    ctx.lineWidth = 2;
    ctx.lineCap = 'round';
    ctx.lineJoin = 'round';
    
    ctx.beginPath();
    
    const sliceWidth = w / data.length;
    let x = 0;
    
    for (let i = 0; i < data.length; i++) {
      const v = (data[i] + 1) / 2; // Normalize from [-1, 1] to [0, 1]
      const y = v * h;
      
      if (i === 0) {
        ctx.moveTo(x, y);
      } else {
        ctx.lineTo(x, y);
      }
      
      x += sliceWidth;
    }
    
    ctx.stroke();
    
    // Add glow effect
    ctx.shadowBlur = 8;
    ctx.shadowColor = theme.primary;
    ctx.stroke();
    ctx.shadowBlur = 0;
  };

  const drawDots = (
    ctx: CanvasRenderingContext2D,
    w: number,
    h: number,
    level: number,
    time: number,
    theme: typeof currentTheme
  ) => {
    const dotCount = 15;
    const centerX = w / 2;
    const centerY = h / 2;
    
    // Create gradient
    const gradient = ctx.createRadialGradient(centerX, centerY, 0, centerX, centerY, w / 2);
    theme.gradient.forEach((color, index) => {
      gradient.addColorStop(index / (theme.gradient.length - 1), color);
    });
    
    ctx.fillStyle = gradient;
    
    for (let i = 0; i < dotCount; i++) {
      const angle = (i / dotCount) * Math.PI * 2 + time * 2;
      const baseRadius = 20;
      const radiusVariation = level * 15 + Math.sin(time * 6 + i) * 8;
      const radius = baseRadius + radiusVariation;
      
      const x = centerX + Math.cos(angle) * radius;
      const y = centerY + Math.sin(angle) * radius;
      
      const dotSize = 2 + level * 3 + Math.sin(time * 4 + i) * 1;
      
      ctx.beginPath();
      ctx.arc(x, y, dotSize, 0, Math.PI * 2);
      ctx.fill();
      
      // Add glow
      ctx.shadowBlur = 6;
      ctx.shadowColor = theme.primary;
      ctx.fill();
      ctx.shadowBlur = 0;
    }
  };

  // Generate mock waveform data when no real data is available
  const generateMockWaveform = (level: number): Float32Array => {
    const data = new Float32Array(128);
    for (let i = 0; i < data.length; i++) {
      data[i] = (Math.random() - 0.5) * level * 2;
    }
    return data;
  };

  return (
    <motion.div
      className={`relative ${className}`}
      initial={{ opacity: 0, scale: 0.9 }}
      animate={{ 
        opacity: isRecording ? 1 : 0.7, 
        scale: isRecording ? 1 : 0.95 
      }}
      transition={{ duration: 0.3 }}
      data-testid="audio-waveform"
    >
      <canvas
        ref={canvasRef}
        className="rounded-lg bg-background/30 backdrop-blur-sm border border-border/50"
        style={{ 
          width: `${width}px`, 
          height: `${height}px`,
          filter: isRecording ? 'none' : 'blur(0.5px)'
        }}
      />
      
      {/* Overlay effects */}
      {isRecording && (
        <div className="absolute inset-0 rounded-lg bg-gradient-to-r from-transparent via-white/5 to-transparent animate-shimmer pointer-events-none" />
      )}
    </motion.div>
  );
};