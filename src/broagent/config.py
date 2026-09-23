import os
from dotenv import load_dotenv

load_dotenv()

PROVIDER = os.getenv("BROAGENT_PROVIDER", "anthropic").strip().lower()

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
ANTHROPIC_MODEL = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-5")

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_BASE_URL = os.getenv("GROQ_BASE_URL", "https://api.groq.com/openai/v1")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

PROFILE_DIR = os.getenv("BROAGENT_PROFILE_DIR", "./profile")
START_URL = os.getenv("BROAGENT_START_URL", "about:blank")
MAX_STEPS = int(os.getenv("BROAGENT_MAX_STEPS", "30"))
MAX_TOKENS = int(os.getenv("BROAGENT_MAX_TOKENS", "2048"))


def active_model_name() -> str:
    return ANTHROPIC_MODEL if PROVIDER == "anthropic" else GROQ_MODEL