import React, { useState } from 'react';
import { ShieldAlert, Check, X } from 'lucide-react';

export default function SupervisorApprovalModal({ pendingApproval, onApprove, onReject, isApproving }) {
  const [notes, setNotes] = useState('Verified merchant invoice & customer KYC');

  if (!pendingApproval) return null;

  const { incident_id, amount, batch_code } = pendingApproval;

  return (
    <div className="rounded-md border-2 border-amber-400 bg-amber-50/70 p-2.5 shadow-sm shrink-0">
      <div className="flex items-start gap-2.5">
        <div className="h-7 w-7 rounded-sm bg-amber-100 border border-amber-300 flex items-center justify-center text-amber-700 shrink-0 mt-0.5">
          <ShieldAlert className="h-4 w-4" />
        </div>

        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-1.5 flex-wrap">
            <span className="font-mono text-[10px] uppercase tracking-wider font-semibold text-amber-800">
              Human-in-the-Loop Authorization Required
            </span>
            <span className="font-mono text-[9px] px-1 py-0.2 rounded-sm bg-amber-200 text-amber-900">
              LangGraph Checkpoint
            </span>
            <span className="text-xs font-bold text-ink ml-auto">
              Hold: <span className="text-amber-700">₹{amount?.toLocaleString('en-IN', { minimumFractionDigits: 2 })}</span>
            </span>
          </div>

          <p className="text-[11px] text-bodyText mt-0.5">
            Exceeds autonomous limit (₹25,000). Agent verified ledger; requires supervisor override before releasing batch <span className="font-mono font-medium text-ink">#{batch_code}</span>.
          </p>

          <div className="mt-2 flex items-center gap-2">
            <input
              type="text"
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              placeholder="Supervisor approval note"
              className="flex-1 px-2.5 py-1 text-xs rounded-sm border border-amber-300 bg-white focus:outline-none focus:border-ink font-mono"
            />

            <button
              onClick={() => onApprove(incident_id, notes)}
              disabled={isApproving}
              className="h-7 px-3 flex items-center gap-1 rounded-full bg-ink text-white font-medium text-xs hover:bg-black transition-colors disabled:opacity-50 shrink-0 shadow-whisper"
            >
              <Check className="h-3 w-3 text-emerald-400" />
              <span>{isApproving ? 'Authorizing...' : 'Approve'}</span>
            </button>

            <button
              onClick={() => onReject(incident_id, 'Rejected by Supervisor')}
              disabled={isApproving}
              className="h-7 px-2.5 flex items-center gap-1 rounded-sm border border-hairline bg-white text-xs text-bodyText hover:text-rose-600 hover:border-rose-300 transition-colors shrink-0"
            >
              <X className="h-3 w-3" />
              <span>Reject</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
