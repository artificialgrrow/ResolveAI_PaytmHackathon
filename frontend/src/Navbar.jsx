import React from 'react';
import { ShieldCheck, Radio, Globe, RotateCcw } from 'lucide-react';
import { INDIAN_LANGUAGES } from './languages';

export default function Navbar({
  selectedLanguage = 'en',
  onLanguageChange,
  onResetDemo
}) {
  return (
    <header className="sticky top-0 z-40 w-full border-b border-hairline bg-canvas/95 backdrop-blur-md shrink-0">
      <div className="mx-auto flex h-12 max-w-7xl items-center justify-between px-3 sm:px-6">
        {/* Brand */}
        <div className="flex items-center gap-2.5">
          <div className="flex h-7 w-7 items-center justify-center rounded-sm bg-ink text-white font-bold text-xs shadow-whisper">
            ₹
          </div>
          <div className="flex items-baseline gap-1.5">
            <span className="font-semibold text-ink tracking-tight text-sm sm:text-base font-sans">
              Paytm QR Armor
            </span>
            <span className="hidden sm:inline font-mono text-[9px] tracking-wider uppercase text-mute bg-hairlineSoft px-1.5 py-0.5 rounded-sm">
              Provenance Agent v2.0
            </span>
          </div>
        </div>

        {/* Center/Right Tools */}
        <div className="flex items-center gap-2 sm:gap-3">
          {/* Multi-Language Dropdown */}
          <div className="flex items-center gap-1.5 px-2 py-0.5 rounded-sm border border-hairline bg-elevated text-xs text-body shadow-whisper">
            <Globe className="h-3.5 w-3.5 text-link shrink-0" />
            <select
              value={selectedLanguage}
              onChange={(e) => onLanguageChange && onLanguageChange(e.target.value)}
              className="bg-transparent text-xs font-medium text-ink focus:outline-none cursor-pointer py-0.5 pr-1 font-sans"
              title="Select Regional Language for Voice Agent"
            >
              {INDIAN_LANGUAGES.map((lang) => (
                <option key={lang.code} value={lang.code} className="bg-canvas text-ink py-1">
                  {lang.nativeName} ({lang.name})
                </option>
              ))}
            </select>
          </div>

          {/* Autonomous Status indicator */}
          <div className="hidden md:flex items-center gap-1.5 px-2.5 py-1 rounded-full border border-hairline bg-elevated text-xs text-body shadow-whisper">
            <span className="relative flex h-2 w-2">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
            </span>
            <span className="font-mono text-[10px]">Dual-Binding Active</span>
          </div>

          {/* Reset Button */}
          {onResetDemo && (
            <button
              onClick={onResetDemo}
              title="Reset Demo State"
              className="flex items-center gap-1 px-2.5 py-1 text-xs rounded-sm border border-hairline bg-elevated hover:bg-slate-50 text-body hover:text-ink transition-colors font-mono shadow-whisper"
            >
              <RotateCcw className="h-3 w-3" />
              <span className="hidden sm:inline">Reset State</span>
            </button>
          )}
        </div>
      </div>
    </header>
  );
}
