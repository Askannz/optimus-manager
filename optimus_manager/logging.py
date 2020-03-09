import sys
import os
from pathlib import Path
import contextlib
from . import envs

@contextlib.contextmanager
def logging(mode, log_id):

    log_dir_path = Path(envs.LOG_DIR_PATH)
    log_filepath = log_dir_path / mode / (str(log_id) + ".txt")

    os.makedirs(log_filepath.parent, exist_ok=True)

    f = open(log_filepath, "a")

    old_stdout = sys.stdout
    old_stderr = sys.stderr

    sys.stdout = f
    sys.stderr = f

    try:
        yield
    finally:
        sys.stdout = old_stdout
        sys.stderr = old_stderr
        f.close()
