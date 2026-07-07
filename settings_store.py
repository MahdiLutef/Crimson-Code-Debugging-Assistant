import json
import os

STORE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ui_settings.json")

DEFAULTS = {
    "theme_name": "Dark Crimson",
    "editor_font_size": 11,
    "source_wrap": False,
    "animations_enabled": True,
    "auto_scroll_output": True,
}


def load():
    if not os.path.exists(STORE_PATH):
        return dict(DEFAULTS)
    try:
        with open(STORE_PATH, "r") as f:
            data = json.load(f)
        merged = dict(DEFAULTS)
        merged.update(data)
        return merged
    except (json.JSONDecodeError, OSError):
        return dict(DEFAULTS)


def save(values):
    try:
        with open(STORE_PATH, "w") as f:
            json.dump(values, f, indent=2)
        return True
    except OSError:
        return False