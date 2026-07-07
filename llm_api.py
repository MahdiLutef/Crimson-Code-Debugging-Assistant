import requests
import config


def resolve_endpoint():
    if config.provider == "custom":
        return config.base_url
    return config.PROVIDER_ENDPOINTS.get(config.provider, "")


def ask(prompt):
    if not config.api_key:
        return "no api_key set in .env"

    if not config.model:
        return "no model set in .env"

    endpoint = resolve_endpoint()
    if not endpoint:
        return f"no endpoint configured for provider: {config.provider}"

    if config.provider == "anthropic":
        return ask_anthropic(endpoint, prompt)

    if config.provider in config.OPENAI_COMPATIBLE_PROVIDERS:
        return ask_openai_compatible(endpoint, prompt)

    return f"unsupported provider: {config.provider}"


def ask_openai_compatible(endpoint, prompt):
    headers = {
        "Authorization": f"Bearer {config.api_key}",
        "Content-Type": "application/json"
    }

    body = {
        "model": config.model,
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.3
    }

    try:
        res = requests.post(endpoint, headers=headers, json=body, timeout=config.api_timeout)
        res.raise_for_status()
        data = res.json()
        return data["choices"][0]["message"]["content"]
    except requests.exceptions.Timeout:
        return f"{config.provider} request timed out after {config.api_timeout}s"
    except requests.exceptions.HTTPError:
        return f"{config.provider} rejected the request: {res.status_code} {res.text}"
    except requests.exceptions.RequestException as e:
        return f"{config.provider} request failed: {e}"
    except (KeyError, IndexError, ValueError):
        return f"{config.provider} returned an unexpected response format"


def ask_anthropic(endpoint, prompt):
    headers = {
        "x-api-key": config.api_key,
        "anthropic-version": "2023-06-01",
        "Content-Type": "application/json"
    }

    body = {
        "model": config.model,
        "max_tokens": 1024,
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.3
    }

    try:
        res = requests.post(endpoint, headers=headers, json=body, timeout=config.api_timeout)
        res.raise_for_status()
        data = res.json()
        return data["content"][0]["text"]
    except requests.exceptions.Timeout:
        return f"anthropic request timed out after {config.api_timeout}s"
    except requests.exceptions.HTTPError:
        return f"anthropic rejected the request: {res.status_code} {res.text}"
    except requests.exceptions.RequestException as e:
        return f"anthropic request failed: {e}"
    except (KeyError, IndexError, ValueError):
        return "anthropic returned an unexpected response format"
