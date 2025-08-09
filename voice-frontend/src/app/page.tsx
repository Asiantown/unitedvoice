'use client';

import Link from 'next/link';
import { useEffect, useState } from 'react';

export default function Home() {
  const [isLoaded, setIsLoaded] = useState(false);
  const [typedText, setTypedText] = useState('');
  const [particles, setParticles] = useState<any[]>([]);
  const fullText = 'United Voice Agent';

  useEffect(() => {
    setIsLoaded(true);
    
    // Generate particles only on client side
    const generatedParticles = [...Array(30)].map((_, i) => ({
      id: i,
      size: Math.random() * 3 + 2,
      duration: Math.random() * 20 + 15,
      delay: Math.random() * 5,
      startX: Math.random() * 100,
      startY: Math.random() * 100,
    }));
    setParticles(generatedParticles);
    
    // Typewriter effect for main title
    let index = 0;
    const interval = setInterval(() => {
      if (index <= fullText.length) {
        setTypedText(fullText.slice(0, index));
        index++;
      } else {
        clearInterval(interval);
      }
    }, 100);

    return () => clearInterval(interval);
  }, []);

  return (
    <div className="min-h-screen relative overflow-hidden flex flex-col items-center justify-center"
         style={{
           background: 'linear-gradient(135deg, #000000 0%, #0A0A0B 25%, #1A1A1D 50%, #0F0F11 75%, #000000 100%)',
         }}>
      
      {/* Animated Background */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        {/* Floating Particles - only render on client */}
        <div className="absolute inset-0">
          {particles.map((particle) => (
            <div
              key={particle.id}
              className="absolute rounded-full bg-gradient-to-r from-blue-500/20 to-purple-500/20 animate-float"
              style={{
                width: `${particle.size}px`,
                height: `${particle.size}px`,
                left: `${particle.startX}%`,
                top: `${particle.startY}%`,
                animationDuration: `${particle.duration}s`,
                animationDelay: `${particle.delay}s`,
                filter: 'blur(1px)',
                boxShadow: '0 0 10px rgba(59, 130, 246, 0.3)'
              }}
            />
          ))}
        </div>
        
        {/* Gradient Orbs */}
        <div className="absolute top-20 left-20 w-96 h-96 bg-blue-500/5 rounded-full blur-3xl animate-pulse-slow" />
        <div className="absolute bottom-20 right-20 w-80 h-80 bg-purple-500/5 rounded-full blur-3xl animate-pulse-slow" 
             style={{ animationDelay: '2s' }} />
        <div className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] bg-cyan-500/3 rounded-full blur-3xl animate-pulse-slow" 
             style={{ animationDelay: '4s' }} />
      </div>

      {/* Main Content */}
      <div className={`relative z-10 text-center transition-all duration-1000 ${
        isLoaded ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-8'
      }`}>
        
        {/* Hero Title with Typewriter Effect */}
        <div className="mb-6">
          <h1 className="text-6xl md:text-7xl lg:text-8xl font-bold mb-2 text-transparent bg-gradient-to-r from-white via-blue-100 to-cyan-100 bg-clip-text leading-tight"
              style={{
                fontFamily: 'Inter, system-ui, sans-serif',
                fontWeight: 700,
                letterSpacing: '-0.02em',
                textShadow: '0 0 40px rgba(59, 130, 246, 0.3)'
              }}>
            {typedText}
            <span className="animate-pulse text-blue-400">|</span>
          </h1>
          
          {/* Shimmer Effect */}
          <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/20 to-transparent transform -skew-x-12 opacity-0 animate-shimmer" 
               style={{ animation: 'shimmer 3s ease-in-out infinite' }} />
        </div>
        
        {/* Subtitle with Fade-in */}
        <p className={`text-xl md:text-2xl mb-16 text-gray-300 transition-all duration-1000 delay-1000 ${
          isLoaded ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-4'
        }`}
           style={{
             fontFamily: 'Inter, system-ui, sans-serif',
             fontWeight: 400,
             fontSize: '18px',
             lineHeight: '1.6',
             letterSpacing: '0.01em'
           }}>
          AI-powered voice assistant for seamless flight booking
        </p>
        
        {/* Action Button - Single Launch Button */}
        <div className="flex justify-center">
          <Link 
            href="/voice"
            className={`group relative overflow-hidden px-12 py-5 bg-gradient-to-r from-blue-600 via-blue-700 to-blue-800 
                       hover:from-blue-500 hover:via-blue-600 hover:to-blue-700 
                       rounded-2xl text-xl font-semibold transition-all duration-500 
                       transform hover:scale-105 hover:-translate-y-1 
                       shadow-lg shadow-blue-500/25 hover:shadow-xl hover:shadow-blue-500/40 
                       border border-blue-500/30 hover:border-blue-400/50 
                       backdrop-filter backdrop-blur-sm 
                       transition-all duration-1000 delay-1500 ${
              isLoaded ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-4'
            }`}
            style={{
              fontFamily: 'Inter, system-ui, sans-serif',
              fontWeight: 600,
              letterSpacing: '0.01em'
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.animation = 'ripple 0.6s ease-out';
            }}
          >
            {/* Ripple Effect */}
            <div className="absolute inset-0 bg-gradient-to-r from-blue-400/20 to-cyan-400/20 rounded-2xl opacity-0 group-hover:opacity-100 transition-all duration-300 animate-pulse" />
            
            {/* Button Content */}
            <span className="relative z-10 flex items-center gap-3">
              <svg className="w-6 h-6 transform group-hover:rotate-12 transition-transform duration-300" 
                   fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} 
                      d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z" />
              </svg>
              Launch Voice Agent
            </span>
          </Link>
        </div>
      </div>

      <style jsx>{`
        @keyframes float {
          0%, 100% {
            transform: translateY(0px) rotate(0deg);
            opacity: 0.4;
          }
          50% {
            transform: translateY(-20px) rotate(180deg);
            opacity: 0.8;
          }
        }
        
        @keyframes pulse-slow {
          0%, 100% {
            opacity: 0.3;
            transform: scale(1);
          }
          50% {
            opacity: 0.6;
            transform: scale(1.05);
          }
        }
        
        @keyframes shimmer {
          0% {
            transform: translateX(-100%) skew(-12deg);
            opacity: 0;
          }
          50% {
            opacity: 0.6;
          }
          100% {
            transform: translateX(200%) skew(-12deg);
            opacity: 0;
          }
        }
        
        @keyframes ripple {
          0% {
            transform: scale(1);
            box-shadow: 0 0 0 0 rgba(59, 130, 246, 0.4);
          }
          50% {
            transform: scale(1.05);
            box-shadow: 0 0 0 10px rgba(59, 130, 246, 0.1);
          }
          100% {
            transform: scale(1);
            box-shadow: 0 0 0 20px rgba(59, 130, 246, 0);
          }
        }
        
        .animate-pulse-slow {
          animation: pulse-slow 6s ease-in-out infinite;
        }
        
        .animate-float {
          animation: float 15s linear infinite;
        }
        
        .animate-shimmer {
          animation: shimmer 3s ease-in-out infinite;
        }
      `}</style>
    </div>
  );
}