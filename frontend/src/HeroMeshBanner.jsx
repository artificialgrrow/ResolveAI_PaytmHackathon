import React from 'react';
import { Bot, Shield, Zap, Sparkles } from 'lucide-react';

export default function HeroMeshBanner() {
  return (
    <div className="relative overflow-hidden border-b border-hairline bg-canvas py-1.5 px-3 sm:px-6 shrink-0">
      {/* Background Mesh Gradient */}
      <div className="absolute inset-0 geist-mesh-gradient pointer-events-none" />

      <div className="relative mx-auto max-w-7xl flex flex-wrap items-center justify-between gap-2">
        <div className="flex items-center gap-2">
          <span className="font-mono text-[10px] uppercase tracking-wider text-mute flex items-center gap-1 bg-hairlineSoft px-1.5 py-0.5 rounded-sm">
            <Bot className="h-3 w-3 text-accentBlue" />
            Hackathon Track 3: Autonomous AI Teammates
          </span>
          <span className="hidden sm:inline text-xs font-semibold text-ink">
            ResolveAI: <span className="text-bodyText font-normal">Don't tell merchants what to do.</span> <span className="text-accentBlue font-medium">Do it for them.</span>
          </span>
        </div>

        <div className="flex items-center gap-2 text-[10px] font-mono">
          <div className="flex items-center gap-1 px-2 py-0.5 rounded-sm border border-hairline bg-elevated shadow-whisper">
            <Zap className="h-3 w-3 text-amber-500" />
            <span>≤ ₹25,000 Auto-Fix</span>
          </div>
          <div className="flex items-center gap-1 px-2 py-0.5 rounded-sm border border-hairline bg-elevated shadow-whisper">
            <Shield className="h-3 w-3 text-accentBlue" />
            <span>Human-in-Loop Safe</span>
          </div>
        </div>
      </div>
    </div>
  );
}
