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
    log_filepath = log_dir_path / mode / ("%s-%d.log" % (mode, log_id))

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

        header = time.strftime("%Y-%m-%d %I:%M:%S %p %z\n")
        self.f.write(header)

        self.newline = True
        self.t0 = time.time()

    def write(self, s):

        dt = time.time() - self.t0

        for substr in s.splitlines(keepends=True):
            prefix = "[%s] " % ("%.6f" % dt).rjust(12) if self.newline else ""
            self.f.write(prefix + substr)
            self.newline = (substr[-1] == "\n")

    def close(self):
        self.f.write("\n")
        self.f.close()
