import React from 'react';
import { Layers, ArrowUpRight, CheckCircle2, Clock, AlertCircle } from 'lucide-react';

export default function LedgerPipelineCard({ batches = [], transactions = [] }) {
  return (
    <div className="rounded-md border border-hairline bg-elevated p-3 shadow-whisper h-full flex flex-col min-h-0 overflow-hidden">
      <div className="flex items-center justify-between mb-2 pb-1.5 border-b border-hairline shrink-0">
        <div className="flex items-center gap-1.5">
          <Layers className="h-3.5 w-3.5 text-ink" />
          <span className="font-mono text-[11px] uppercase tracking-wider font-semibold text-ink">
            Multi-Silo Settlement & Ledger Pipeline
          </span>
        </div>
        <span className="font-mono text-[9px] text-mute">
          Live Core Bank Reconciliation
        </span>
      </div>

      <div className="flex-1 min-h-0 overflow-y-auto space-y-3 pr-1">
        {/* Settlement Batches Table */}
        <div>
          <div className="text-[10px] font-mono uppercase text-mute font-medium mb-1">
            Settlement Batches (Clearing Pipeline)
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs font-mono">
              <thead>
                <tr className="border-b border-hairline text-mute text-[9px] uppercase">
                  <th className="pb-1 font-medium">Batch</th>
                  <th className="pb-1 font-medium">Amount</th>
                  <th className="pb-1 font-medium">Rail</th>
                  <th className="pb-1 font-medium">Status</th>
                  <th className="pb-1 font-medium">Bank UTR Reference</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-hairline/60">
                {batches.length === 0 ? (
                  <tr>
                    <td colSpan={5} className="py-2 text-mute text-center italic text-xs">No settlement batches found</td>
                  </tr>
                ) : (
                  batches.map((b) => (
                    <tr key={b.id || b.batch_code} className="hover:bg-canvas/50 transition-colors">
                      <td className="py-1.5 font-medium text-ink">{b.batch_code}</td>
                      <td className="py-1.5 text-ink">₹{b.total_amount?.toLocaleString('en-IN', { minimumFractionDigits: 2 })}</td>
                      <td className="py-1.5 text-bodyText">{b.rail}</td>
                      <td className="py-1.5">
                        <span className={`inline-flex items-center gap-1 px-1.5 py-0.2 rounded-sm text-[9px] uppercase ${
                          b.status === 'SETTLED'
                            ? 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                            : b.status === 'HELD'
                            ? 'bg-amber-50 text-amber-700 border border-amber-200'
                            : 'bg-blue-50 text-blue-700 border border-blue-200'
                        }`}>
                          {b.status === 'SETTLED' ? <CheckCircle2 className="h-2 w-2" /> : <Clock className="h-2 w-2" />}
                          {b.status}
                        </span>
                      </td>
                      <td className="py-1.5 font-mono text-ink">
                        {b.utr_number ? (
                          <span className="text-emerald-700 font-semibold">{b.utr_number}</span>
                        ) : (
                          <span className="text-mute italic">{b.hold_reason || 'Pending Clearing'}</span>
                        )}
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>

        {/* Recent Transactions List */}
        <div className="pt-2 border-t border-hairline">
          <div className="text-[10px] font-mono uppercase text-mute font-medium mb-1">
            Recent Payment Gateway Transactions
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs font-mono">
              <thead>
                <tr className="border-b border-hairline text-mute text-[9px] uppercase">
                  <th className="pb-1 font-medium">Order ID</th>
                  <th className="pb-1 font-medium">Amount</th>
                  <th className="pb-1 font-medium">Mode</th>
                  <th className="pb-1 font-medium">Status</th>
                  <th className="pb-1 font-medium">Telemetry / Failure</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-hairline/60">
                {transactions.length === 0 ? (
                  <tr>
                    <td colSpan={5} className="py-2 text-mute text-center italic text-xs">No transactions found</td>
                  </tr>
                ) : (
                  transactions.map((tx) => (
                    <tr key={tx.id || tx.order_id} className="hover:bg-canvas/50 transition-colors">
                      <td className="py-1 text-ink">{tx.order_id}</td>
                      <td className="py-1 font-medium text-ink">₹{tx.amount?.toLocaleString('en-IN', { minimumFractionDigits: 2 })}</td>
                      <td className="py-1 text-bodyText">{tx.payment_mode}</td>
                      <td className="py-1">
                        <span className={`inline-flex items-center gap-1 px-1.5 py-0.2 rounded-sm text-[9px] uppercase ${
                          tx.status === 'SUCCESS'
                            ? 'bg-emerald-50 text-emerald-700'
                            : tx.status === 'REVERSED'
                            ? 'bg-purple-50 text-purple-700'
                            : 'bg-rose-50 text-rose-700'
                        }`}>
                          {tx.status}
                        </span>
                      </td>
                      <td className="py-1 text-mute text-[9px]">
                        {tx.failure_reason || `RRN: ${tx.rrn || 'Verified'}`}
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
}
