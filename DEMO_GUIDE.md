# Paytm ResolveAI - Live Hackathon Presentation Guide
### Track 3: Autonomous AI Teammates
**Motto:** *"Don't tell merchants what to do. Do it for them."*

---

## 🚀 1-Click Startup Instructions

You can start the entire stack using either method:
* **Option A (Double-Click Batch):** Run `start_demo.bat`
* **Option B (PowerShell):** Run `.\start_demo.ps1`
* **Option C (Manual):**
  * Terminal 1: `cd backend && python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload`
  * Terminal 2: `cd frontend && npm run dev`

Open your browser at: **`http://localhost:5173`**  
Backend Swagger Docs: **`http://localhost:8000/docs`**

---

## 🎯 Live Stage Demo Cheat Sheet (5 Scenarios)

The login screen features a **1-Click Quick Selector** for all 5 scenarios. You can click any scenario to log in immediately with pre-loaded queries:

### Scenario 1: Ramesh Kirana Store (Instant Auto-Resolution)
* **Login:** `ramesh_kirana` / `paytm123` (or click *Ramesh Kirana Store*)
* **Issue:** ₹4,500 morning sales missing from bank account.
* **Pitch to Judges:**
  > *"When Ramesh checks his bank account, ₹4,500 is missing. Instead of giving him an FAQ link or opening an 18-hour support ticket, watch ResolveAI work in real-time."*
* **What Happens Live:**
  1. Click **"Ask AI"** on the prompt: *"My ₹4,500 payment from morning sales hasn't reached my bank account yet."*
  2. The **Pipeline Cards light up in real time**:
     - `Manager Agent` extracts intent and checks safety limit ($\le$ ₹25,000 threshold).
     - `SQL Investigator` detects batch `#B-402` held due to `NPCI_CLEARING_TIMEOUT`.
     - `Remediation Agent` re-routes the batch to the secondary IMPS rail.
     - `Verification Agent` confirms bank credit and retrieves **Bank UTR `#9021849182`**.
  3. Ramesh gets instant credit and a verified UTR receipt in under 5 seconds!

---

### Scenario 2: Sharmaji Electronics (Human-in-the-Loop Threshold Breach)
* **Login:** `sharma_electro` / `paytm123`
* **Issue:** High-value smart TV sale of ₹78,000 held under velocity limits.
* **Pitch to Judges:**
  > *"Judges always ask: Can an AI hallucinate money transfers? Here is our LangGraph Human-in-the-Loop safety guardrail."*
* **What Happens Live:**
  1. Click **"Ask AI"** on the ₹78,000 prompt.
  2. The agent verifies the ledger, discovers ₹78,000 exceeds the ₹25,000 autonomous threshold, and **pauses execution**.
  3. The right pane displays a highlighted **Supervisor Approval Card** (`LangGraph Checkpoint`).
  4. Click **"Approve Settlement"**.
  5. The agent immediately resumes, releases the hold, generates the UTR, and confirms the credit.

---

### Scenario 3: Chai Point Stall (Paytm Soundbox Speech Mismatch)
* **Login:** `chai_point` / `paytm123`
* **Issue:** Customer paid ₹60 for tea, but the Soundbox didn't speak.
* **Pitch to Judges:**
  > *"Soundbox is Paytm's signature hardware. When it fails to speak, merchants panic that the customer faked the payment."*
* **What Happens Live:**
  1. Click **"Ask AI"** on the Soundbox prompt.
  2. The agent checks the gateway $\to$ confirms transaction `PTM-33219` succeeded $\to$ detects Soundbox `SB-4402` had a temporary GSM disconnect.
  3. ResolveAI triggers an OTA chime, plays the chime audio, restores Soundbox to `ONLINE`, and reassures the merchant.

---

### Scenario 4: Verma Medical Hall (Duplicate UPI Reversal)
* **Login:** `verma_meds` / `paytm123`
* **Issue:** Customer claims they were debited twice for ₹1,200 medicine.
* **Pitch to Judges:**
  > *"Chargeback and duplicate debit anxiety leads to merchant friction. ResolveAI audits the NPCI clearing rail."*
* **What Happens Live:**
  1. Click **"Ask AI"** on the duplicate debit prompt.
  2. The agent queries transactions $\to$ finds 1 successful payment and 1 in `AUTO_REVERSAL_INITIATED`.
  3. Issues a definitive dispute-shield reference proving no chargeback risk exists.

---

### Scenario 5: Gupta Sweets & Snacks (Acquiring Rail Degradation Failover)
* **Login:** `gupta_sweets` / `paytm123`
* **Issue:** Multiple QR customer payments failing in the afternoon.
* **Pitch to Judges:**
  > *"ResolveAI is not just reactive—it is proactive. It detects bank gateway latency and auto-switches routes."*
* **What Happens Live:**
  1. Click **"Ask AI"** on the decline prompt.
  2. Detects 35% decline spike on HDFC acquiring rail.
  3. Automatically switches merchant acquiring traffic to the ICICI backup gateway.

---

## 🌐 Multilingual Demonstration (Top 10 Indian Languages)

To demonstrate ResolveAI's localized merchant experience to judges:
1. In the top navigation bar, click the **Language Selector** dropdown (`🌐 English`).
2. Switch to **मराठी (Marathi)**, **हिन्दी (Hindi)**, **ગુજરાતી (Gujarati)**, **বাংলা (Bengali)**, **தமிழ் (Tamil)**, **తెలుగు (Telugu)**, **ಕನ್ನಡ (Kannada)**, **മലയാളം (Malayalam)**, or **ਪੰਜਾਬੀ (Punjabi)**.
3. Observe:
   - The merchant chat greeting immediately adapts to the selected regional language.
   - The **"Ask AI"** scenario prompt displays natively in that language (e.g. in Marathi: *"माझ्या सकाळच्या विक्रीचे ₹4,500 अजूनही माझ्या बँक खात्यात जमा झाले नाहीत. कृपया तपासा."*).
   - Click **"Ask AI"**:
     - Background agent operations, SQL queries, and tool RPCs continue executing deterministically in **English** on the Operations Center (right pane).
     - The final Verification Agent output and audio broadcast text are presented to the merchant in **native Marathi/Hindi/chosen language** with the verified bank UTR receipt!

---

## 🧪 Comprehensive Verification Suite

Run the master diagnostic test at any time:
```powershell
python Test/test_master_suite.py
python Test/test_multilingual.py
```
This script executes:
1. `compileall` on backend source files (100% Python syntax verification)
2. Database schema, tables, and indices integrity check
3. All 5 agent scenarios end-to-end (diagnostics, tools, and UTR generation)
4. Fast API routes and authentication validation
5. Multilingual verification across all 10 Indian languages
6. Vite + Tailwind CSS production bundle build (`dist/`)
4. FastAPI REST and authentication endpoints
5. Production bundle check (`npm run build`)

