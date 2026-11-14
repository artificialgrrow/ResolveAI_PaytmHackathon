import React, { useState } from 'react';
import { Volume2, Battery, Wifi, WifiOff, BellRing, RefreshCw } from 'lucide-react';
import { pingSoundbox } from './api';

export default function SoundboxCard({ soundbox, onSoundboxUpdated }) {
  const [testingChime, setTestingChime] = useState(false);
  const [lastChimeMsg, setLastChimeMsg] = useState('');

  if (!soundbox) return null;

  const playLocalBeep = () => {
    try {
      const ctx = new (window.AudioContext || window.webkitAudioContext)();
      const osc = ctx.createOscillator();
      const gain = ctx.createGain();
      osc.type = 'sine';
      osc.frequency.setValueAtTime(880, ctx.currentTime); // 880Hz
      osc.frequency.exponentialRampToValueAtTime(1760, ctx.currentTime + 0.2); // chirp
      gain.gain.setValueAtTime(0.3, ctx.currentTime);
      gain.gain.exponentialRampToValueAtTime(0.01, ctx.currentTime + 0.3);
      osc.connect(gain);
      gain.connect(ctx.destination);
      osc.start();
      osc.stop(ctx.currentTime + 0.35);
    } catch (e) {
      console.warn("Audio Context blocked or not supported:", e);
    }
  };

  const handleTestChime = async () => {
    setTestingChime(true);
    playLocalBeep();
    try {
      const res = await pingSoundbox(soundbox.device_id, 60.0);
      setLastChimeMsg(res.message);
      if (onSoundboxUpdated) onSoundboxUpdated();
    } catch (err) {
      setLastChimeMsg('Failed to ping device');
    } finally {
      setTestingChime(false);
    }
  };

  const isOnline = soundbox.sim_status === 'ONLINE';

  return (
    <div className="rounded-md border border-hairline bg-elevated p-3 shadow-whisper h-full flex flex-col min-h-0 overflow-hidden">
      <div className="flex items-center justify-between mb-2 pb-1.5 border-b border-hairline shrink-0">
        <div className="flex items-center gap-1.5">
          <Volume2 className="h-3.5 w-3.5 text-ink" />
          <span className="font-mono text-[11px] uppercase tracking-wider font-semibold text-ink">
            Paytm Soundbox IoT Telemetry
          </span>
        </div>
        <span className="font-mono text-[9px] text-mute">
          Firmware: {soundbox.firmware_version}
        </span>
      </div>

      <div className="flex-1 min-h-0 overflow-y-auto space-y-3">
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
          <div className="p-2 rounded-sm border border-hairline bg-canvas">
            <div className="text-[9px] text-mute uppercase font-mono">Device ID</div>
            <div className="font-mono text-xs font-semibold text-ink mt-0.5">{soundbox.device_id}</div>
          </div>

          <div className="p-2 rounded-sm border border-hairline bg-canvas">
            <div className="text-[9px] text-mute uppercase font-mono">GSM Network</div>
            <div className="flex items-center gap-1 mt-0.5">
              {isOnline ? (
                <>
                  <Wifi className="h-3 w-3 text-emerald-600" />
                  <span className="font-mono text-xs text-emerald-700 font-medium">ONLINE</span>
                </>
              ) : (
                <>
                  <WifiOff className="h-3 w-3 text-rose-500" />
                  <span className="font-mono text-xs text-rose-600 font-medium">DISCONNECT</span>
                </>
              )}
            </div>
          </div>

          <div className="p-2 rounded-sm border border-hairline bg-canvas">
            <div className="text-[9px] text-mute uppercase font-mono">Battery</div>
            <div className="flex items-center gap-1 mt-0.5">
              <Battery className="h-3 w-3 text-bodyText" />
              <span className="font-mono text-xs text-ink">{soundbox.battery_level}%</span>
            </div>
          </div>

          <div className="p-2 rounded-sm border border-hairline bg-canvas">
            <div className="text-[9px] text-mute uppercase font-mono">Chime Status</div>
            <div className="font-mono text-xs font-medium mt-0.5">
              <span className={soundbox.last_chime_status === 'SUCCESS' ? 'text-emerald-600' : 'text-amber-600'}>
                {soundbox.last_chime_status}
              </span>
            </div>
          </div>
        </div>

        <div className="p-2.5 rounded-sm bg-canvas border border-hairline text-xs font-mono text-bodyText leading-relaxed">
          <div className="text-[10px] uppercase text-mute mb-1 font-semibold">Sim Telemetry & Health</div>
          <div>Carrier: Vodafone-Idea IoT M2M SIM</div>
          <div>Signal: -68 dBm (Strong RSSI)</div>
          <div>Audio Engine: ALSA Speech Synthesizer v2.1</div>
        </div>
      </div>

      <div className="mt-2 flex items-center justify-between pt-2 border-t border-hairline/60 shrink-0">
        <span className="text-[10px] text-mute font-mono truncate mr-2">
          {lastChimeMsg || "Last ping: Normal operational handshake."}
        </span>
        <button
          onClick={handleTestChime}
          disabled={testingChime}
          className="flex items-center gap-1.5 px-2.5 py-1 text-xs rounded-sm border border-hairline bg-elevated hover:border-ink hover:text-ink text-bodyText transition-colors font-medium shrink-0 disabled:opacity-50"
        >
          <BellRing className="h-3 w-3 text-accentBlue" />
          <span>{testingChime ? 'Emitting...' : 'Test Chime'}</span>
        </button>
      </div>
    </div>
  );
}
