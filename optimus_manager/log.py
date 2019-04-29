import os
import time
from pathlib import Path
import optimus_manager.envs as envs


def setup_logfiles():

    prime_logfile_path = os.path.join(envs.LOG_DIR_PATH, envs.PRIME_SETUP_LOGFILE_NAME)

    if not os.path.isfile(prime_logfile_path):
        Path(prime_logfile_path).touch(mode=0o666)


def print_timestamp_separator():

    time_str = time.strftime("%Y-%m-%d %I:%M:%S %p %z ")
    print("\n" + time_str + ("=" * 20) + "\n")
