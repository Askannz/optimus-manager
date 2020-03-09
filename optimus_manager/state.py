import json
from .envs import STATE_FILE_PATH


def make_attempt_id():
    return 42  # Placeholder


def write_state(state):
    with open(STATE_FILE_PATH, "w") as f:
        json.dump(state, f)

def load_state():
    try:
        with open(STATE_FILE_PATH, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return None
