import React, { useState } from 'react';
import AgentPipelineFlow from './AgentPipelineFlow';
import SupervisorApprovalModal from './SupervisorApprovalModal';
import LedgerPipelineCard from './LedgerPipelineCard';
import SoundboxCard from './SoundboxCard';
import TerminalTrace from './TerminalTrace';
import AntiTamperQRView from './AntiTamperQRView';
import { Columns, Square, ShieldCheck } from 'lucide-react';

export default function OpsCenterPane({
  events,
  isStreaming,
  currentIncidentId,
  pendingApproval,
  onApprove,
  onReject,
  isApproving,
  merchantData,
  currentMerchant,
  onSoundboxUpdated,
  onClearTrace
}) {
  const [activeTab, setActiveTab] = useState('pipeline'); // 'pipeline' | 'terminal' | 'soundbox' | 'stego_qr'
  const [splitView, setSplitView] = useState(false);

  return (
    <div className="h-full flex flex-col min-h-0 space-y-2">
      {/* 1. Cinematic Multi-Agent Flow Diagram */}
      <AgentPipelineFlow
        events={events}
        isStreaming={isStreaming}
        currentIncidentId={currentIncidentId}
      />

      {/* 2. Human-in-the-Loop Approval Banner (Appears on > 25k Threshold Breach) */}
      {pendingApproval && (
        <SupervisorApprovalModal
          pendingApproval={pendingApproval}
          onApprove={onApprove}
          onReject={onReject}
          isApproving={isApproving}
        />
      )}

      {/* 3. Bottom Operations Area: Tabbed or Split View */}
      <div className="flex-1 min-h-0 flex flex-col">
        {/* Tab & View Mode Header */}
        <div className="flex items-center justify-between border-b border-hairline pb-1.5 shrink-0 mb-2">
          <div className="flex items-center gap-1">
            <button
              onClick={() => { setActiveTab('pipeline'); setSplitView(false); }}
              className={`px-2.5 py-1 text-xs font-mono rounded-sm transition-colors ${
                !splitView && activeTab === 'pipeline'
                  ? 'bg-ink text-white font-medium shadow-whisper'
                  : 'text-bodyText hover:text-ink bg-canvas'
              }`}
            >
              Settlement Pipeline
            </button>

            <button
              onClick={() => { setActiveTab('terminal'); setSplitView(false); }}
              className={`flex items-center gap-1.5 px-2.5 py-1 text-xs font-mono rounded-sm transition-colors ${
                !splitView && activeTab === 'terminal'
                  ? 'bg-ink text-white font-medium shadow-whisper'
                  : 'text-bodyText hover:text-ink bg-canvas'
              }`}
            >
              <span>Live Terminal Trace</span>
              <span className={`text-[10px] px-1 py-0.2 rounded-full font-mono ${
                !splitView && activeTab === 'terminal'
                  ? 'bg-white/20 text-white'
                  : 'bg-hairlineSoft text-mute'
              }`}>
                {events.length}
              </span>
              {isStreaming && (
                <span className="relative flex h-1.5 w-1.5">
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                  <span className="relative inline-flex rounded-full h-1.5 w-1.5 bg-emerald-500"></span>
                </span>
              )}
            </button>

            <button
              onClick={() => { setActiveTab('soundbox'); setSplitView(false); }}
              className={`px-2.5 py-1 text-xs font-mono rounded-sm transition-colors ${
                !splitView && activeTab === 'soundbox'
                  ? 'bg-ink text-white font-medium shadow-whisper'
                  : 'text-bodyText hover:text-ink bg-canvas'
              }`}
            >
              Soundbox IoT
            </button>

            <button
              onClick={() => { setActiveTab('stego_qr'); setSplitView(false); }}
              className={`flex items-center gap-1 px-2.5 py-1 text-xs font-mono rounded-sm transition-colors ${
                !splitView && activeTab === 'stego_qr'
                  ? 'bg-ink text-white font-medium shadow-whisper'
                  : 'text-bodyText hover:text-ink bg-canvas'
              }`}
            >
              <ShieldCheck className="h-3 w-3 text-accentBlue" />
              <span>Anti-Tamper QR</span>
            </button>
          </div>

          {/* Split Mode Toggle Button */}
          <button
            onClick={() => setSplitView(!splitView)}
            title={splitView ? "Switch to Full Tab View" : "Split View: Ledger + Terminal simultaneously"}
            className={`flex items-center gap-1 px-2 py-0.5 text-[11px] font-mono rounded-sm border transition-colors ${
              splitView
                ? 'bg-accentBlueSoft text-accentBlueDeep border-accentBlue'
                : 'bg-canvas text-mute border-hairline hover:text-ink hover:border-ink'
            }`}
          >
            {splitView ? <Square className="h-3 w-3" /> : <Columns className="h-3 w-3" />}
            <span className="hidden sm:inline">{splitView ? 'Single View' : 'Split View'}</span>
          </button>
        </div>

        {/* Dynamic Content Pane */}
        <div className="flex-1 min-h-0">
          {splitView ? (
            /* Split View: 50% Ledger Pipeline, 50% Live Terminal Trace */
            <div className="grid grid-rows-2 gap-2 h-full min-h-0">
              <div className="min-h-0">
                <LedgerPipelineCard
                  batches={merchantData?.settlement_batches || []}
                  transactions={merchantData?.transactions || []}
                />
              </div>
              <div className="min-h-0">
                <TerminalTrace
                  events={events}
                  onClear={onClearTrace}
                />
              </div>
            </div>
          ) : (
            /* Tabbed Single View: 100% Height to Active Tab */
            <div className="h-full min-h-0">
              {activeTab === 'pipeline' && (
                <LedgerPipelineCard
                  batches={merchantData?.settlement_batches || []}
                  transactions={merchantData?.transactions || []}
                />
              )}
              {activeTab === 'terminal' && (
                <TerminalTrace
                  events={events}
                  onClear={onClearTrace}
                />
              )}
              {activeTab === 'soundbox' && (
                <SoundboxCard
                  soundbox={merchantData?.soundbox}
                  onSoundboxUpdated={onSoundboxUpdated}
                />
              )}
              {activeTab === 'stego_qr' && (
                <AntiTamperQRView
                  merchant={currentMerchant || merchantData?.merchant}
                />
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
