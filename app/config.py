import os
from dotenv import load_dotenv

load_dotenv()

LLM_PROVIDER = os.getenv("LLM_PROVIDER", "gemini")  # "gemini" or "openai"
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")

MIN_PARTICIPANTS = int(os.getenv("MIN_PARTICIPANTS", "2"))
MAX_PARTICIPANTS = int(os.getenv("MAX_PARTICIPANTS", "6"))

# AI gating
AI_COOLDOWN_SECONDS = 12
AI_NO_INTERRUPT_WINDOW = 3  # seconds after last user message
SILENCE_THRESHOLD = 6  # seconds of silence before URGENT
