import os
from pathlib import Path
import json
from .envs import STATE_FILE_PATH

def make_startup_id():
    return 1337  # Placeholder

def make_attempt_id():
    return 42  # Placeholder


def write_state(state):

    filepath = Path(STATE_FILE_PATH)

    os.makedirs(filepath.parent, exist_ok=True)

    with open(filepath, "w") as f:
        json.dump(state, f)

def load_state():
    try:
        with open(STATE_FILE_PATH, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return None
