# Paytm QR Armor - Live Hackathon Presentation Guide
### Track 3: Autonomous AI Teammates
**Motto:** *"Cryptographically bind physical QR standees to merchant identity. Stop physical payment diversion at the counter."*

---

## 🚀 1-Click Startup Instructions

1. **Option A (Double-Click Batch):** Run `start_demo.bat`
2. **Option B (PowerShell):** Run `.\start_demo.ps1`
3. **Option C (Manual):**
   * Terminal 1: `cd backend && ..\venv\bin\python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload`
   * Terminal 2: `cd frontend && npm run dev`

Open your browser at: **`http://localhost:5173`**  
Backend Swagger Docs: **`http://localhost:8000/docs`**

---

## 🎯 The Pitch to Judges (60 Seconds)

> *"Judges, today Paytm's official guidance still tells shopkeepers: 'Before paying, verify the merchant name shown on your screen'. But in real life, customers in rush don't check names. In December 2025, Delhi Police arrested fraudsters who altered over 100 merchant QR codes with physical stickers to divert payments to thief accounts.*
>
> *Today we present **Paytm QR Armor**: An autonomous security teammate that solves physical QR tampering using **Dual-Binding Cryptographic Provenance**:*
> 1. *The **Visible QR Payload** routes to the merchant's UPI VPA.*
> 2. *An **Invisible Cryptographic Watermark (HMAC-SHA256)** is embedded directly inside the standee bitplanes.*
>
> *If an attacker alters the QR code or pastes a sticker over it, the dual-binding breaks. The autonomous AI agent immediately freezes the compromised payout route, broadcasts a spoken fraud warning on the merchant's physical Soundbox, and alerts the merchant in their regional language."*

---

## 🎪 Step-by-Step Stage Demo Flow

### Step 1: Generate Merchant Standee (Panel 1)
1. Select **Ramesh Kirana Store (`M-101`)**.
2. Notice the generated Paytm standee with official cyan branding and central QR code.
3. Click **"Inspect Secret Layer"** to reveal the invisible steganographic watermark matrix hidden in the bitplanes.
4. Show the **Signed Cryptographic Metadata Card**:
   - Destination VPA: `ramesh_kirana@paytm`
   - Digital HMAC Signature: `HMAC-SHA256:cac7ca03...`
5. Click **"Test This Genuine Standee"**.

### Step 2: Verify Genuine Standee (Panel 2)
1. The engine unmerges the LSB bitplanes and audits the 3 corner finder pattern boxes.
2. Result: **`GENUINE PAYTM QR AUTHENTICATED`** (Integrity: `96.6%`).
3. Show the **Dual-Binding Breakdown Table**:
   - Visible Destination VPA: `ramesh_kirana@paytm` (MATCH)
   - Merchant Name: `Ramesh Kirana Store` (MATCH)
   - Cryptographic Watermark: `HMAC Valid` (MATCH)
   - Bitplane Matrix Integrity: `96.6%` (MATCH)

### Step 3: Simulate Physical Sticker Tampering (Delhi Police Fraud Scenario)
1. In Panel 2, click the red button: **"Simulate Thief Tampering"**.
2. Notice the uploaded standee now has a rogue thief QR sticker pasted over the original QR code!
3. The engine instantly flags: **`⚠️ CRITICAL: PHYSICAL QR TAMPERING DETECTED`**.
4. Show the **Payload Comparison Table**:
   - Visible Scanned VPA: `thief_scam99@ybl` (MISMATCH! Diverted to thief!)
   - Merchant Name: `Quick Discount Pay (Rogue Destination)` (MISMATCH!)
   - Cryptographic Watermark: `CORRUPTED / OVERLAID` (MISMATCH!)
   - Bitplane Integrity: `24.8%` (FAIL! Well below 85% safety threshold!)

### Step 4: Autonomous Security Remediation
Show the live telemetry under Panel 3:
- 🛡️ **Settlement Payout Rail:** Immediately flipped to **`FROZEN (PROTECTED)`** to stop diverted funds from leaving.
- 🔊 **Soundbox SB-4402 Alert:** Spoken fraud warning emitted: *"Savdhan: Physical QR tamper detected!"*
- 📁 **NPCI Fraud Docket:** Formally filed with cryptographic hash proof (`#INC-QR-764825`).

### Step 5: Multilingual Voice Agent (No Chatbot!)
1. In Panel 3, click any of the **Quick Spoken Questions** or hold the **Mic button** to speak (e.g. *"Is this QR code valid?"* or in Hindi *"क्या यह क्यूआर सुरक्षित है?"*).
2. The AI Agent responds **out loud** with neural spoken audio using Sarvam AI Bulbul TTS (or Edge TTS).
3. The spoken voice explains the exact tamper diagnosis and reassures the merchant in their regional language (Hindi, Marathi, Gujarati, Tamil, etc.).

---

## 🏆 Why This Wins Track 3: Autonomous AI Teammates
1. **Real Problem:** Solves physical counter QR sticker alteration, an active UPI crime vector reported by Delhi Police and NPCI.
2. **Dual-Layer Defense:** Merges visible UPI payments with invisible cryptographic steganography.
3. **Autonomous Actions:** Not just an image scanner—it actively freezes payouts, triggers Soundbox hardware alerts, and files fraud dossiers.
4. **Voice-First Experience:** 100% voice interaction with natural Indian language neural audio.
