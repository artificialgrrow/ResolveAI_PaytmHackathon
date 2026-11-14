import React, { useState, useRef, useEffect } from 'react';
import { Send, Bot, User, Mic, CheckCircle2, ShieldCheck, Sparkles, Globe, Volume2, VolumeX, Loader2 } from 'lucide-react';
import { UI_LABELS, INDIAN_LANGUAGES } from './languages';
import { fetchTTSAudio } from './api';

export default function MerchantChatPane({
  merchant,
  messages,
  onSendMessage,
  isStreaming,
  verifiedUtr,
  suggestedPrompt,
  selectedLanguage = 'en'
}) {
  const [input, setInput] = useState('');
  const [playingIndex, setPlayingIndex] = useState(null);
  const [loadingAudioIndex, setLoadingAudioIndex] = useState(null);
  const audioRef = useRef(null);

  const currentLangObj = INDIAN_LANGUAGES.find((l) => l.code === selectedLanguage) || INDIAN_LANGUAGES[0];
  const askAiText = UI_LABELS.askAi[selectedLanguage] || UI_LABELS.askAi.en;
  const placeholderText = UI_LABELS.placeholder[selectedLanguage] || UI_LABELS.placeholder.en;
  const promptLabel = UI_LABELS.scenarioPrompt[selectedLanguage] || UI_LABELS.scenarioPrompt.en;

  // Cleanup active audio on unmount or merchant change
  const stopCurrentAudio = () => {
    if (audioRef.current) {
      audioRef.current.pause();
      audioRef.current = null;
    }
    if ('speechSynthesis' in window) {
      window.speechSynthesis.cancel();
    }
    setPlayingIndex(null);
    setLoadingAudioIndex(null);
  };

  useEffect(() => {
    return () => stopCurrentAudio();
  }, [merchant?.id, selectedLanguage]);

  const handleSend = (textToSend) => {
    const query = textToSend || input;
    if (!query.trim() || isStreaming) return;
    stopCurrentAudio();
    onSendMessage(query.trim());
    setInput('');
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const fallbackBrowserTTS = (text, index) => {
    if ('speechSynthesis' in window) {
      window.speechSynthesis.cancel();
      const utterance = new SpeechSynthesisUtterance(text);
      utterance.lang = selectedLanguage === 'en' ? 'en-IN' : `${selectedLanguage}-IN`;
      utterance.onstart = () => setPlayingIndex(index);
      utterance.onend = () => setPlayingIndex(null);
      utterance.onerror = () => setPlayingIndex(null);
      window.speechSynthesis.speak(utterance);
    } else {
      setPlayingIndex(null);
    }
  };

  const handleToggleAudio = async (text, index) => {
    if (playingIndex === index || loadingAudioIndex === index) {
      stopCurrentAudio();
      return;
    }

    stopCurrentAudio();
    setLoadingAudioIndex(index);

    try {
      const blob = await fetchTTSAudio(text, selectedLanguage);
      const audioUrl = URL.createObjectURL(blob);
      const audio = new Audio(audioUrl);
      audioRef.current = audio;

      audio.onended = () => {
        setPlayingIndex(null);
        audioRef.current = null;
      };
      audio.onerror = () => {
        setLoadingAudioIndex(null);
        fallbackBrowserTTS(text, index);
      };

      setLoadingAudioIndex(null);
      setPlayingIndex(index);
      await audio.play();
    } catch (err) {
      console.warn('Edge TTS service call failed, falling back to browser synthesis:', err);
      setLoadingAudioIndex(null);
      fallbackBrowserTTS(text, index);
    }
  };

  return (
    <div className="flex flex-col h-full rounded-md border border-hairline bg-elevated shadow-whisper overflow-hidden min-h-0">
      {/* Pane Header */}
      <div className="flex items-center justify-between px-3 py-2 border-b border-hairline bg-canvas shrink-0">
        <div className="flex items-center gap-2">
          <div className="h-6 w-6 rounded-full bg-ink text-white flex items-center justify-center text-xs font-semibold">
            AI
          </div>
          <div>
            <div className="text-xs font-semibold text-ink leading-tight">ResolveAI Operations Assistant</div>
            <div className="text-[10px] text-mute font-mono">Paytm Autonomous Merchant Teammate</div>
          </div>
        </div>

        <div className="flex items-center gap-1.5">
          <span className="inline-flex items-center gap-1 font-mono text-[10px] text-accentBlue bg-blue-50 border border-blue-200 px-1.5 py-0.5 rounded-sm">
            <Globe className="h-2.5 w-2.5" />
            <span>{currentLangObj.nativeName}</span>
          </span>
          <span className="font-mono text-[10px] text-mute bg-hairlineSoft px-1.5 py-0.5 rounded-sm hidden sm:inline">
            Zero FAQ Deflection
          </span>
        </div>
      </div>

      {/* Suggested Scenario Prompt Bar */}
      {suggestedPrompt && messages.length <= 1 && (
        <div className="px-3 py-1.5 bg-blue-50/60 border-b border-blue-100 flex items-center justify-between gap-2 shrink-0">
          <div className="flex items-center gap-1.5 text-xs text-blue-900 truncate">
            <Sparkles className="h-3 w-3 text-accentBlue shrink-0" />
            <span className="font-medium truncate">{promptLabel}</span>
            <span className="truncate italic">"{suggestedPrompt}"</span>
          </div>
          <button
            onClick={() => handleSend(suggestedPrompt)}
            disabled={isStreaming}
            className="text-[11px] font-medium px-2.5 py-0.5 rounded-full bg-accentBlue text-white hover:bg-accentBlueDeep transition-colors shrink-0 disabled:opacity-50 shadow-whisper"
          >
            {askAiText}
          </button>
        </div>
      )}

      {/* Message List */}
      <div className="flex-1 overflow-y-auto p-3 space-y-3 min-h-0">
        {messages.map((msg, i) => (
          <div
            key={i}
            className={`flex gap-2.5 ${msg.sender === 'merchant' ? 'justify-end' : 'justify-start'}`}
          >
            {msg.sender === 'ai' && (
              <div className="h-6 w-6 rounded-full bg-ink text-white flex items-center justify-center text-[10px] font-semibold shrink-0 mt-0.5">
                AI
              </div>
            )}

            {msg.sender === 'merchant' ? (
              <div className="max-w-[85%] rounded-md px-3 py-2 text-xs leading-relaxed bg-ink text-white">
                <p className="whitespace-pre-wrap">{msg.text}</p>
              </div>
            ) : (
              <div className="flex flex-col items-start max-w-[85%]">
                <div className="rounded-md px-3 py-2 text-xs leading-relaxed bg-canvas border border-hairline text-ink">
                  <p className="whitespace-pre-wrap">{msg.text}</p>
                </div>

                {/* Clean Edge TTS Audio Voice Button */}
                <button
                  type="button"
                  onClick={() => handleToggleAudio(msg.text, i)}
                  className={`mt-1.5 inline-flex items-center gap-1.5 px-2 py-0.5 rounded-sm border text-[10px] font-mono transition-colors shadow-whisper ${
                    playingIndex === i
                      ? 'bg-rose-50 border-rose-300 text-rose-700'
                      : loadingAudioIndex === i
                      ? 'bg-blue-50 border-blue-200 text-accentBlue'
                      : 'bg-canvas border-hairline text-bodyText hover:border-ink hover:text-ink'
                  }`}
                  title="Listen to response in selected regional language (Edge TTS)"
                >
                  {loadingAudioIndex === i ? (
                    <>
                      <Loader2 className="h-3 w-3 animate-spin text-accentBlue" />
                      <span>Synthesizing Voice...</span>
                    </>
                  ) : playingIndex === i ? (
                    <>
                      <VolumeX className="h-3 w-3 text-rose-600" />
                      <span className="font-semibold text-rose-600">Stop Audio</span>
                    </>
                  ) : (
                    <>
                      <Volume2 className="h-3 w-3 text-accentBlue" />
                      <span>Listen Voice</span>
                    </>
                  )}
                </button>
              </div>
            )}

            {msg.sender === 'merchant' && (
              <div className="h-6 w-6 rounded-full bg-hairlineSoft border border-hairline flex items-center justify-center text-xs font-medium text-ink shrink-0 mt-0.5">
                <User className="h-3.5 w-3.5" />
              </div>
            )}
          </div>
        ))}

        {/* Real-time thinking pulse */}
        {isStreaming && (
          <div className="flex gap-2.5 justify-start items-center text-xs text-mute font-mono">
            <div className="h-6 w-6 rounded-full bg-ink text-white flex items-center justify-center text-[10px] font-semibold shrink-0">
              AI
            </div>
            <div className="flex items-center gap-2 bg-canvas border border-hairline px-2.5 py-1.5 rounded-md">
              <span className="relative flex h-2 w-2">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-accentBlue opacity-75"></span>
                <span className="relative inline-flex rounded-full h-2 w-2 bg-accentBlue"></span>
              </span>
              <span>Investigating payment rails & settlement batches...</span>
            </div>
          </div>
        )}

        {/* Verified Bank UTR Receipt Card */}
        {verifiedUtr && (
          <div className="rounded-md border-2 border-emerald-500 bg-emerald-50/60 p-3 shadow-sm">
            <div className="flex items-start gap-2.5">
              <div className="h-6 w-6 rounded-full bg-emerald-100 flex items-center justify-center text-emerald-700 shrink-0 mt-0.5">
                <CheckCircle2 className="h-3.5 w-3.5" />
              </div>
              <div>
                <div className="text-xs font-semibold text-emerald-900 flex items-center gap-1.5">
                  <span>Settlement Credit Verified</span>
                  <span className="font-mono text-[9px] bg-emerald-200/70 text-emerald-800 px-1.5 py-0.5 rounded">
                    Core Bank Proof
                  </span>
                </div>
                <div className="mt-1 font-mono text-xs font-bold text-ink">
                  Bank UTR: <span className="text-emerald-700">{verifiedUtr}</span>
                </div>
                <div className="mt-0.5 text-[11px] text-emerald-800">
                  Credited to: {merchant?.bank_name} ({merchant?.account_number})
                </div>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Input Box */}
      <div className="p-2.5 border-t border-hairline bg-canvas shrink-0">
        <div className="relative flex items-center">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyPress}
            disabled={isStreaming}
            placeholder={isStreaming ? "Teammate is resolving..." : placeholderText}
            className="w-full pl-3 pr-18 py-1.5 text-xs rounded-sm border border-hairline bg-elevated focus:outline-none focus:border-ink transition-colors disabled:opacity-50"
          />
          <div className="absolute right-1 flex items-center gap-1">
            <button
              type="button"
              title="Voice Input (Phase 2)"
              className="h-6 w-6 flex items-center justify-center rounded-sm text-mute hover:text-ink transition-colors"
            >
              <Mic className="h-3 w-3" />
            </button>
            <button
              type="button"
              onClick={() => handleSend()}
              disabled={isStreaming || !input.trim()}
              className="h-6 px-2 flex items-center justify-center gap-1 rounded-full bg-ink text-white font-medium text-xs hover:bg-black transition-colors disabled:opacity-40 shadow-whisper"
            >
              <Send className="h-2.5 w-2.5" />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
