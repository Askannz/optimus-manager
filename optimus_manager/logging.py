import sys
import os
from pathlib import Path
import io
import time
import contextlib
from . import envs

@contextlib.contextmanager
def logging(mode, log_id):

    log_dir_path = Path(envs.LOG_DIR_PATH)
    log_filepath = log_dir_path / mode / (str(log_id) + ".txt")

    os.makedirs(log_filepath.parent, exist_ok=True)

    f = TimeStampedFile(log_filepath)

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


class TimeStampedFile(io.TextIOBase):

    def __init__(self, path):
        io.TextIOBase.__init__(self)
        self.f = open(path, "a")

    def write(self, s):

        prefix = time.strftime("%Y-%m-%d %I:%M:%S %p %z: ") \
            if s != "\n" else ""
        self.f.write(prefix + s)

    def close(self):
        self.f.close()
