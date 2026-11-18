# Paytm QR Armor - Autonomous Physical QR Provenance & Anti-Tamper Security Agent

> **Paytm India AI Hackathon (Track 3: Autonomous AI Teammates)**  
> An autonomous AI security teammate that cryptographically binds physical merchant QR standees to merchant identity and defends against physical sticker replacement and payment diversion fraud.

---

## 💡 The Core Problem: Counter QR Tampering & Sticker Swaps

In December 2025, Delhi Police uncovered a fraud ring that altered over 100 genuine merchant QR codes by pasting fraudulent stickers over them to divert payments. Current UPI systems rely solely on asking busy merchants and customers to verify the name displayed on their phones.

**Paytm QR Armor** solves this through **Dual-Binding Cryptographic Provenance**:
1. **Visible QR Destination:** Scanned UPI VPA (`ramesh_kirana@paytm`)
2. **Invisible Cryptographic Watermark:** HMAC-SHA256 digital signature embedded into the standee bitplanes via 4-bit LSB steganography.
3. **Autonomous Remediation:** If either layer differs, the autonomous AI agent freezes settlement payouts, emits a spoken warning on the Paytm Soundbox, and files an NPCI fraud dossier.

---

## 🚀 Quick Start (Setup in 3 Steps)

### 1. Prerequisites
- **Python 3.10+**
- **Node.js 18+**

### 2. Backend Setup
```bash
# Setup virtual environment and dependencies
uv venv venv
uv pip install --python venv -r requirements.txt
```

### 3. Frontend Setup
```bash
cd frontend
npm install
cd ..
```

---

## 🏃 Running the Application

### Option A: 1-Click Launch (Windows)
Double-click `start_demo.bat` or run:
```bash
.\start_demo.bat
```

### Option B: Manual Launch
**Terminal 1 (Backend):**
```bash
cd backend
..\venv\bin\python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

**Terminal 2 (Frontend):**
```bash
cd frontend
npm run dev
```

Open **`http://localhost:5173`** in your browser.

---

## ⚙️ Architecture & Features

```
Merchant Physical Standee
           │
           ├────────────────────────────┐
           ▼                            ▼
  [Visible QR Code]            [Invisible Bitplane Watermark]
  UPI URI: upi://pay?pa=...    HMAC-SHA256 Merchant Signature
           │                            │
           └──────────────┬─────────────┘
                          │
                          ▼
            ┌───────────────────────────┐
            │ Dual-Binding Provenance   │
            │ Engine (Integrity Check)  │
            └─────────────┬─────────────┘
                          │
            ┌─────────────┴─────────────┐
            ▼                           ▼
    [GENUINE VERIFIED]          [TAMPERING DETECTED]
    - Status: 96.6% Match       - Destination: thief_scam99@ybl
    - Payments Flow Normally    - Autonomous Payout Freeze
                                - Soundbox Hardware Fraud Spoken Alert
                                - NPCI Fraud Docket Filed
```

- **Zero-Chat Voice-First Experience:** Uses Sarvam AI (Saaras STT & Bulbul TTS) with Edge TTS fallback for spoken regional voice across Top 10 Indian Languages (Hindi, Marathi, Gujarati, Tamil, etc.).
- **Vercel Geist Design System:** Engineered, clean layout conforming strictly to `DESIGN.md`.
