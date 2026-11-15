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
  Loader2, 
  RefreshCw,
  Zap,
  ArrowRight
} from 'lucide-react';
import { generateStegoTemplate, verifyStegoImage, getSampleTamperedTemplate } from './api';

export default function AntiTamperQRView({ merchant }) {
  const merchantId = merchant?.id || 'M-101';
  const merchantName = merchant?.name || 'Verified Merchant';
  const vpa = merchant?.username ? `${merchant.username}@paytm` : 'merchant@paytm';

  // Generation state
  const [isGenerating, setIsGenerating] = useState(false);
  const [stegoData, setStegoData] = useState(null);
  const [showSecretLayer, setShowSecretLayer] = useState(false);
  const [genError, setGenError] = useState(null);

  // Verification state
  const [isVerifying, setIsVerifying] = useState(false);
  const [uploadedImageBase64, setUploadedImageBase64] = useState(null);
  const [uploadedFileName, setUploadedFileName] = useState('');
  const [verificationResult, setVerificationResult] = useState(null);
  const [verifyError, setVerifyError] = useState(null);

  const fileInputRef = useRef(null);

  // Auto-generate on first mount or merchant switch
  useEffect(() => {
    handleGenerate();
    setVerificationResult(null);
    setUploadedImageBase64(null);
    setUploadedFileName('');
  }, [merchantId]);

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

  const runVerification = async (base64Img, fileName = 'uploaded_image.png') => {
    setIsVerifying(true);
    setVerifyError(null);
    setVerificationResult(null);
    setUploadedImageBase64(base64Img);
    setUploadedFileName(fileName);

    try {
      const result = await verifyStegoImage(merchantId, base64Img);
      setVerificationResult(result);
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

  const handleSimulateTamper = async () => {
    setIsVerifying(true);
    setVerifyError(null);
    setVerificationResult(null);
    try {
      const tampered = await getSampleTamperedTemplate(merchantId);
      const b64 = `data:image/png;base64,${tampered.tampered_image_base64}`;
      setUploadedImageBase64(b64);
      setUploadedFileName('Tampered_Rogue_Sticker.png');
      const result = await verifyStegoImage(merchantId, tampered.tampered_image_base64);
      setVerificationResult(result);
    } catch (err) {
      setVerifyError(err.message || 'Failed to simulate tamper test');
    } finally {
      setIsVerifying(false);
    }
  };

  const handleLoadGenuineDirectly = () => {
    if (!stegoData?.stego_image_base64) return;
    const b64 = `data:image/png;base64,${stegoData.stego_image_base64}`;
    runVerification(b64, stegoData.download_filename || 'Genuine_Paytm_Standee.png');
  };

  return (
    <div className="h-full flex flex-col min-h-0 bg-white border border-hairline rounded-sm overflow-hidden text-ink">
      {/* Top Banner / System Description */}
      <div className="p-3 border-b border-hairline bg-slate-50 flex flex-wrap items-center justify-between gap-2 shrink-0">
        <div className="flex items-center gap-2">
          <div className="p-1.5 rounded-sm bg-accentBlue text-white shadow-sm">
            <QrCode className="h-4 w-4" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h2 className="text-sm font-semibold tracking-tight text-ink">
                Anti-Tamper Steganographic QR System
              </h2>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-blue-100 text-accentBlueDeep font-medium">
                4-Bit LSB Bitplane Security
              </span>
            </div>
            <p className="text-xs text-mute">
              Prevents counter QR sticker swap theft by hiding cryptographic payment matrices inside the standee pixels.
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <span className="text-xs font-mono text-bodyText">
            Merchant: <strong className="text-ink">{merchantName}</strong> ({vpa})
          </span>
        </div>
      </div>

      {/* Main 2-Column Workflow Area */}
      <div className="flex-1 min-h-0 grid grid-cols-1 md:grid-cols-2 divide-y md:divide-y-0 md:divide-x divide-hairline overflow-y-auto">
        
        {/* LEFT COLUMN: Step 1 - Generate & Download Protected Template */}
        <div className="p-3.5 flex flex-col min-h-0 space-y-3 bg-white">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-1.5">
              <span className="h-5 w-5 rounded-full bg-ink text-white text-[11px] font-mono font-bold flex items-center justify-center">
                1
              </span>
              <h3 className="text-xs font-mono font-semibold uppercase tracking-wider text-ink">
                Generate Stego Standee
              </h3>
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

          <p className="text-xs text-mute">
            The merchant's real UPI QR code is invisibly merged into this Paytm standee. To the naked eye it looks like an official template, but pixel bitplanes contain the tamper-sensitive QR.
          </p>

          {genError && (
            <div className="p-2 text-xs bg-rose-50 text-rose-700 border border-rose-200 rounded-sm">
              {genError}
            </div>
          )}

          {/* Standee Preview Box */}
          <div className="flex-1 min-h-[260px] flex flex-col items-center justify-center p-3 border border-hairlineSoft rounded-sm bg-slate-50 relative group">
            {isGenerating ? (
              <div className="flex flex-col items-center gap-2 text-mute text-xs font-mono">
                <Loader2 className="h-6 w-6 animate-spin text-accentBlue" />
                <span>Computing LSB Bitplane Matrices...</span>
              </div>
            ) : stegoData ? (
              <div className="flex flex-col items-center space-y-2">
                <div className="relative border-2 border-hairline rounded-md overflow-hidden shadow-sm bg-white">
                  <img
                    src={
                      showSecretLayer
                        ? `data:image/png;base64,${stegoData.extracted_qr_base64}`
                        : `data:image/png;base64,${stegoData.stego_image_base64}`
                    }
                    alt="Steganographic Standee"
                    className="w-56 h-56 object-contain"
                  />
                  <span className="absolute bottom-1 right-1 text-[9px] font-mono px-1.5 py-0.5 rounded bg-black/75 text-white">
                    {showSecretLayer ? 'Secret QR Layer' : 'Standee (Invisible QR)'}
                  </span>
                </div>

                <div className="flex items-center gap-2 pt-1">
                  <button
                    onClick={() => setShowSecretLayer(!showSecretLayer)}
                    className="flex items-center gap-1 px-2 py-0.5 text-[11px] font-mono rounded border border-hairline bg-white hover:bg-slate-100 text-bodyText"
                    title="Toggle to view the cryptographic secret QR matrix hidden inside"
                  >
                    {showSecretLayer ? <EyeOff className="h-3 w-3" /> : <Eye className="h-3 w-3" />}
                    <span>{showSecretLayer ? 'Show Standee' : 'Inspect Secret QR'}</span>
                  </button>
                </div>
              </div>
            ) : null}
          </div>

          {/* Action Buttons */}
          <div className="pt-1 flex flex-col sm:flex-row gap-2 shrink-0">
            <button
              onClick={handleDownload}
              disabled={!stegoData || isGenerating}
              className="flex-1 flex items-center justify-center gap-1.5 px-3 py-2 text-xs font-mono font-medium rounded-sm bg-accentBlue text-white hover:bg-blue-600 transition-colors disabled:opacity-50 shadow-whisper"
            >
              <Download className="h-3.5 w-3.5" />
              <span>Download Standee (.PNG)</span>
            </button>

            <button
              onClick={handleLoadGenuineDirectly}
              disabled={!stegoData || isGenerating}
              className="flex items-center justify-center gap-1 px-3 py-2 text-xs font-mono rounded-sm border border-hairline bg-slate-50 hover:bg-slate-100 text-ink disabled:opacity-50"
              title="Instantly test this genuine template in the verification engine without manual file picking"
            >
              <span>Test This Template</span>
              <ArrowRight className="h-3.5 w-3.5" />
            </button>
          </div>
        </div>

        {/* RIGHT COLUMN: Step 2 - Upload & Verify Counter QR Authenticity */}
        <div className="p-3.5 flex flex-col min-h-0 space-y-3 bg-white">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-1.5">
              <span className="h-5 w-5 rounded-full bg-ink text-white text-[11px] font-mono font-bold flex items-center justify-center">
                2
              </span>
              <h3 className="text-xs font-mono font-semibold uppercase tracking-wider text-ink">
                Upload & Verify Authenticity
              </h3>
            </div>
            
            <button
              onClick={handleSimulateTamper}
              disabled={isVerifying}
              className="flex items-center gap-1 px-2.5 py-1 text-xs font-mono rounded-sm bg-rose-50 text-rose-700 border border-rose-200 hover:bg-rose-100 transition-colors disabled:opacity-50"
              title="Simulates a thief pasting a sticker or drawing a dot on the standee"
            >
              <AlertTriangle className="h-3 w-3" />
              <span>Simulate Thief Tampering</span>
            </button>
          </div>

          <p className="text-xs text-mute">
            Upload any standee image. The engine will unmerge the LSB bitplanes, audit the 3 QR position markers, and detect if thieves drew a dot, edited pixels, or replaced the code.
          </p>

          {/* Hidden File Input */}
          <input
            ref={fileInputRef}
            type="file"
            accept="image/png,image/jpeg,image/webp"
            className="hidden"
            onChange={handleFileUpload}
          />

          {/* Upload Dropzone */}
          <div
            onClick={() => fileInputRef.current?.click()}
            className="cursor-pointer border-2 border-dashed border-hairline hover:border-accentBlue rounded-sm p-3 bg-slate-50/70 hover:bg-blue-50/30 transition-all flex flex-col items-center justify-center gap-1 text-center"
          >
            <Upload className="h-5 w-5 text-mute" />
            <span className="text-xs font-mono font-medium text-ink">
              {uploadedFileName ? `Loaded: ${uploadedFileName}` : 'Click or Drop Standee Image Here'}
            </span>
            <span className="text-[10px] text-mute font-mono">
              Accepts lossless .PNG or .JPG standee files
            </span>
          </div>

          {verifyError && (
            <div className="p-2 text-xs bg-rose-50 text-rose-700 border border-rose-200 rounded-sm">
              {verifyError}
            </div>
          )}

          {/* Verification Results Area */}
          <div className="flex-1 min-h-[220px] flex flex-col justify-center">
            {isVerifying ? (
              <div className="flex flex-col items-center justify-center gap-2 p-6 text-mute text-xs font-mono bg-slate-50 rounded-sm">
                <Loader2 className="h-6 w-6 animate-spin text-accentBlue" />
                <span>Auditing bitplanes and decoding hidden QR matrix...</span>
              </div>
            ) : verificationResult ? (
              <div className="space-y-2.5">
                {/* Result Verdict Card */}
                <div
                  className={`p-3 rounded-sm border ${
                    verificationResult.is_valid
                      ? 'bg-emerald-50 border-emerald-300 text-emerald-950'
                      : 'bg-rose-50 border-rose-300 text-rose-950'
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
                          {verificationResult.is_valid ? 'GENUINE AUTHENTICATED' : 'TAMPERED / FAKE DETECTED'}
                        </span>
                        <span className="text-[11px] font-mono font-bold px-1.5 py-0.2 rounded bg-white/70 border border-current">
                          Integrity: {verificationResult.integrity_score}%
                        </span>
                      </div>
                      <p className="text-xs mt-1 leading-relaxed">
                        {verificationResult.message}
                      </p>
                    </div>
                  </div>
                </div>

                {/* Side-by-Side Decoded Inspection */}
                <div className="grid grid-cols-2 gap-2 pt-1">
                  <div className="flex flex-col items-center p-2 rounded border border-hairline bg-slate-50">
                    <span className="text-[10px] font-mono text-mute mb-1">Uploaded Standee</span>
                    {uploadedImageBase64 ? (
                      <img
                        src={uploadedImageBase64}
                        alt="Uploaded"
                        className="w-28 h-28 object-contain border border-hairlineSoft rounded bg-white shadow-xs"
                      />
                    ) : (
                      <div className="w-28 h-28 bg-slate-100 flex items-center justify-center text-[10px] text-mute">
                        No image
                      </div>
                    )}
                  </div>

                  <div className="flex flex-col items-center p-2 rounded border border-hairline bg-slate-50">
                    <span className="text-[10px] font-mono text-mute mb-1">Decoded Secret QR Layer</span>
                    {verificationResult.decoded_qr_base64 ? (
                      <img
                        src={`data:image/png;base64,${verificationResult.decoded_qr_base64}`}
                        alt="Decoded Secret QR"
                        className="w-28 h-28 object-contain border border-hairlineSoft rounded bg-white shadow-xs"
                      />
                    ) : (
                      <div className="w-28 h-28 bg-slate-100 flex items-center justify-center text-[10px] text-mute">
                        Decoding failed
                      </div>
                    )}
                  </div>
                </div>
              </div>
            ) : (
              <div className="p-4 border border-hairlineSoft rounded-sm bg-slate-50/50 flex flex-col items-center justify-center text-center gap-1.5 text-mute">
                <ShieldCheck className="h-6 w-6 text-slate-300" />
                <span className="text-xs font-mono">No Standee Verified Yet</span>
                <span className="text-[11px]">
                  Upload a standee or click "Simulate Thief Tampering" above to test.
                </span>
              </div>
            )}
          </div>
        </div>

      </div>
    </div>
  );
}
