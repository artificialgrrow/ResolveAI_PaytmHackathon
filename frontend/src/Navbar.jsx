import React from 'react';
import { ShieldCheck, Radio, User, LogOut, RefreshCw, RotateCcw, Globe } from 'lucide-react';
import { INDIAN_LANGUAGES } from './languages';

export default function Navbar({
  merchant,
  onLogout,
  onRefreshData,
  onResetScenarios,
  selectedLanguage = 'en',
  onLanguageChange
}) {
  return (
    <header className="sticky top-0 z-40 w-full border-b border-hairline bg-canvas/90 backdrop-blur-md shrink-0">
      <div className="mx-auto flex h-12 max-w-7xl items-center justify-between px-3 sm:px-6">
        {/* Brand */}
        <div className="flex items-center gap-2.5">
          <div className="flex h-7 w-7 items-center justify-center rounded-sm bg-ink text-white font-bold text-xs shadow-whisper">
            ₹
          </div>
          <div className="flex items-baseline gap-1.5">
            <span className="font-semibold text-ink tracking-tight text-sm sm:text-base">Paytm ResolveAI</span>
            <span className="hidden sm:inline font-mono text-[9px] tracking-wider uppercase text-mute bg-hairlineSoft px-1.5 py-0.5 rounded-sm">
              Teammate v1.0
            </span>
          </div>
        </div>

        {/* Center/Right Tools: Language Selector, Status, Merchant Profile */}
        <div className="flex items-center gap-2 sm:gap-3">
          {/* Multi-Language Selector Dropdown */}
          <div className="flex items-center gap-1.5 px-2 py-0.5 rounded-sm border border-hairline bg-elevated text-xs text-bodyText shadow-whisper">
            <Globe className="h-3.5 w-3.5 text-accentBlue shrink-0" />
            <select
              value={selectedLanguage}
              onChange={(e) => onLanguageChange && onLanguageChange(e.target.value)}
              className="bg-transparent text-xs font-medium text-ink focus:outline-none cursor-pointer py-0.5 pr-1 font-sans"
              title="Select Language for Merchant Chat & Final Resolution"
            >
              {INDIAN_LANGUAGES.map((lang) => (
                <option key={lang.code} value={lang.code} className="bg-canvas text-ink py-1">
                  {lang.nativeName} ({lang.name})
                </option>
              ))}
            </select>
          </div>

          <div className="hidden lg:flex items-center gap-1.5 px-2.5 py-1 rounded-full border border-hairline bg-elevated text-xs text-bodyText">
            <span className="relative flex h-2 w-2">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
            </span>
            <span className="font-mono text-[10px]">Autonomous Ops Active</span>
          </div>

          {merchant && (
            <div className="flex items-center gap-1.5 sm:gap-2 pl-2 border-l border-hairline">
              <div className="text-right hidden md:block">
                <div className="text-xs font-medium text-ink leading-tight">{merchant.name}</div>
                <div className="text-[10px] text-mute font-mono">@{merchant.username} • {merchant.bank_name}</div>
              </div>

              <button
                onClick={onResetScenarios}
                title="Reset All 5 Demo Scenarios back to initial stuck state"
                className="flex items-center gap-1 px-2 py-1 text-xs rounded-sm border border-amber-300 bg-amber-50 text-amber-800 hover:bg-amber-100 transition-colors font-mono"
              >
                <RotateCcw className="h-3 w-3" />
                <span className="hidden sm:inline">Reset Demo</span>
              </button>

              <button
                onClick={onRefreshData}
                title="Refresh Ledger"
                className="h-7 w-7 flex items-center justify-center rounded-sm border border-hairline bg-elevated text-bodyText hover:text-ink hover:border-ink transition-colors"
              >
                <RefreshCw className="h-3.5 w-3.5" />
              </button>

              <button
                onClick={onLogout}
                title="Switch Merchant / Logout"
                className="flex items-center gap-1 px-2 py-1 text-xs rounded-sm border border-hairline bg-elevated text-bodyText hover:text-ink hover:border-ink transition-colors"
              >
                <LogOut className="h-3.5 w-3.5" />
                <span className="hidden sm:inline">Switch</span>
              </button>
            </div>
          )}
        </div>
      </div>
    </header>
  );
}
