import React, { useState, useEffect, useRef } from 'react';
import {
  QrCode,
  Download,
  Upload,
  Eye,
  EyeOff,
  ShieldCheck,
  ShieldAlert,
  AlertTriangle,
  CheckCircle2,
  XCircle,
  Loader2,
  RefreshCw,
  Mic,
  MicOff,
  Volume2,
  VolumeX,
  Play,
  RotateCcw,
  Radio,
  FileText,
  Lock,
  ArrowRight,
  Zap,
  Globe
} from 'lucide-react';
import {
  generateStegoTemplate,
  verifyStegoImage,
  getSampleTamperedTemplate,
  askVoiceAgent,
  pingSoundbox,
  transcribeVoiceAudio
} from './api';
import { INDIAN_LANGUAGES, QR_VOICE_SAMPLE_QUERIES } from './languages';

const DEMO_MERCHANTS = [
  { id: 'M-101', name: 'Ramesh Kirana Store', username: 'ramesh_kirana', bank: 'State Bank of India', vpa: 'ramesh_kirana@paytm' },
  { id: 'M-102', name: 'Sharmaji Electronics', username: 'sharma_electro', bank: 'HDFC Bank', vpa: 'sharma_electro@paytm' },
  { id: 'M-103', name: 'Chai Point Stall', username: 'chai_point', bank: 'ICICI Bank', vpa: 'chai_point@paytm' },
  { id: 'M-104', name: 'Verma Medical Hall', username: 'verma_meds', bank: 'Punjab National Bank', vpa: 'verma_meds@paytm' },
  { id: 'M-105', name: 'Gupta Sweets & Snacks', username: 'gupta_sweets', bank: 'Axis Bank', vpa: 'gupta_sweets@paytm' }
];

export default function QRProvenanceStudio({
  merchant,
  selectedLanguage = 'en',
  onLanguageChange
}) {
  const [selectedMerchantId, setSelectedMerchantId] = useState(merchant?.id || 'M-101');

  useEffect(() => {
    if (merchant?.id) {
      setSelectedMerchantId(merchant.id);
    }
  }, [merchant?.id]);

  const activeMerchant = DEMO_MERCHANTS.find(m => m.id === selectedMerchantId) || DEMO_MERCHANTS[0];
  const merchantId = activeMerchant.id;
  const merchantName = activeMerchant.name;
  const vpa = activeMerchant.vpa;

  // Panel 1: Generation state
  const [isGenerating, setIsGenerating] = useState(false);
  const [stegoData, setStegoData] = useState(null);
  const [showSecretLayer, setShowSecretLayer] = useState(false);
  const [genError, setGenError] = useState(null);

  // Panel 2: Verification state
  const [isVerifying, setIsVerifying] = useState(false);
  const [uploadedImageBase64, setUploadedImageBase64] = useState(null);
  const [uploadedFileName, setUploadedFileName] = useState('');
  const [verificationResult, setVerificationResult] = useState(null);
  const [verifyError, setVerifyError] = useState(null);
  const fileInputRef = useRef(null);

  // Panel 3: Voice Agent state
  const [isListening, setIsListening] = useState(false);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [voiceQueryText, setVoiceQueryText] = useState('');
  const [voiceAgentResponse, setVoiceAgentResponse] = useState(null);
  const [isVoiceLoading, setIsVoiceLoading] = useState(false);
  const audioPlayerRef = useRef(null);
  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);

  // Auto-generate standee on mount or merchant change
  useEffect(() => {
    handleGenerate();
    setVerificationResult(null);
    setUploadedImageBase64(null);
    setUploadedFileName('');
    setVoiceAgentResponse(null);
    setVoiceQueryText('');
  }, [merchantId]);

  // Generate merchant stego template
  const handleGenerate = async () => {
    setIsGenerating(true);
    setGenError(null);
    try {
      const data = await generateStegoTemplate(merchantId);
      setStegoData(data);
    } catch (err) {
      setGenError(err.message || 'Failed to generate steganographic QR');
    } finally {
      setIsGenerating(false);
    }
  };

  const handleDownload = () => {
    if (!stegoData?.stego_image_base64) return;
    const link = document.createElement('a');
    link.href = `data:image/png;base64,${stegoData.stego_image_base64}`;
    link.download = stegoData.download_filename || `Paytm_Stego_QR_${merchantId}.png`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  // Run verification on an image
  const runVerification = async (base64Img, fileName = 'uploaded_image.png', isTamperedSim = false) => {
    setIsVerifying(true);
    setVerifyError(null);
    setVerificationResult(null);
    setUploadedImageBase64(base64Img);
    setUploadedFileName(fileName);

    try {
      const result = await verifyStegoImage(merchantId, base64Img);
      setVerificationResult(result);

      // Auto-trigger voice agent greeting/alert if desired
      handleAskAgent(
        result.is_valid
          ? "Is this QR code genuine and safe to accept payments?"
          : "Is this QR code valid? Did someone tamper with it?",
        result
      );
    } catch (err) {
      setVerifyError(err.message || 'Verification failed');
    } finally {
      setIsVerifying(false);
    }
  };

  const handleFileUpload = (e) => {
    const file = e.target.files?.[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = () => {
      runVerification(reader.result, file.name);
    };
    reader.readAsDataURL(file);
    if (fileInputRef.current) fileInputRef.current.value = '';
  };

  // 1-Click: Test genuine standee
  const handleLoadGenuine = () => {
    if (!stegoData?.stego_image_base64) return;
    const b64 = `data:image/png;base64,${stegoData.stego_image_base64}`;
    runVerification(b64, `Genuine_Standee_${merchantId}.png`);
  };

  // 1-Click: Simulate rogue thief sticker tampering
  const handleSimulateTamper = async () => {
    setIsVerifying(true);
    setVerifyError(null);
    setVerificationResult(null);
    try {
      const tampered = await getSampleTamperedTemplate(merchantId);
      const b64 = `data:image/png;base64,${tampered.tampered_image_base64}`;
      runVerification(b64, 'Tampered_Rogue_Sticker.png', true);
    } catch (err) {
      setVerifyError(err.message || 'Failed to simulate tamper test');
      setIsVerifying(false);
    }
  };

  // Speak agent response aloud
  const playSpeech = (text, audioBase64) => {
    if (audioBase64) {
      if (audioPlayerRef.current) {
        audioPlayerRef.current.pause();
      }
      const audio = new Audio(`data:audio/wav;base64,${audioBase64}`);
      audioPlayerRef.current = audio;
      setIsSpeaking(true);
      audio.onended = () => setIsSpeaking(false);
      audio.onerror = () => {
        setIsSpeaking(false);
        fallbackBrowserSpeech(text);
      };
      audio.play().catch(() => {
        fallbackBrowserSpeech(text);
      });
    } else {
      fallbackBrowserSpeech(text);
    }
  };

  // Fallback to native Web Speech Synthesis if audio bytes not available
  const fallbackBrowserSpeech = (text) => {
    if ('speechSynthesis' in window) {
      window.speechSynthesis.cancel();
      const utterance = new SpeechSynthesisUtterance(text);
      utterance.rate = 0.95;
      utterance.onstart = () => setIsSpeaking(true);
      utterance.onend = () => setIsSpeaking(false);
      utterance.onerror = () => setIsSpeaking(false);
      window.speechSynthesis.speak(utterance);
    }
  };

  // Ask Voice Agent (query + current verification state)
  const handleAskAgent = async (queryText, currentVerifyResult = null) => {
    const vResult = currentVerifyResult !== null ? currentVerifyResult : verificationResult;
    setIsVoiceLoading(true);
    setVoiceQueryText(queryText);

    try {
      const payload = {
        merchant_id: merchantId,
        query: queryText,
        language: selectedLanguage,
        is_verified: !!vResult,
        is_valid: vResult ? vResult.is_valid : null,
        integrity_score: vResult ? vResult.integrity_score : null,
        scanned_vpa: vResult?.scanned_payload?.destination_vpa || null
      };

      const res = await askVoiceAgent(payload);
      setVoiceAgentResponse(res);
      playSpeech(res.spoken_text, res.audio_base64);
    } catch (err) {
      console.error('Voice agent error:', err);
    } finally {
      setIsVoiceLoading(false);
    }
  };

  // Microphone Push-to-Talk Handling
  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      audioChunksRef.current = [];
      const mediaRecorder = new MediaRecorder(stream);
      mediaRecorderRef.current = mediaRecorder;

      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };

      mediaRecorder.onstop = async () => {
        const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/webm' });
        setIsListening(false);
        setIsVoiceLoading(true);

        try {
          const sttRes = await transcribeVoiceAudio(audioBlob, selectedLanguage);
          const transcript = sttRes.transcript || "Is this QR code valid?";
          handleAskAgent(transcript);
        } catch (err) {
          console.warn('STT failed, using default regional prompt:', err);
          const fallbackQuery = QR_VOICE_SAMPLE_QUERIES[selectedLanguage]?.[0] || "Is this QR valid?";
          handleAskAgent(fallbackQuery);
        }
      };

      mediaRecorder.start();
      setIsListening(true);
    } catch (err) {
      console.warn('Mic access denied or unavailable, triggering quick query:', err);
      const sample = QR_VOICE_SAMPLE_QUERIES[selectedLanguage]?.[0] || "Is this QR valid?";
      handleAskAgent(sample);
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && isListening) {
      mediaRecorderRef.current.stop();
      mediaRecorderRef.current.stream.getTracks().forEach(track => track.stop());
    }
  };

  const sampleVoiceQueries = QR_VOICE_SAMPLE_QUERIES[selectedLanguage] || QR_VOICE_SAMPLE_QUERIES.en;

  return (
    <div className="h-full flex flex-col min-h-0 bg-canvas text-ink overflow-hidden font-sans">
      
      {/* Top Banner / System Bar */}
      <div className="px-4 py-2.5 border-b border-hairline bg-elevated flex flex-wrap items-center justify-between gap-3 shrink-0">
        <div className="flex items-center gap-2.5">
          <div className="p-1.5 rounded-sm bg-ink text-white shadow-whisper">
            <ShieldCheck className="h-4 w-4 text-emerald-400" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-sm font-semibold tracking-tight text-ink font-sans">
                Paytm QR Armor • Autonomous Provenance & Anti-Tamper Suite
              </h1>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-slate-100 text-body font-medium border border-hairline">
                Track 3: Autonomous AI Teammates
              </span>
            </div>
            <p className="text-[11px] text-mute font-mono">
              Dual-Binding Defense: Visible QR Payment Destination + Invisible Cryptographic HMAC Watermark
            </p>
          </div>
        </div>

        {/* Top Controls: Merchant Selector & Language Selector */}
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-1.5">
            <span className="text-xs font-mono text-mute">Merchant:</span>
            <select
              value={selectedMerchantId}
              onChange={(e) => setSelectedMerchantId(e.target.value)}
              className="text-xs font-mono font-medium px-2 py-1 rounded-sm border border-hairline bg-elevated text-ink focus:outline-none focus:border-ink cursor-pointer"
            >
              {DEMO_MERCHANTS.map((m) => (
                <option key={m.id} value={m.id}>
                  {m.name} ({m.vpa})
                </option>
              ))}
            </select>
          </div>

          <div className="flex items-center gap-1.5 px-2 py-1 rounded-sm border border-hairline bg-elevated text-xs">
            <Globe className="h-3.5 w-3.5 text-link shrink-0" />
            <select
              value={selectedLanguage}
              onChange={(e) => onLanguageChange && onLanguageChange(e.target.value)}
              className="bg-transparent text-xs font-medium text-ink focus:outline-none cursor-pointer pr-1"
            >
              {INDIAN_LANGUAGES.map((lang) => (
                <option key={lang.code} value={lang.code}>
                  {lang.nativeName} ({lang.name})
                </option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {/* Main 3-Column Studio Grid */}
      <div className="flex-1 min-h-0 grid grid-cols-1 lg:grid-cols-12 divide-y lg:divide-y-0 lg:divide-x divide-hairline overflow-y-auto">
        
        {/* PANEL 1 (col-span-4): Standee Generator & Cryptographic Signer */}
        <div className="lg:col-span-4 p-4 flex flex-col min-h-0 space-y-3 bg-elevated overflow-y-auto">
          <div className="flex items-center justify-between pb-1 border-b border-hairline">
            <div className="flex items-center gap-2">
              <span className="h-5 w-5 rounded-full bg-ink text-white text-[11px] font-mono font-bold flex items-center justify-center">
                1
              </span>
              <h2 className="text-xs font-mono font-semibold uppercase tracking-wider text-ink">
                Standee Generator & Signer
              </h2>
            </div>
            <button
              onClick={handleGenerate}
              disabled={isGenerating}
              className="flex items-center gap-1 px-2.5 py-1 text-xs font-mono rounded-sm border border-hairline hover:bg-slate-50 transition-colors disabled:opacity-50"
            >
              {isGenerating ? <Loader2 className="h-3 w-3 animate-spin" /> : <RefreshCw className="h-3 w-3" />}
              <span>Regenerate</span>
            </button>
          </div>

          <p className="text-[11px] text-body leading-relaxed">
            Generates the authentic Paytm standee with embedded cryptographic signature. The naked eye sees a clean Paytm QR, while pixel bitplanes hold the signed merchant provenance.
          </p>

          {/* Standee Artwork Display */}
          <div className="flex flex-col items-center justify-center p-3 border border-hairline rounded-md bg-canvas relative">
            {isGenerating ? (
              <div className="flex flex-col items-center gap-2 py-12 text-mute text-xs font-mono">
                <Loader2 className="h-6 w-6 animate-spin text-ink" />
                <span>Computing 4-Bit LSB Matrix...</span>
              </div>
            ) : stegoData ? (
              <div className="flex flex-col items-center space-y-2">
                <div className="relative border border-hairline rounded-md overflow-hidden bg-white shadow-whisper">
                  <img
                    src={
                      showSecretLayer
                        ? `data:image/png;base64,${stegoData.extracted_qr_base64}`
                        : `data:image/png;base64,${stegoData.stego_image_base64}`
                    }
                    alt="Paytm Standee"
                    className="w-52 h-52 object-contain"
                  />
                  <span className="absolute bottom-1 right-1 text-[9px] font-mono px-1.5 py-0.5 rounded bg-black/80 text-white">
                    {showSecretLayer ? 'Secret Watermark Layer' : 'Official Standee'}
                  </span>
                </div>

                <div className="flex items-center gap-2 pt-1">
                  <button
                    onClick={() => setShowSecretLayer(!showSecretLayer)}
                    className="flex items-center gap-1 px-2.5 py-1 text-[11px] font-mono rounded-sm border border-hairline bg-elevated hover:bg-slate-50 text-ink shadow-whisper"
                  >
                    {showSecretLayer ? <EyeOff className="h-3 w-3" /> : <Eye className="h-3 w-3" />}
                    <span>{showSecretLayer ? 'View Standee' : 'Inspect Secret Layer'}</span>
                  </button>
                </div>
              </div>
            ) : null}
          </div>

          {/* Issued Provenance Metadata Card */}
          {stegoData?.issued_payload && (
            <div className="p-2.5 rounded-md border border-hairline bg-slate-50 space-y-1.5 text-[11px] font-mono">
              <div className="flex items-center justify-between text-mute border-b border-hairline pb-1">
                <span>CRYPTOGRAPHIC BINDING</span>
                <span className="text-emerald-600 font-bold">SIGNED</span>
              </div>
              <div className="grid grid-cols-3 gap-1">
                <span className="text-mute">Destination:</span>
                <span className="col-span-2 text-ink font-bold truncate">{stegoData.issued_payload.destination_vpa}</span>
              </div>
              <div className="grid grid-cols-3 gap-1">
                <span className="text-mute">Bank A/C:</span>
                <span className="col-span-2 text-ink truncate">{stegoData.issued_payload.bank_account}</span>
              </div>
              <div className="grid grid-cols-3 gap-1">
                <span className="text-mute">HMAC Hash:</span>
                <span className="col-span-2 text-ink truncate text-[10px] text-link">
                  {stegoData.issued_payload.digital_signature.slice(0, 24)}...
                </span>
              </div>
            </div>
          )}

          {/* Action Buttons */}
          <div className="pt-1 flex flex-col gap-2 shrink-0">
            <button
              onClick={handleLoadGenuine}
              disabled={!stegoData || isGenerating}
              className="flex items-center justify-center gap-2 px-4 py-2 text-xs font-medium rounded-pill bg-ink text-white hover:bg-black transition-colors disabled:opacity-50 shadow-whisper"
            >
              <span>Test This Genuine Standee</span>
              <ArrowRight className="h-3.5 w-3.5" />
            </button>

            <button
              onClick={handleDownload}
              disabled={!stegoData || isGenerating}
              className="flex items-center justify-center gap-1.5 px-3 py-1.5 text-xs font-mono rounded-sm border border-hairline bg-elevated hover:bg-slate-50 text-body transition-colors disabled:opacity-50"
            >
              <Download className="h-3.5 w-3.5" />
              <span>Download Standee (.PNG)</span>
            </button>
          </div>
        </div>

        {/* PANEL 2 (col-span-5): Dual-Binding Verifier & Payload Comparison */}
        <div className="lg:col-span-5 p-4 flex flex-col min-h-0 space-y-3 bg-canvas overflow-y-auto">
          <div className="flex items-center justify-between pb-1 border-b border-hairline">
            <div className="flex items-center gap-2">
              <span className="h-5 w-5 rounded-full bg-ink text-white text-[11px] font-mono font-bold flex items-center justify-center">
                2
              </span>
              <h2 className="text-xs font-mono font-semibold uppercase tracking-wider text-ink">
                Dual-Binding Verifier
              </h2>
            </div>

            <button
              onClick={handleSimulateTamper}
              disabled={isVerifying}
              className="flex items-center gap-1 px-2.5 py-1 text-xs font-mono rounded-sm bg-rose-50 text-rose-700 border border-rose-200 hover:bg-rose-100 transition-colors disabled:opacity-50"
              title="Simulates a thief sticking a fake QR sticker over the merchant's code"
            >
              <AlertTriangle className="h-3 w-3" />
              <span>Simulate Thief Tampering</span>
            </button>
          </div>

          <p className="text-[11px] text-body leading-relaxed">
            Upload the physical standee. The engine decodes both the <strong>visible payment destination</strong> and the <strong>invisible cryptographic bitplanes</strong> to detect sticker overlays, altered VPAs, or digital tampering.
          </p>

          {/* Hidden File Picker */}
          <input
            ref={fileInputRef}
            type="file"
            accept="image/png,image/jpeg,image/webp"
            className="hidden"
            onChange={handleFileUpload}
          />

          {/* Dropzone */}
          <div
            onClick={() => fileInputRef.current?.click()}
            className="cursor-pointer border-2 border-dashed border-hairline hover:border-ink rounded-md p-3 bg-elevated hover:bg-slate-50 transition-all flex flex-col items-center justify-center gap-1 text-center"
          >
            <Upload className="h-4 w-4 text-mute" />
            <span className="text-xs font-mono font-medium text-ink">
              {uploadedFileName ? `Loaded: ${uploadedFileName}` : 'Click to Upload Standee Image'}
            </span>
            <span className="text-[10px] text-mute font-mono">
              Upload genuine template or tampered sticker image
            </span>
          </div>

          {verifyError && (
            <div className="p-2 text-xs bg-rose-50 text-rose-700 border border-rose-200 rounded-sm">
              {verifyError}
            </div>
          )}

          {/* Verification Results Display */}
          {isVerifying ? (
            <div className="flex-1 flex flex-col items-center justify-center p-8 bg-elevated border border-hairline rounded-md text-mute text-xs font-mono space-y-2">
              <Loader2 className="h-6 w-6 animate-spin text-ink" />
              <span>Unmerging LSB Bitplanes & Auditing Cryptographic Provenance...</span>
            </div>
          ) : verificationResult ? (
            <div className="space-y-3">
              {/* Verdict Header Alert */}
              <div
                className={`p-3 rounded-md border ${
                  verificationResult.is_valid
                    ? 'bg-emerald-50/80 border-emerald-300 text-emerald-950'
                    : 'bg-rose-50/90 border-rose-300 text-rose-950'
                }`}
              >
                <div className="flex items-start gap-2.5">
                  {verificationResult.is_valid ? (
                    <CheckCircle2 className="h-5 w-5 text-emerald-600 shrink-0 mt-0.5" />
                  ) : (
                    <ShieldAlert className="h-5 w-5 text-rose-600 shrink-0 mt-0.5" />
                  )}
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-mono font-bold uppercase tracking-wide">
                        {verificationResult.is_valid ? 'GENUINE PAYTM QR AUTHENTICATED' : 'CRITICAL: PHYSICAL QR TAMPERING DETECTED'}
                      </span>
                      <span className="text-[10px] font-mono font-bold px-1.5 py-0.5 rounded bg-white/80 border border-current">
                        Integrity: {verificationResult.integrity_score}%
                      </span>
                    </div>
                    <p className="text-xs mt-1 leading-relaxed">
                      {verificationResult.message}
                    </p>
                  </div>
                </div>
              </div>

              {/* DUAL-BINDING PAYLOAD COMPARISON TABLE (User Core Requirement) */}
              <div className="border border-hairline rounded-md bg-elevated overflow-hidden shadow-whisper">
                <div className="px-3 py-2 bg-slate-50 border-b border-hairline flex items-center justify-between">
                  <span className="text-[11px] font-mono uppercase font-bold text-ink">
                    Dual-Binding Verification Breakdown
                  </span>
                  <span className="text-[10px] font-mono text-mute">
                    Visible Payload vs Hidden Watermark
                  </span>
                </div>

                <div className="divide-y divide-hairline text-xs font-mono">
                  {verificationResult.comparison?.map((row, idx) => (
                    <div key={idx} className="p-2.5 grid grid-cols-12 gap-2 items-center hover:bg-slate-50/50">
                      <div className="col-span-4 text-mute text-[11px]">{row.property}</div>
                      <div className="col-span-3 text-ink truncate text-[11px]" title={row.expected}>
                        {row.expected}
                      </div>
                      <div className={`col-span-3 truncate text-[11px] font-semibold ${row.status === 'MATCH' ? 'text-emerald-700' : 'text-rose-600'}`} title={row.scanned}>
                        {row.scanned}
                      </div>
                      <div className="col-span-2 text-right">
                        <span className={`text-[10px] px-1.5 py-0.5 rounded font-bold ${
                          row.status === 'MATCH'
                            ? 'bg-emerald-100 text-emerald-800'
                            : 'bg-rose-100 text-rose-800'
                        }`}>
                          {row.status}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Side-by-Side Image Visualizer */}
              <div className="grid grid-cols-2 gap-2">
                <div className="flex flex-col items-center p-2 rounded-md border border-hairline bg-elevated">
                  <span className="text-[10px] font-mono text-mute mb-1">Uploaded Standee</span>
                  {uploadedImageBase64 ? (
                    <img
                      src={uploadedImageBase64}
                      alt="Uploaded Standee"
                      className="w-24 h-24 object-contain border border-hairline rounded bg-white"
                    />
                  ) : (
                    <div className="w-24 h-24 bg-slate-100 flex items-center justify-center text-[10px] text-mute">
                      No Image
                    </div>
                  )}
                </div>

                <div className="flex flex-col items-center p-2 rounded-md border border-hairline bg-elevated">
                  <span className="text-[10px] font-mono text-mute mb-1">Decoded Secret Layer</span>
                  {verificationResult.decoded_qr_base64 ? (
                    <img
                      src={`data:image/png;base64,${verificationResult.decoded_qr_base64}`}
                      alt="Decoded Secret"
                      className="w-24 h-24 object-contain border border-hairline rounded bg-white"
                    />
                  ) : (
                    <div className="w-24 h-24 bg-slate-100 flex items-center justify-center text-[10px] text-mute">
                      Decoding Failed
                    </div>
                  )}
                </div>
              </div>
            </div>
          ) : (
            <div className="p-8 border border-hairline rounded-md bg-elevated flex flex-col items-center justify-center text-center gap-2 text-mute">
              <ShieldCheck className="h-8 w-8 text-slate-300" />
              <span className="text-xs font-mono font-medium text-ink">No Standee Verified Yet</span>
              <p className="text-[11px] max-w-xs text-body">
                Click <strong>"Test This Genuine Standee"</strong> on the left or <strong>"Simulate Thief Tampering"</strong> above to see the dual-layer verification in action.
              </p>
            </div>
          )}
        </div>

        {/* PANEL 3 (col-span-3): Voice Agent & Autonomous Remediation Center */}
        <div className="lg:col-span-3 p-4 flex flex-col min-h-0 space-y-3 bg-elevated overflow-y-auto">
          <div className="flex items-center justify-between pb-1 border-b border-hairline">
            <div className="flex items-center gap-2">
              <span className="h-5 w-5 rounded-full bg-ink text-white text-[11px] font-mono font-bold flex items-center justify-center">
                3
              </span>
              <h2 className="text-xs font-mono font-semibold uppercase tracking-wider text-ink">
                Voice Agent & Ops Center
              </h2>
            </div>
            
            <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-blue-50 text-link font-medium border border-blue-200">
              Sarvam AI Neural Audio
            </span>
          </div>

          <p className="text-[11px] text-body leading-relaxed">
            Zero-chat conversational voice agent. Speak in any of the top 10 Indian languages to ask if your QR is safe. The agent speaks back directly and performs autonomous security operations.
          </p>

          {/* Large Push-To-Talk Voice Interface */}
          <div className="p-3 border border-hairline rounded-md bg-canvas flex flex-col items-center justify-center space-y-2 relative overflow-hidden">
            {/* Visual Ripple effect when speaking or listening */}
            {(isListening || isSpeaking) && (
              <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
                <div className={`w-36 h-36 rounded-full animate-ping opacity-20 ${isSpeaking ? 'bg-emerald-500' : 'bg-link'}`} />
              </div>
            )}

            <button
              onMouseDown={startRecording}
              onMouseUp={stopRecording}
              onTouchStart={startRecording}
              onTouchEnd={stopRecording}
              disabled={isVoiceLoading}
              className={`relative z-10 w-16 h-16 rounded-full flex items-center justify-center text-white transition-all shadow-md ${
                isListening
                  ? 'bg-rose-600 scale-105'
                  : isSpeaking
                  ? 'bg-emerald-600 animate-pulse'
                  : 'bg-ink hover:bg-black'
              }`}
              title="Hold to speak or click to ask"
            >
              {isVoiceLoading ? (
                <Loader2 className="h-6 w-6 animate-spin" />
              ) : isSpeaking ? (
                <Volume2 className="h-6 w-6 animate-bounce" />
              ) : isListening ? (
                <Radio className="h-6 w-6 animate-pulse" />
              ) : (
                <Mic className="h-6 w-6" />
              )}
            </button>

            <div className="text-center">
              <span className="text-xs font-mono font-bold text-ink block">
                {isListening
                  ? 'Listening... Release to Ask'
                  : isSpeaking
                  ? 'Agent Speaking Aloud...'
                  : isVoiceLoading
                  ? 'Analyzing QR Provenance...'
                  : 'Hold Mic to Speak'}
              </span>
              <span className="text-[10px] text-mute font-mono">
                {isListening ? 'Recording voice audio' : 'Or tap a quick spoken question below'}
              </span>
            </div>
          </div>

          {/* Quick Regional Voice Prompt Chips */}
          <div className="space-y-1">
            <span className="text-[10px] font-mono uppercase text-mute font-bold tracking-wider">
              Quick Spoken Questions ({INDIAN_LANGUAGES.find(l => l.code === selectedLanguage)?.nativeName}):
            </span>
            <div className="flex flex-col gap-1.5">
              {sampleVoiceQueries.map((query, idx) => (
                <button
                  key={idx}
                  onClick={() => handleAskAgent(query)}
                  disabled={isVoiceLoading}
                  className="text-left px-2.5 py-1.5 text-[11px] rounded-sm border border-hairline bg-canvas hover:bg-slate-100 hover:border-ink transition-colors text-ink disabled:opacity-50 flex items-center justify-between group"
                >
                  <span className="truncate pr-1">"{query}"</span>
                  <Play className="h-3 w-3 text-mute group-hover:text-ink shrink-0" />
                </button>
              ))}
            </div>
          </div>

          {/* Agent Transcript Card */}
          {voiceAgentResponse && (
            <div className="p-3 rounded-md border border-hairline bg-slate-50 space-y-2 text-xs">
              <div className="flex items-center justify-between text-[10px] font-mono text-mute border-b border-hairline pb-1">
                <span>VOICE AGENT TRANSCRIPT</span>
                <button
                  onClick={() => playSpeech(voiceAgentResponse.spoken_text, voiceAgentResponse.audio_base64)}
                  className="flex items-center gap-1 text-link hover:underline font-bold"
                >
                  <Volume2 className="h-3 w-3" />
                  <span>Replay Voice</span>
                </button>
              </div>

              {voiceQueryText && (
                <div className="text-[11px] text-body italic">
                  <strong>You asked:</strong> "{voiceQueryText}"
                </div>
              )}

              <div className="text-xs text-ink leading-relaxed font-sans bg-white p-2 rounded border border-hairline">
                {voiceAgentResponse.spoken_text}
              </div>
            </div>
          )}

          {/* Autonomous Security Actions Checklist */}
          <div className="pt-1 space-y-1.5 border-t border-hairline">
            <div className="flex items-center justify-between text-[11px] font-mono uppercase font-bold text-ink">
              <span>Autonomous Ops Execution</span>
              <span className="text-[10px] text-emerald-600 font-bold">LIVE TELEMETRY</span>
            </div>

            <div className="space-y-1 text-[11px] font-mono">
              <div className="p-2 rounded border border-hairline bg-canvas flex items-center justify-between">
                <span className="text-body flex items-center gap-1.5">
                  <Lock className="h-3.5 w-3.5 text-mute" />
                  <span>Settlement Payout Rail:</span>
                </span>
                <span className={`font-bold px-1.5 py-0.2 rounded text-[10px] ${
                  verificationResult && !verificationResult.is_valid
                    ? 'bg-rose-100 text-rose-800'
                    : 'bg-emerald-100 text-emerald-800'
                }`}>
                  {verificationResult && !verificationResult.is_valid ? 'FROZEN (PROTECTED)' : 'ACTIVE'}
                </span>
              </div>

              <div className="p-2 rounded border border-hairline bg-canvas flex items-center justify-between">
                <span className="text-body flex items-center gap-1.5">
                  <Radio className="h-3.5 w-3.5 text-mute" />
                  <span>Soundbox SB-4402 Alert:</span>
                </span>
                <span className={`font-bold px-1.5 py-0.2 rounded text-[10px] ${
                  verificationResult && !verificationResult.is_valid
                    ? 'bg-rose-100 text-rose-800 animate-pulse'
                    : 'bg-slate-100 text-body'
                }`}>
                  {verificationResult && !verificationResult.is_valid ? 'FRAUD ALERT SPOKEN' : 'STANDBY'}
                </span>
              </div>

              <div className="p-2 rounded border border-hairline bg-canvas flex items-center justify-between">
                <span className="text-body flex items-center gap-1.5">
                  <FileText className="h-3.5 w-3.5 text-mute" />
                  <span>NPCI Fraud Docket:</span>
                </span>
                <span className="font-bold text-[10px] text-ink">
                  {verificationResult && !verificationResult.is_valid ? (verificationResult.incident_id || 'INC-QR-89104') : 'NONE'}
                </span>
              </div>
            </div>
          </div>

        </div>

      </div>
    </div>
  );
}
