Crimson CDA

Paste code, paste the error, hit check. It sends both to an LLM (Groq API or a local gguf) and gets back what's wrong, why, and a fix.

Setup

pip install -r requirements.txt

Copy .env.example to .env and fill it in.

MODE picks the default tab (api or local), you can still flip it in the GUI.
GROQ_KEY is your Groq API key.
GROQ_MODEL defaults to qwen/qwen3-32b since Groq doesn't host a model literally named qwen3-coder right now. Swap this if that changes.
LLM_PATH is the path to a local gguf file, loaded through llama-cpp-python. Leave blank if you're not using local mode.

Run

python main.py

Files

main.py - starts the app
gui.py - the crimson/root themed tkinter interface
config.py - reads .env
analyzer.py - builds the prompt and picks local vs api
llm_api.py - Groq calls
llm_local.py - local gguf calls through llama_cpp