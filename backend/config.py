import os
from dotenv import load_dotenv

# Load .env from backend directory first, then root
backend_env = os.path.join(os.path.dirname(__file__), ".env")
if os.path.exists(backend_env):
    load_dotenv(dotenv_path=backend_env)
load_dotenv()

# LLM Providers Configuration
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "sarvam").lower()

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL = os.getenv("GROQ_MODEL", "qwen/qwen3.8-27b")

SARVAM_API_KEY = os.getenv("SARVAM_API_KEY", "")
SARVAM_API_URL = os.getenv("SARVAM_API_URL", "https://api.sarvam.ai/v1")
SARVAM_MODEL = os.getenv("SARVAM_MODEL", "sarvam-105b-conversations")
SARVAM_TTS_MODEL = os.getenv("SARVAM_TTS_MODEL", "bulbul:v3")
SARVAM_STT_MODEL = os.getenv("SARVAM_STT_MODEL", "saaras:v3")

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

class DirectSarvamClient:
    """
    Lightweight zero-dependency direct HTTP client for Sarvam AI.
    Used when the official `sarvamai` SDK is not installed in the active Python environment.
    """
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.speech_to_text = self._STT(api_key)
        self.text_to_speech = self._TTS(api_key)

    class _STT:
        def __init__(self, api_key: str):
            self.api_key = api_key

        def transcribe(self, file, model: str = "saaras:v3", language_code: str = "hi-IN"):
            import requests
            filename, audio_bytes, content_type = file
            files = {
                "file": (filename, audio_bytes, content_type or "audio/webm")
            }
            data = {
                "model": model,
                "language_code": language_code
            }
            headers = {
                "api-subscription-key": self.api_key
            }
            resp = requests.post(
                "https://api.sarvam.ai/speech-to-text",
                headers=headers,
                files=files,
                data=data,
                timeout=30
            )
            if resp.status_code != 200:
                raise Exception(f"Sarvam STT HTTP {resp.status_code}: {resp.text}")
            payload = resp.json()
            class STTResult:
                def __init__(self, t):
                    self.transcript = t
            return STTResult(payload.get("transcript", ""))

    class _TTS:
        def __init__(self, api_key: str):
            self.api_key = api_key

        def convert(self, text: str, language_code: str = "hi-IN", speaker: str = "aditya", model: str = "bulbul:v3"):
            import requests
            headers = {
                "api-subscription-key": self.api_key,
                "Content-Type": "application/json"
            }
            payload = {
                "inputs": [text],
                "target_language_code": language_code,
                "speaker": speaker,
                "model": model
            }
            resp = requests.post(
                "https://api.sarvam.ai/text-to-speech",
                headers=headers,
                json=payload,
                timeout=30
            )
            if resp.status_code != 200:
                raise Exception(f"Sarvam TTS HTTP {resp.status_code}: {resp.text}")
            data = resp.json()
            class TTSResult:
                def __init__(self, a):
                    self.audios = a
            return TTSResult(data.get("audios", []))

def get_sarvam_client():
    """Initializes and returns Sarvam AI client (via official SDK or direct HTTP client)."""
    if not SARVAM_API_KEY:
        return None
    try:
        from sarvamai import SarvamAI
        return SarvamAI(api_subscription_key=SARVAM_API_KEY)
    except Exception:
        # Seamlessly fallback to DirectSarvamClient using requests
        return DirectSarvamClient(api_key=SARVAM_API_KEY)

# Central LLM Factory: Swap providers simply by changing LLM_PROVIDER in .env
def get_llm():
    """
    Standard LangChain BaseChatModel factory.
    Swap providers (groq, sarvam, openai, azure, bedrock, gemini) seamlessly
    by setting LLM_PROVIDER in .env or updating this single function.
    """
    provider = LLM_PROVIDER.lower()

    try:
        if provider == "groq" and GROQ_API_KEY:
            from langchain_groq import ChatGroq
            return ChatGroq(
                api_key=GROQ_API_KEY,
                model_name=GROQ_MODEL,
                temperature=0.1
            )

        elif provider == "sarvam" and SARVAM_API_KEY:
            # Sarvam AI exposes OpenAI-compatible chat completion endpoints
            try:
                from langchain_openai import ChatOpenAI
                return ChatOpenAI(
                    api_key=SARVAM_API_KEY,
                    base_url=SARVAM_API_URL,
                    model_name=SARVAM_MODEL,
                    default_headers={"api-subscription-key": SARVAM_API_KEY},
                    temperature=0.1
                )
            except ImportError:
                if GROQ_API_KEY:
                    from langchain_groq import ChatGroq
                    return ChatGroq(
                        api_key=GROQ_API_KEY,
                        model_name=GROQ_MODEL,
                        temperature=0.1
                    )

        elif provider == "openai" and OPENAI_API_KEY:
            from langchain_openai import ChatOpenAI
            return ChatOpenAI(
                api_key=OPENAI_API_KEY,
                model_name=OPENAI_MODEL,
                temperature=0.1
            )

        elif provider == "azure":
            from langchain_openai import AzureChatOpenAI
            return AzureChatOpenAI(
                azure_deployment=os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME"),
                api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-15-preview"),
                temperature=0.1
            )

        elif provider == "bedrock":
            from langchain_aws import ChatBedrock
            return ChatBedrock(
                model_id=os.getenv("BEDROCK_MODEL_ID", "anthropic.claude-3-haiku-20240307-v1:0"),
                temperature=0.1
            )

        elif provider == "gemini":
            from langchain_google_genai import ChatGoogleGenerativeAI
            return ChatGoogleGenerativeAI(
                model=os.getenv("GEMINI_MODEL", "gemini-1.5-flash"),
                temperature=0.1
            )

    except Exception as e:
        print(f"[LLM_FACTORY] Warning initializing {provider}: {e}. Proceeding with deterministic fallback.")

    return None

# Fallback & Thresholds
AUTO_RESOLUTION_THRESHOLD = float(os.getenv("AUTO_RESOLUTION_THRESHOLD", "25000.0")) # Up to ₹25,000
DEMO_SIMULATION_MODE = os.getenv("DEMO_SIMULATION_MODE", "false").lower() == "true"

# Server Host & Port
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8000"))

