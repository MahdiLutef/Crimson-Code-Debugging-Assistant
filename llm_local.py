import config

model = None
load_error = None


def load():
    global model, load_error
    if model is not None:
        return model

    if not config.llm_path:
        return None

    try:
        from llama_cpp import Llama
        model = Llama(
            model_path=config.llm_path,
            n_ctx=config.llm_ctx,
            n_threads=config.llm_threads,
            verbose=False
        )
        return model
    except Exception as e:
        load_error = str(e)
        return None


def ask(prompt):
    m = load()
    if m is None:
        if load_error:
            return f"could not load local model: {load_error}"
        return "no llm_path set in .env"

    try:
        out = m.create_chat_completion(
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=1024
        )
        return out["choices"][0]["message"]["content"]
    except Exception as e:
        return f"local model failed: {e}"