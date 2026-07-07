import os
from dotenv import load_dotenv

load_dotenv()

mode = os.getenv("MODE", "api").lower()
groq_key = os.getenv("GROQ_KEY", "")
groq_model = os.getenv("GROQ_MODEL", "qwen/qwen3-32b")
llm_path = os.getenv("LLM_PATH", "")
llm_ctx = int(os.getenv("LLM_CTX", "8192"))
llm_threads = int(os.getenv("LLM_THREADS", "4"))