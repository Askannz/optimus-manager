import sys
import os
from pathlib import Path
import time
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


def print_timestamp_separator():

    time_str = time.strftime("%Y-%m-%d %I:%M:%S %p %z")
    print("\n" + time_str + envs.LOGGING_SEPARATOR_SUFFIX + "\n")

def crop_logs():

    log_files_list = [envs.BOOT_SETUP_LOGFILE_NAME,
                      envs.GPU_SETUP_LOGFILE_NAME,
                      envs.PRIME_SETUP_LOGFILE_NAME]

    for filename in log_files_list:
        filepath = os.path.join(envs.LOG_DIR_PATH, filename)
        _crop_log_file(filepath)

def _crop_log_file(filepath):

    try:
        with open(filepath, "r") as f:
            content = f.read()
    except FileNotFoundError:
        return

    lines_list = content.splitlines()

    if len(lines_list) > envs.LOG_MAX_SIZE:
        print("Log file %s has more than %d lines, cropping it to %d"
              % (filepath, envs.LOG_MAX_SIZE, envs.LOG_CROPPED_SIZE))

        lines_list = lines_list[-envs.LOG_CROPPED_SIZE:]

        with open(filepath, "w") as f:
            f.write("\n".join(lines_list))
