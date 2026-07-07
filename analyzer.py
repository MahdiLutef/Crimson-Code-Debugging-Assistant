import llm_api
import llm_local

template = """You are a debugging assistant looking at a piece of code and, if given, the error it throws.

Find the bug, explain what is wrong and why, then give a corrected version of the code.

Code:
{code}

Error:
{error}

Reply with three sections: What's wrong, Why it happens, Fixed code.
"""


def check(code, error, mode):
    if not code.strip():
        return "paste some code first"

    err = error.strip() if error.strip() else "no error given, just review the code for bugs"
    prompt = template.format(code=code.strip(), error=err)

    if mode == "local":
        return llm_local.ask(prompt)
    return llm_api.ask(prompt)