import React from 'react';
import { Bot, Search, Wrench, ShieldCheck, CheckCircle2, Clock, AlertTriangle, Cpu } from 'lucide-react';

const PIPELINE_NODES = [
  {
    step: 1,
    id: "manager",
    label: "01. Incident Manager",
    role: "Intent & Safety Boundary",
    icon: Bot,
  },
  {
    step: 2,
    id: "investigator",
    label: "02. SQL Investigator",
    role: "Database & Rail Diagnostic",
    icon: Search,
  },
  {
    step: 3,
    id: "remediation",
    label: "03. Remediation Agent",
    role: "Idempotent API Execution",
    icon: Wrench,
  },
  {
    step: 4,
    id: "verifier",
    label: "04. Verification Agent",
    role: "Bank UTR & Ledger Proof",
    icon: ShieldCheck,
  }
];

export default function AgentPipelineFlow({ events, isStreaming, currentIncidentId }) {
  const activeStep = events.length > 0 ? events[events.length - 1].step : 0;
  const latestEvent = events.length > 0 ? events[events.length - 1] : null;

  return (
    <div className="rounded-md border border-hairline bg-elevated p-2.5 shadow-whisper shrink-0">
      {/* Header */}
      <div className="flex items-center justify-between mb-2 pb-1.5 border-b border-hairline">
        <div className="flex items-center gap-1.5">
          <Cpu className="h-3.5 w-3.5 text-ink" />
          <span className="font-mono text-[11px] uppercase tracking-wider font-semibold text-ink">
            Autonomous Teammate Pipeline Flow
          </span>
        </div>
        {currentIncidentId && (
          <span className="font-mono text-[10px] text-mute bg-hairlineSoft px-1.5 py-0.5 rounded-sm">
            Trace ID: {currentIncidentId}
          </span>
        )}
      </div>

      {/* Grid of Pipeline Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-2">
        {PIPELINE_NODES.map((node) => {
          const NodeIcon = node.icon;
          const nodeEvents = events.filter((e) => e.step === node.step);
          const isCurrentActive = activeStep === node.step && isStreaming;
          const isDone = activeStep > node.step || (node.step === 4 && latestEvent?.status === 'RESOLVED');
          const isWaitingApproval = node.step === 3 && latestEvent?.status === 'AWAITING_APPROVAL';

          const nodeMessage = nodeEvents.length > 0 ? nodeEvents[nodeEvents.length - 1].message : null;

          return (
            <div
              key={node.id}
              className={`relative rounded-md border p-2 transition-all duration-300 flex flex-col justify-between ${
                isWaitingApproval
                  ? "border-amber-400 bg-amber-50/50 shadow-sm"
                  : isCurrentActive
                  ? "border-accentBlue bg-blue-50/20 shadow-sm ring-1 ring-accentBlue"
                  : isDone
                  ? "border-emerald-300 bg-emerald-50/20"
                  : "border-hairline bg-canvas opacity-75"
              }`}
            >
              {/* Top Row: Icon & Status Badge */}
              <div className="flex items-center justify-between gap-1">
                <div
                  className={`h-6 w-6 rounded-sm flex items-center justify-center border transition-colors ${
                    isWaitingApproval
                      ? "bg-amber-100 border-amber-300 text-amber-700"
                      : isCurrentActive
                      ? "bg-accentBlueSoft border-accentBlue text-accentBlue"
                      : isDone
                      ? "bg-emerald-100 border-emerald-300 text-emerald-700"
                      : "bg-white border-hairline text-mute"
                  }`}
                >
                  <NodeIcon className="h-3 w-3" />
                </div>

                <div>
                  {isWaitingApproval ? (
                    <span className="inline-flex items-center gap-0.5 font-mono text-[9px] uppercase tracking-wider px-1 py-0.2 rounded-sm bg-amber-100 text-amber-800 border border-amber-200">
                      <AlertTriangle className="h-2.5 w-2.5" />
                      Approval
                    </span>
                  ) : isCurrentActive ? (
                    <span className="inline-flex items-center gap-1 font-mono text-[9px] uppercase tracking-wider px-1 py-0.2 rounded-sm bg-blue-100 text-accentBlueDeep border border-blue-200">
                      <span className="relative flex h-1.5 w-1.5">
                        <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-blue-400 opacity-75"></span>
                        <span className="relative inline-flex rounded-full h-1.5 w-1.5 bg-accentBlue"></span>
                      </span>
                      Thinking
                    </span>
                  ) : isDone ? (
                    <span className="inline-flex items-center gap-0.5 font-mono text-[9px] uppercase tracking-wider px-1 py-0.2 rounded-sm bg-emerald-100 text-emerald-800 border border-emerald-200">
                      <CheckCircle2 className="h-2.5 w-2.5" />
                      Done
                    </span>
                  ) : (
                    <span className="inline-flex items-center gap-0.5 font-mono text-[9px] uppercase tracking-wider px-1 py-0.2 rounded-sm bg-hairlineSoft text-mute">
                      <Clock className="h-2.5 w-2.5" />
                      Idle
                    </span>
                  )}
                </div>
              </div>

              {/* Title & Role */}
              <div className="mt-1.5">
                <div className="font-semibold text-[11px] text-ink leading-tight truncate">{node.label}</div>
                <div className="font-mono text-[9px] text-mute truncate">{node.role}</div>
              </div>

              {/* Dynamic Thought Output */}
              <div className="mt-1.5 pt-1 border-t border-hairline/60 min-h-[32px] flex items-center">
                {nodeMessage ? (
                  <p className="text-[10px] text-bodyText leading-snug line-clamp-2">
                    {nodeMessage}
                  </p>
                ) : (
                  <p className="text-[10px] text-faint italic font-mono">
                    Awaiting incident trigger...
                  </p>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
