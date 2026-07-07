import requests
import config

url = "https://api.groq.com/openai/v1/chat/completions"


def ask(prompt):
    if not config.groq_key:
        return "no groq_key set in .env"

    headers = {
        "Authorization": f"Bearer {config.groq_key}",
        "Content-Type": "application/json"
    }

    body = {
        "model": config.groq_model,
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.3
    }

    try:
        res = requests.post(url, headers=headers, json=body, timeout=60)
        res.raise_for_status()
        data = res.json()
        return data["choices"][0]["message"]["content"]
    except requests.exceptions.HTTPError:
        return f"groq rejected the request: {res.status_code} {res.text}"
    except Exception as e:
        return f"groq request failed: {e}"