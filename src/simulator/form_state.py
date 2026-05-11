import json
import os

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "data")
FORM_FILE = os.path.join(DATA_DIR, "last_dosing_form.json")


def save_form(data: dict):
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(FORM_FILE, "w") as f:
        json.dump(data, f, indent=2)


def load_form() -> dict:
    if os.path.exists(FORM_FILE):
        with open(FORM_FILE) as f:
            return json.load(f)
    return {}
