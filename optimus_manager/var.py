import time
import os
import shutil
from pathlib import Path
import json
from . import envs
from .log_utils import get_logger


class VarError(Exception):
    pass


def read_temp_conf_path_var():

    filepath = Path(envs.TEMP_CONFIG_PATH_VAR_PATH)

    try:
        with open(filepath, 'r') as f:
            return f.read().strip()
    except FileNotFoundError:
        raise VarError("File %s not found." % str(filepath))
    except IOError:
        raise VarError("Cannot open or read %s" % str(filepath))

def write_temp_conf_path_var(path):

    filepath = Path(envs.TEMP_CONFIG_PATH_VAR_PATH)

    os.makedirs(filepath.parent, exist_ok=True)

    try:
        with open(envs.TEMP_CONFIG_PATH_VAR_PATH, 'w') as f:
            f.write(path)
    except IOError:
        raise VarError("Cannot open or write to %s" % envs.TEMP_CONFIG_PATH_VAR_PATH)

def remove_temp_conf_path_var():

    try:
        os.remove(envs.TEMP_CONFIG_PATH_VAR_PATH)
    except FileNotFoundError:
        pass

def write_acpi_call_strings(call_strings_list):

    filepath = Path(envs.ACPI_CALL_STRING_VAR_PATH)

    os.makedirs(filepath.parent, exist_ok=True)

    try:
        with open(filepath, 'w') as f:
            json.dump(call_strings_list, f)
    except IOError:
        raise VarError("Cannot open or write to %s" % str(filepath))

def read_acpi_call_strings():

    filepath = Path(envs.ACPI_CALL_STRING_VAR_PATH)

    try:
        with open(filepath, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        raise VarError("File %s not found." % str(filepath))
    except (IOError, json.decoder.JSONDecodeError):
        raise VarError("Cannot open or read %s" % str(filepath))

def write_last_acpi_call_state(state):

    filepath = Path(envs.LAST_ACPI_CALL_STATE_VAR)

    os.makedirs(filepath.parent, exist_ok=True)

    try:
        with open(filepath, 'w') as f:
            f.write(state)
    except IOError:
        raise VarError("Cannot open or write to %s" % str(filepath))

def read_last_acpi_call_state():

    filepath = Path(envs.LAST_ACPI_CALL_STATE_VAR)

    try:
        with open(filepath, 'r') as f:
            return f.read().strip()
    except FileNotFoundError:
        raise VarError("File %s not found." % str(filepath))
    except IOError:
        raise VarError("Cannot open or read %s" % str(filepath))


def make_daemon_run_id():
    return time.strftime("%Y%m%dT%H%M%S")

def make_switch_id():
    return time.strftime("%Y%m%dT%H%M%S")


def write_daemon_run_id(daemon_run_id):

    filepath = Path(envs.CURRENT_DAEMON_RUN_ID)

    os.makedirs(filepath.parent, exist_ok=True)

    with open(filepath, "w") as f:
        f.write(str(daemon_run_id))


def load_daemon_run_id():
    try:
        with open(envs.CURRENT_DAEMON_RUN_ID, "r") as f:
            return f.read().strip()
    except FileNotFoundError:
        return None


def write_state(state):

    logger = get_logger()

    logger.info("Writing state %s", str(state))

    filepath = Path(envs.STATE_FILE_PATH)

    os.makedirs(filepath.parent, exist_ok=True)

    with open(filepath, "w") as f:
        json.dump(state, f)

    try:
        os.chmod(filepath, mode=0o666)
    except PermissionError:
        pass

def load_state():
    try:
        with open(envs.STATE_FILE_PATH, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return None


def cleanup_tmp_vars():
    shutil.rmtree(envs.TMP_VARS_FOLDER_PATH, ignore_errors=True)
