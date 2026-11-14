import React, { useRef, useEffect } from 'react';
import { Terminal, Copy, Check, Trash2 } from 'lucide-react';

export default function TerminalTrace({ events, onClear }) {
  const terminalRef = useRef(null);
  const [copied, setCopied] = React.useState(false);

  useEffect(() => {
    if (terminalRef.current) {
      terminalRef.current.scrollTop = terminalRef.current.scrollHeight;
    }
  }, [events]);

  const handleCopy = () => {
    const text = events.map((e) => `[${e.timestamp}] [${e.agent}] [${e.status}] ${e.message}`).join('\n');
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="rounded-md border border-hairline bg-elevated shadow-whisper overflow-hidden flex flex-col h-full min-h-0">
      {/* Terminal Title Bar */}
      <div className="flex items-center justify-between px-3 py-1.5 border-b border-hairline bg-canvas shrink-0">
        <div className="flex items-center gap-1.5">
          <Terminal className="h-3 w-3 text-mute" />
          <span className="font-mono text-[10px] uppercase tracking-wider text-mute font-medium">
            Live Execution Trace & Tool RPCs ({events.length} events)
          </span>
        </div>
        <div className="flex items-center gap-1">
          <button
            onClick={handleCopy}
            title="Copy Logs"
            className="h-5 px-2 flex items-center gap-1 rounded-sm border border-hairline bg-elevated text-[9px] font-mono text-bodyText hover:text-ink hover:border-ink transition-colors"
          >
            {copied ? <Check className="h-2.5 w-2.5 text-emerald-600" /> : <Copy className="h-2.5 w-2.5" />}
            <span>{copied ? 'Copied' : 'Copy'}</span>
          </button>
          {onClear && (
            <button
              onClick={onClear}
              title="Clear Trace"
              className="h-5 px-1.5 flex items-center gap-1 rounded-sm border border-hairline bg-elevated text-[9px] font-mono text-bodyText hover:text-ink hover:border-ink transition-colors"
            >
              <Trash2 className="h-2.5 w-2.5" />
            </button>
          )}
        </div>
      </div>

      {/* Terminal Log Area */}
      <div
        ref={terminalRef}
        className="p-2.5 overflow-y-auto flex-1 min-h-0 font-mono text-xs space-y-1.5 bg-white"
      >
        {events.length === 0 ? (
          <div className="text-mute text-center py-8 italic text-xs">
            // No execution logs yet. Send a merchant query or trigger a scenario to stream trace events.
          </div>
        ) : (
          events.map((ev, i) => (
            <div key={i} className="leading-snug hover:bg-canvasSoft px-1 py-0.5 rounded transition-colors text-[11px]">
              <span className="text-mute select-none mr-1.5 text-[10px]">[{ev.timestamp}]</span>
              <span className={`font-semibold mr-1.5 ${
                ev.status === 'SUCCESS' || ev.status === 'RESOLVED'
                  ? 'text-emerald-600'
                  : ev.status === 'AWAITING_APPROVAL'
                  ? 'text-amber-600'
                  : ev.status === 'TOOL_CALL'
                  ? 'text-accentBlue'
                  : 'text-ink'
              }`}>
                [{ev.agent}]
              </span>
              <span className="text-bodyText">{ev.message}</span>
              {ev.details?.sql_query && (
                <div className="mt-0.5 pl-3 py-0.5 text-[10px] bg-canvas border-l-2 border-accentBlue text-ink rounded-r font-mono">
                  &gt; SQL: {ev.details.sql_query}
                </div>
              )}
              {ev.details?.utr_number && (
                <div className="mt-0.5 pl-3 py-0.5 text-[10px] bg-emerald-50 border-l-2 border-emerald-500 text-emerald-800 rounded-r font-mono font-medium">
                  &gt; VERIFIED CORE BANK UTR: {ev.details.utr_number}
                </div>
              )}
            </div>
          ))
        )}
      </div>
    </div>
  );
}
