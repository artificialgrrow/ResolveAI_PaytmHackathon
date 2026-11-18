import React from 'react';
import { ShieldCheck, ShieldAlert, Zap, Mic, Lock } from 'lucide-react';

export default function HeroMeshBanner() {
  return (
    <div className="relative overflow-hidden border-b border-hairline bg-canvas py-1.5 px-3 sm:px-6 shrink-0">
      {/* Background Mesh Gradient defined in DESIGN.md */}
      <div className="absolute inset-0 geist-mesh-gradient pointer-events-none opacity-40" />

      <div className="relative mx-auto max-w-7xl flex flex-wrap items-center justify-between gap-2">
        <div className="flex items-center gap-2">
          <span className="font-mono text-[10px] uppercase tracking-wider text-mute flex items-center gap-1 bg-white px-2 py-0.5 rounded-sm border border-hairline shadow-whisper">
            <ShieldCheck className="h-3 w-3 text-emerald-600" />
            Paytm QR Armor • Track 3: Autonomous AI Teammates
          </span>
          <span className="hidden sm:inline text-xs font-semibold text-ink">
            Physical QR Security: <span className="text-body font-normal">Visible UPI Destination</span> + <span className="text-link font-medium">Invisible Cryptographic Watermark</span>
          </span>
        </div>

        <div className="flex items-center gap-2 text-[10px] font-mono">
          <div className="flex items-center gap-1 px-2 py-0.5 rounded-sm border border-hairline bg-elevated shadow-whisper">
            <Lock className="h-3 w-3 text-ink" />
            <span>Dual-Binding Provenance</span>
          </div>
          <div className="flex items-center gap-1 px-2 py-0.5 rounded-sm border border-hairline bg-elevated shadow-whisper">
            <Mic className="h-3 w-3 text-link" />
            <span>Voice-First Multilingual</span>
          </div>
          <div className="flex items-center gap-1 px-2 py-0.5 rounded-sm border border-hairline bg-elevated shadow-whisper text-emerald-700">
            <Zap className="h-3 w-3 text-amber-500" />
            <span>Autonomous Security Ops</span>
          </div>
        </div>
      </div>
    </div>
  );
}
