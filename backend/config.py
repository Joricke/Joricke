"""Configuration management for Research Chat System."""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# --- LLM Configuration ---
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "anthropic").lower()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
ANTHROPIC_MODEL = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-20250514")
LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", "0.7"))
LLM_MAX_TOKENS = int(os.getenv("LLM_MAX_TOKENS", "1024"))

# --- Database Configuration ---
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./data/research_chat.db")

# --- Application Configuration ---
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8000"))

# --- Consent Notice ---
CONSENT_NOTICE = os.getenv(
    "CONSENT_NOTICE",
    "This chat is part of a research study. All messages are logged and may be "
    "analysed for educational research purposes. No personally identifiable "
    "information is stored — only your pseudonymised student ID. By continuing, "
    "you confirm that you have read the participant information sheet and consent "
    "to participate. If you have questions, contact the researcher."
)


def get_api_key() -> str:
    """Return the API key for the configured provider."""
    if LLM_PROVIDER == "openai":
        return OPENAI_API_KEY
    elif LLM_PROVIDER == "anthropic":
        return ANTHROPIC_API_KEY
    else:
        raise ValueError(f"Unknown LLM provider: {LLM_PROVIDER}")


def get_model() -> str:
    """Return the model name for the configured provider."""
    if LLM_PROVIDER == "openai":
        return OPENAI_MODEL
    elif LLM_PROVIDER == "anthropic":
        return ANTHROPIC_MODEL
    else:
        raise ValueError(f"Unknown LLM provider: {LLM_PROVIDER}")


def validate_config() -> dict:
    """Validate configuration and return status info."""
    api_key = get_api_key()
    return {
        "provider": LLM_PROVIDER,
        "model": get_model(),
        "api_key_configured": bool(api_key),
        "database_url": DATABASE_URL,
        "temperature": LLM_TEMPERATURE,
        "max_tokens": LLM_MAX_TOKENS,
    }
