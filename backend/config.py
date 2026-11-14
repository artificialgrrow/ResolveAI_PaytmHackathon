import os
from dotenv import load_dotenv

load_dotenv()

# LLM Providers Configuration
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "groq").lower()

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

SARVAM_API_KEY = os.getenv("SARVAM_API_KEY", "")
SARVAM_API_URL = os.getenv("SARVAM_API_URL", "https://api.sarvam.ai/v1")
SARVAM_MODEL = os.getenv("SARVAM_MODEL", "sarvam-2b")

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

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
            from langchain_openai import ChatOpenAI
            return ChatOpenAI(
                api_key=SARVAM_API_KEY,
                base_url=SARVAM_API_URL,
                model_name=SARVAM_MODEL,
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

