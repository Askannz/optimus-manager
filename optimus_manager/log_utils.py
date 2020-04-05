import sys
import os
from pathlib import Path
import logging
from . import envs


def set_logger_config(log_type, log_id):

    log_dir_path = Path(envs.LOG_DIR_PATH)
    log_filepath = log_dir_path / log_type / ("%s-%s.log" % (log_type, log_id))

    if not log_filepath.parent.exists():
        os.makedirs(log_filepath.parent)
        os.chmod(log_filepath.parent, 0o777)

    logging.basicConfig(
        level=logging.INFO,
        format="[%(relativeCreated)d] %(levelname)s: %(message)s",
        handlers=[
            logging.StreamHandler(stream=sys.stdout),
            logging.FileHandler(filename=log_filepath)
        ]
    )

    try:
        os.chmod(log_filepath, 0o777)
    except PermissionError:
        pass


def get_logger():
    return logging.getLogger()
