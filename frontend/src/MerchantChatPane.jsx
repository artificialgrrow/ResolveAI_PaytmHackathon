import React, { useState, useRef, useEffect } from 'react';
import { Send, Bot, User, Mic, MicOff, CheckCircle2, ShieldCheck, ShieldAlert, Sparkles, Globe, Volume2, VolumeX, Loader2, Square } from 'lucide-react';
import { UI_LABELS, INDIAN_LANGUAGES } from './languages';
import { fetchTTSAudio, transcribeVoiceAudio } from './api';

export default function MerchantChatPane({
  merchant,
  messages,
  onSendMessage,
  isStreaming,
  verifiedUtr,
  fraudAlert,
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

  // Voice Recording & STT state
  const [isRecording, setIsRecording] = useState(false);
  const [isTranscribing, setIsTranscribing] = useState(false);
  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);

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

  const recognitionRef = useRef(null);

  const startRecording = async () => {
    stopCurrentAudio();
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;

    // Path 1: Native Browser Real-Time Speech Recognition (Zero Server Delay)
    if (SpeechRecognition) {
      try {
        const recognition = new SpeechRecognition();
        recognitionRef.current = recognition;
        const bLang = {
          en: 'en-IN', hi: 'hi-IN', mr: 'mr-IN', gu: 'gu-IN',
          bn: 'bn-IN', ta: 'ta-IN', te: 'te-IN', kn: 'kn-IN',
          ml: 'ml-IN', pa: 'pa-IN'
        }[selectedLanguage] || 'en-IN';

        recognition.lang = bLang;
        recognition.interimResults = true;
        recognition.continuous = false;

        let finalTranscript = '';

        recognition.onstart = () => {
          setIsRecording(true);
        };

        recognition.onresult = (event) => {
          let interim = '';
          for (let i = event.resultIndex; i < event.results.length; ++i) {
            if (event.results[i].isFinal) {
              finalTranscript += event.results[i][0].transcript;
            } else {
              interim += event.results[i][0].transcript;
            }
          }
          const currentText = (finalTranscript + ' ' + interim).trim();
          if (currentText) {
            setInput(currentText);
          }
        };

        recognition.onerror = (e) => {
          console.warn("Browser SpeechRecognition notice, attempting MediaRecorder fallback:", e.error);
          setIsRecording(false);
          if (e.error === 'not-allowed') {
            alert("Microphone permission denied. Please allow microphone access in your browser settings.");
          } else {
            // Attempt fallback to MediaRecorder + Sarvam
            startMediaRecorderFallback();
          }
        };

        recognition.onend = () => {
          setIsRecording(false);
          const textToSubmit = finalTranscript.trim() || input.trim();
          if (textToSubmit) {
            handleSend(textToSubmit);
          }
        };

        recognition.start();
        return;
      } catch (err) {
        console.warn("SpeechRecognition init failed, falling back to MediaRecorder:", err);
      }
    }

    // Path 2: MediaRecorder + Sarvam AI Saaras STT
    startMediaRecorderFallback();
  };

  const startMediaRecorderFallback = async () => {
    try {
      if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
        alert("Microphone is not supported in this browser. Please type your query.");
        setIsRecording(false);
        return;
      }
      audioChunksRef.current = [];
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mediaRecorder = new MediaRecorder(stream);
      mediaRecorderRef.current = mediaRecorder;

      mediaRecorder.ondataavailable = (e) => {
        if (e.data && e.data.size > 0) {
          audioChunksRef.current.push(e.data);
        }
      };

      mediaRecorder.onstop = async () => {
        stream.getTracks().forEach((track) => track.stop());
        const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/webm' });
        if (audioBlob.size < 100) {
          setIsRecording(false);
          return;
        }
        setIsTranscribing(true);
        try {
          const res = await transcribeVoiceAudio(audioBlob, selectedLanguage);
          if (res.transcript && res.transcript.trim()) {
            setInput(res.transcript.trim());
            handleSend(res.transcript.trim());
          } else {
            alert("No speech detected. Please try speaking closer to the microphone.");
          }
        } catch (err) {
          console.error("Voice transcription failed:", err);
          alert("Voice service temporarily busy. You can type your query in the box below.");
        } finally {
          setIsTranscribing(false);
          setIsRecording(false);
        }
      };

      mediaRecorder.start();
      setIsRecording(true);
    } catch (err) {
      console.error("Mic access denied or error:", err);
      alert("Could not access microphone. Please enable mic permissions in your browser.");
      setIsRecording(false);
    }
  };

  const stopRecording = () => {
    if (recognitionRef.current) {
      try { recognitionRef.current.stop(); } catch (_) {}
    }
    if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
      try { mediaRecorderRef.current.stop(); } catch (_) {}
    }
    setIsRecording(false);
  };

  const handleToggleRecord = () => {
    if (isRecording) {
      stopRecording();
    } else {
      startRecording();
    }
  };

  useEffect(() => {
    return () => {
      stopCurrentAudio();
      if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
        mediaRecorderRef.current.stop();
      }
    };
  }, [merchant?.id, selectedLanguage]);

  const handleSend = (textToSend) => {
    const query = textToSend || input;
    if (!query.trim() || isStreaming) return;
    stopCurrentAudio();
    if (isRecording) stopRecording();
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

        {/* Counterfeit Payment Spoof Alert Card */}
        {fraudAlert && (
          <div className="rounded-md border-2 border-rose-500 bg-rose-50/90 p-3 shadow-sm animate-in fade-in duration-300">
            <div className="flex items-start gap-2.5">
              <div className="h-6 w-6 rounded-full bg-rose-100 flex items-center justify-center text-rose-700 shrink-0 mt-0.5">
                <ShieldAlert className="h-4 w-4 text-rose-600" />
              </div>
              <div className="flex-1 min-w-0">
                <div className="text-xs font-bold text-rose-950 flex items-center gap-1.5 flex-wrap">
                  <span>Counterfeit Payment Spoof Alert</span>
                  <span className="font-mono text-[9px] bg-rose-200/90 text-rose-900 px-1.5 py-0.5 rounded font-semibold">
                    0 Records on NPCI Switch
                  </span>
                </div>
                <div className="mt-1 font-mono text-xs font-bold text-rose-950">
                  Claimed Amount: <span className="line-through text-rose-600 font-extrabold">₹{fraudAlert.claimed_amount?.toFixed(2) || '60.00'}</span> (NOT RECEIVED)
                </div>
                <div className="mt-1 text-[11px] font-medium text-rose-800 leading-snug">
                  DO NOT RELEASE GOODS. The customer screen is a counterfeit or spoof app screen. No funds have entered your Paytm settlement pipeline.
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
            disabled={isStreaming || isRecording || isTranscribing}
            placeholder={
              isStreaming
                ? "Teammate is resolving..."
                : isTranscribing
                ? "Transcribing voice via Sarvam AI Saaras..."
                : isRecording
                ? "Listening... Speak in your regional language (Click stop when done)"
                : placeholderText
            }
            className={`w-full pl-3 pr-20 py-1.5 text-xs rounded-sm border transition-colors disabled:opacity-75 ${
              isRecording
                ? 'border-rose-500 bg-rose-50/50 text-rose-900 placeholder:text-rose-500'
                : isTranscribing
                ? 'border-accentBlue bg-blue-50/50 text-blue-900'
                : 'border-hairline bg-elevated focus:outline-none focus:border-ink'
            }`}
          />
          <div className="absolute right-1 flex items-center gap-1">
            {/* Interactive Sarvam AI Microphone Button */}
            <button
              type="button"
              onClick={handleToggleRecord}
              disabled={isStreaming || isTranscribing}
              title={isRecording ? "Click to stop recording and send" : "Speak query (Sarvam AI Speech-to-Text)"}
              className={`h-6 px-1.5 flex items-center justify-center gap-1 rounded-sm text-xs transition-colors shadow-whisper ${
                isRecording
                  ? 'bg-rose-600 text-white animate-pulse'
                  : isTranscribing
                  ? 'bg-blue-100 text-accentBlue'
                  : 'text-mute hover:text-ink hover:bg-hairlineSoft'
              }`}
            >
              {isTranscribing ? (
                <Loader2 className="h-3 w-3 animate-spin" />
              ) : isRecording ? (
                <>
                  <Square className="h-2.5 w-2.5 fill-current" />
                  <span className="text-[10px] font-mono">Done</span>
                </>
              ) : (
                <Mic className="h-3 w-3" />
              )}
            </button>

            {/* Send Button */}
            <button
              type="button"
              onClick={() => handleSend()}
              disabled={isStreaming || !input.trim() || isRecording || isTranscribing}
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
