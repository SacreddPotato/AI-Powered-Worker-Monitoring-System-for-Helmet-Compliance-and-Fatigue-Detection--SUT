import React, { useEffect, useState } from 'react';

export default function VisualEntry({ onComplete }) {
  const [isFading, setIsFading] = useState(false);

  useEffect(() => {
    // Reduced time to 1500ms for a snappier experience
    const timer = setTimeout(() => {
      setIsFading(true);
      setTimeout(onComplete, 600); // Faster fade out
    }, 1500);

    return () => clearTimeout(timer);
  }, [onComplete]);

  return (
    <div className={`fixed inset-0 z-[200] flex flex-col items-center justify-center bg-[#140f1f] transition-all duration-700 ${isFading ? 'opacity-0 scale-95 pointer-events-none' : 'opacity-100'}`}>
      
      {/* ROBOTIC AI EYE / LENS */}
      <div className="relative w-64 h-64 mb-8 flex items-center justify-center translate-y-[-20px]">
        {/* Outer Circular HUD Hub */}
        <div className="absolute w-[140%] h-[140%] rounded-full border border-indigo-500/5 animate-[spin_10s_linear_infinite]"></div>
        <div className="absolute w-[110%] h-[110%] rounded-full border border-dashed border-cyan-500/10 animate-[spin_15s_linear_infinite_reverse]"></div>
        
        <svg viewBox="0 0 100 100" className="w-full h-full drop-shadow-[0_0_40px_rgba(34,211,238,0.4)]">
          <defs>
            <clipPath id="eyeOpening">
               <path d="M10 50 Q 50 12 90 50 Q 50 88 10 50 Z" />
            </clipPath>
            
            <radialGradient id="lensCore" cx="50%" cy="50%" r="50%">
              <stop offset="0%" stopColor="#22d3ee" />
              <stop offset="60%" stopColor="#0891b2" />
              <stop offset="100%" stopColor="#0e7490" />
            </radialGradient>

            <filter id="glow">
                <feGaussianBlur stdDeviation="2.5" result="coloredBlur"/>
                <feMerge>
                    <feMergeNode in="coloredBlur"/>
                    <feMergeNode in="SourceGraphic"/>
                </feMerge>
            </filter>
          </defs>

          {/* Sclera / Background Layer */}
          <path d="M10 50 Q 50 12 90 50 Q 50 88 10 50 Z" fill="#0f172a" stroke="#1e293b" strokeWidth="1" />

          {/* Mechanical / Digital Iris Area */}
          <g clipPath="url(#eyeOpening)">
             {/* Rotating Digital Rings */}
             <circle cx="50" cy="50" r="22" fill="none" stroke="#22d3ee20" strokeWidth="4" />
             <circle cx="50" cy="50" r="22" fill="none" stroke="#22d3ee" strokeWidth="2" strokeDasharray="10 20" className="animate-[spin_4s_linear_infinite]" />
             
             {/* Mechanical Shutter Blades (Simplified visual representation) */}
             <g className="animate-[shutterContract_3s_ease-in-out_infinite]">
                 {/* Shutter segments */}
                 {[0, 60, 120, 180, 240, 300].map((angle) => (
                    <path 
                      key={angle}
                      d="M50 50 L 50 30 Q 60 30 65 37 Z" 
                      fill="#1e293b" 
                      stroke="#334155" 
                      strokeWidth="0.5"
                      transform={`rotate(${angle} 50 50)`}
                    />
                 ))}
             </g>

             {/* The AI Core / Lens */}
             <g filter="url(#glow)">
                <circle cx="50" cy="50" r="10" fill="url(#lensCore)" className="animate-pulse" />
                <circle cx="50" cy="50" r="4" fill="#fff" opacity="0.8" />
                {/* Horizontal Scanline inside lens */}
                <rect x="42" y="49.5" width="16" height="1" fill="#fff" opacity="0.5" className="animate-[lensScan_2s_easeInOut_infinite]" />
             </g>
          </g>

          {/* Eyelid Borders */}
          <path d="M10 50 Q 50 12 90 50 Q 50 88 10 50 Z" fill="none" stroke="#22d3ee" strokeWidth="0.5" opacity="0.3" />
        </svg>
      </div>

      {/* Brand Reveal */}
      <div className="text-center relative z-10">
        <h1 className="text-3xl md:text-5xl font-black tracking-[0.4em] uppercase text-white drop-shadow-[0_0_30px_rgba(255,255,255,0.2)] mb-4">
          Safe Vision AI
        </h1>
        <div className="flex items-center justify-center gap-4">
            <div className="h-[1px] w-12 bg-gradient-to-l from-cyan-500 to-transparent"></div>
            <span className="text-[10px] font-black tracking-[0.8em] text-cyan-500 uppercase opacity-60">Initializing AI Guard</span>
            <div className="h-[1px] w-12 bg-gradient-to-r from-cyan-500 to-transparent"></div>
        </div>
      </div>

      <style>{`
        @keyframes shutterContract {
          0%, 100% { transform: scale(1.1); }
          50% { transform: scale(0.9); }
        }
        @keyframes lensScan {
          0% { transform: translateY(-4px); opacity: 0; }
          50% { opacity: 0.8; }
          100% { transform: translateY(4px); opacity: 0; }
        }
      `}</style>
    </div>
  );
}
