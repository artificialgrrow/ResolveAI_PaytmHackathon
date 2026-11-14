import React, { useState } from 'react';
import { ArrowRight, Store, ShieldAlert, Volume2, CopyCheck, Activity, KeyRound, User } from 'lucide-react';
import { loginMerchant } from './api';

const DEMO_SCENARIOS = [
  {
    id: "M-101",
    name: "Ramesh Kirana Store",
    username: "ramesh_kirana",
    password: "paytm123",
    badge: "Auto-Resolution",
    badgeColor: "bg-emerald-50 text-emerald-700 border-emerald-200",
    icon: Store,
    title: "₹4,500 Stuck Morning Sales",
    description: "Batch #B-402 held on NPCI sync timeout. Auto-re-routes via secondary IMPS rail with verified UTR.",
  },
  {
    id: "M-102",
    name: "Sharmaji Electronics",
    username: "sharma_electro",
    password: "paytm123",
    badge: "Human-in-Loop",
    badgeColor: "bg-amber-50 text-amber-700 border-amber-200",
    icon: ShieldAlert,
    title: "₹78,000 High-Value Sale Hold",
    description: "Exceeds ₹25k autonomous threshold. Pauses for supervisor 1-click override before bank clearing.",
  },
  {
    id: "M-103",
    name: "Chai Point Stall",
    username: "chai_point",
    password: "paytm123",
    badge: "Soundbox Fix",
    badgeColor: "bg-blue-50 text-blue-700 border-blue-200",
    icon: Volume2,
    title: "Soundbox Silent on Payment",
    description: "Customer paid ₹60, device didn't speak. Diagnoses GSM reconnect and triggers instant OTA chime.",
  },
  {
    id: "M-104",
    name: "Verma Medical Hall",
    username: "verma_meds",
    password: "paytm123",
    badge: "Auto-Reversal",
    badgeColor: "bg-purple-50 text-purple-700 border-purple-200",
    icon: CopyCheck,
    title: "Customer Debited Twice",
    description: "Two ₹1,200 deductions for medicine. Confirms 1 success and duplicate in NPCI auto-reversal.",
  },
  {
    id: "M-105",
    name: "Gupta Sweets & Snacks",
    username: "gupta_sweets",
    password: "paytm123",
    badge: "Rail Failover",
    badgeColor: "bg-rose-50 text-rose-700 border-rose-200",
    icon: Activity,
    title: "Multiple QR Declines",
    description: "Industry-wide HDFC acquiring spike. Autonomously shifts merchant traffic to ICICI backup route.",
  }
];

export default function LoginView({ onLoginSuccess }) {
  const [username, setUsername] = useState('ramesh_kirana');
  const [password, setPassword] = useState('paytm123');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    if (e) e.preventDefault();
    setLoading(true);
    setError('');
    try {
      const data = await loginMerchant(username, password);
      onLoginSuccess(data.merchant);
    } catch (err) {
      setError(err.message || 'Login failed. Please check credentials.');
    } finally {
      setLoading(false);
    }
  };

  const handleQuickSelect = async (scenario) => {
    setUsername(scenario.username);
    setPassword(scenario.password);
    setLoading(true);
    setError('');
    try {
      const data = await loginMerchant(scenario.username, scenario.password);
      onLoginSuccess(data.merchant);
    } catch (err) {
      setError(err.message || 'Quick login failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="relative h-[calc(100vh-3rem)] overflow-hidden flex flex-col justify-center px-4 sm:px-6 lg:px-8 py-2 bg-canvas">
      {/* Background Mesh Gradient */}
      <div className="absolute inset-0 geist-mesh-gradient pointer-events-none" />

      <div className="relative mx-auto w-full max-w-4xl max-h-full flex flex-col justify-center">
        {/* Compact Header */}
        <div className="text-center mb-3">
          <div className="inline-flex items-center justify-center h-8 w-8 rounded-sm bg-ink text-white font-bold text-base mb-1 shadow-whisper">
            ₹
          </div>
          <h2 className="text-2xl font-semibold tracking-[-0.8px] text-ink">
            Paytm ResolveAI Merchant Operations
          </h2>
          <p className="mt-0.5 text-xs text-bodyText max-w-lg mx-auto">
            Log in to the operations console or pick a scenario to witness live autonomous multi-agent incident resolution.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-12 gap-5 items-start">
          {/* Left: Standard Login Form */}
          <div className="md:col-span-5 bg-elevated border border-hairline rounded-md p-4 shadow-whisper">
            <h3 className="text-sm font-semibold text-ink tracking-tight mb-3 flex items-center gap-1.5">
              <KeyRound className="h-4 w-4 text-mute" />
              Merchant Sign In
            </h3>

            {error && (
              <div className="mb-3 p-2 rounded-sm bg-rose-50 border border-rose-200 text-rose-700 text-xs">
                {error}
              </div>
            )}

            <form onSubmit={handleSubmit} className="space-y-2.5">
              <div>
                <label className="block text-xs font-medium text-bodyText mb-1">Merchant Username</label>
                <div className="relative">
                  <User className="absolute left-2.5 top-2 h-3.5 w-3.5 text-mute" />
                  <input
                    type="text"
                    value={username}
                    onChange={(e) => setUsername(e.target.value)}
                    required
                    className="w-full pl-8 pr-3 py-1.5 text-xs rounded-sm border border-hairline bg-canvas focus:bg-white focus:outline-none focus:border-ink transition-colors font-mono"
                    placeholder="e.g. ramesh_kirana"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-medium text-bodyText mb-1">Password</label>
                <input
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                  className="w-full px-3 py-1.5 text-xs rounded-sm border border-hairline bg-canvas focus:bg-white focus:outline-none focus:border-ink transition-colors font-mono"
                  placeholder="••••••••"
                />
              </div>

              <button
                type="submit"
                disabled={loading}
                className="w-full mt-2 h-9 flex items-center justify-center gap-1.5 rounded-full bg-ink text-white font-medium text-xs hover:bg-black transition-colors disabled:opacity-50 shadow-whisper"
              >
                {loading ? 'Authenticating...' : 'Sign In to Operations Console'}
                <ArrowRight className="h-3.5 w-3.5" />
              </button>
            </form>

            <div className="mt-3 pt-2.5 border-t border-hairline text-[10px] text-mute text-center">
              Default password for all demo accounts: <span className="font-mono text-ink font-medium">paytm123</span>
            </div>
          </div>

          {/* Right: 1-Click Live Demo Scenarios */}
          <div className="md:col-span-7">
            <div className="flex items-center justify-between mb-2">
              <span className="font-mono text-xs uppercase tracking-wider text-mute font-medium">
                Live Demo Scenarios
              </span>
              <span className="text-[11px] text-mute">1-Click Quick Select</span>
            </div>

            <div className="space-y-1.5">
              {DEMO_SCENARIOS.map((sc) => {
                const IconComponent = sc.icon;
                return (
                  <button
                    key={sc.id}
                    onClick={() => handleQuickSelect(sc)}
                    className="w-full text-left p-2 rounded-md border border-hairline bg-elevated hover:border-ink hover:shadow-whisper transition-all group"
                  >
                    <div className="flex items-center justify-between gap-2.5">
                      <div className="flex items-center gap-2.5 min-w-0">
                        <div className="h-7 w-7 shrink-0 rounded-sm border border-hairline bg-canvas flex items-center justify-center text-ink group-hover:border-ink transition-colors">
                          <IconComponent className="h-3.5 w-3.5" />
                        </div>
                        <div className="min-w-0">
                          <div className="flex items-center gap-1.5">
                            <span className="font-medium text-xs text-ink truncate">{sc.name}</span>
                            <span className={`text-[9px] font-mono px-1 py-0.2 rounded-sm border shrink-0 ${sc.badgeColor}`}>
                              {sc.badge}
                            </span>
                          </div>
                          <div className="text-[11px] font-medium text-bodyText truncate">{sc.title}</div>
                          <p className="text-[10px] text-mute truncate">{sc.description}</p>
                        </div>
                      </div>
                      <ArrowRight className="h-3.5 w-3.5 text-mute group-hover:text-ink group-hover:translate-x-0.5 transition-all shrink-0" />
                    </div>
                  </button>
                );
              })}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
