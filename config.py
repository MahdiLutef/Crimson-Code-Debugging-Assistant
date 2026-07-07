import os
from dotenv import load_dotenv

load_dotenv()

mode = os.getenv("MODE", "api").lower()

provider = os.getenv("PROVIDER", "groq").lower()
api_key = os.getenv("API_KEY", "")
model = os.getenv("MODEL", "")
base_url = os.getenv("BASE_URL", "")
api_timeout = int(os.getenv("API_TIMEOUT", "60"))

DEFAULT_MODELS = {
    "groq": "qwen/qwen3-32b",
    "openai": "gpt-4o-mini",
    "anthropic": "claude-sonnet-5",
    "gemini": "gemini-2.5-flash",
}

if not model:
    model = DEFAULT_MODELS.get(provider, "")

PROVIDER_ENDPOINTS = {
    "groq": "https://api.groq.com/openai/v1/chat/completions",
    "openai": "https://api.openai.com/v1/chat/completions",
    "gemini": "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions",
    "anthropic": "https://api.anthropic.com/v1/messages",
}

OPENAI_COMPATIBLE_PROVIDERS = ("groq", "openai", "gemini", "custom")

llm_path = os.getenv("LLM_PATH", "")
llm_ctx = int(os.getenv("LLM_CTX", "8192"))
llm_threads = int(os.getenv("LLM_THREADS", "4"))
