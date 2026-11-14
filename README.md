# ResolveAI - Autonomous Merchant Operations Teammate

> **Paytm India AI Hackathon (Track 3: Autonomous AI Teammates)**  
> An autonomous multi-agent teammate that diagnoses, investigates, and resolves merchant payment and settlement incidents in real time without FAQ deflection.

---

## Quick Start (Setup in 3 Steps)

### 1. Prerequisites
- **Python 3.10+**
- **Node.js 18+**

### 2. Backend Setup
```bash
# Install Python dependencies
pip install -r requirements.txt

# Create your .env file
copy .env.example backend\.env
```
*(Optional: Open `backend/.env` and add your `GROQ_API_KEY` or `OPENAI_API_KEY`. If no key is provided, the built-in Dynamic Context Engine runs automatically out of the box with zero external dependencies).*

### 3. Frontend Setup
```bash
cd frontend
npm install
cd ..
```

---

## Running the Application

### Option A: 1-Click Launch (Windows)
Double-click `start_demo.bat` or run:
```bash
.\start_demo.bat
```

### Option B: Manual Launch

**Terminal 1 (Backend):**
```bash
cd backend
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

**Terminal 2 (Frontend):**
```bash
cd frontend
npm run dev
```

Open your browser at **`http://localhost:5173`**.

---

## How It Works

ResolveAI functions like a real operational support engineer embedded directly in the Paytm merchant ecosystem:

```
Merchant Query (Text or Regional Voice)
                  │
                  ▼
┌─────────────────────────────────────────────────────────────┐
│ 01. Incident Manager Agent                                   │
│     - Identifies merchant profile and business type         │
│     - Validates ₹25,000 autonomous safety limit              │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│ 02. SQL & Rail Investigator Agent                           │
│     - Inspects live transaction ledger & settlement batches │
│     - Audits Soundbox GSM/network telemetry                 │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│ 03. Remediation Agent                                       │
│     - Re-routes stuck settlement batches (IMPS Secondary)   │
│     - Triggers OTA audio chime broadcasts for Soundbox      │
│     - Fails over acquiring traffic to backup gateways       │
│     - Pauses for 1-click supervisor approval if > ₹25,000   │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│ 04. Verification & Audit Agent                              │
│     - Validates core banking UTR reference                  │
│     - Synthesizes clean plain-text response in merchant's   │
│       language (Hindi, Marathi, Gujarati, English, etc.)    │
│     - Generates Edge TTS neural audio voiceover             │
└─────────────────────────────────────────────────────────────┘
```

---

## Key Features

- **Generic Chatbot & Dynamic Ledger Lookup:** Ask any question (e.g. *"What is the order ID of my payment?"*, *"What is my bank account?"*, *"How much battery is in Soundbox?"*). ResolveAI answers factually from live SQLite records without triggering unneeded actions or displaying irrelevant cards.
- **Top 10 Indian Languages:** Native support for English, Hindi, Marathi, Gujarati, Bengali, Tamil, Telugu, Kannada, Malayalam, and Punjabi.
- **Natural Neural Audio (Edge TTS):** Click the `Listen Voice` button under any response to hear the answer in the selected regional language.
- **Human-in-the-Loop Safety Boundary:** Autonomous auto-fix is capped at **₹25,000**. Transactions above this threshold pause execution and require 1-click supervisor authorization.
- **Zero FAQ Deflection:** Instead of giving merchants static help links, ResolveAI actually diagnoses database records and takes API action.

---

## Demo Scenarios

| Merchant | Scenario | Autonomous Action |
| :--- | :--- | :--- |
| **Ramesh Kirana Store** (`M-101`) | Morning sales ₹4,500 stuck | Re-routes batch via IMPS & generates bank UTR |
| **Sharma Electronics** (`M-102`) | High-value ₹78,000 Smart TV sale | Pauses for 1-click supervisor override |
| **Chai Point Stall** (`M-103`) | Soundbox silent on ₹60 tea payment | OTA audio chime broadcast (`SB-4402`) |
| **Verma Meds** (`M-104`) | Customer charged twice for ₹1,200 | Verifies NPCI auto-reversal reference |
| **Gupta Sweets** (`M-105`) | Multiple customer QR payments failing | Switches route to ICICI backup gateway |

---

## Project Structure

```
Paytm_Hackathon/
├── backend/
│   ├── main.py              # FastAPI server entry point
│   ├── routes.py            # SSE stream and approval endpoints
│   ├── agent_engine.py      # Multi-agent orchestrator & synthesizer
│   ├── tools.py             # Idempotent remediation tools (IMPS, Chime, Reversal)
│   ├── database.py          # SQLite zero-config ledger and telemetry
│   └── config.py            # Environment and LLM provider loader
├── frontend/
│   ├── src/
│   │   ├── App.jsx          # Main application container
│   │   ├── MerchantChatPane.jsx # Chat pane with Edge TTS voice
│   │   ├── OpsCenterPane.jsx    # Real-time multi-agent execution visualizer
│   │   └── languages.js     # Top 10 Indian languages configuration
├── requirements.txt         # Python dependencies
├── start_demo.bat           # 1-click Windows startup script
└── README.md                # Project documentation
```
