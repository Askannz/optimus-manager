import json
import os
import shutil
import time
from pathlib import Path
from . import envs
from .log_utils import get_logger


class VarError(Exception):
    pass


def read_temp_conf_path_var():
    filepath = Path(envs.TEMP_CONFIG_PATH_VAR_PATH)

    try:
        with open(filepath, 'r') as readfile:
            return readfile.read().strip()

    except FileNotFoundError as error:
        raise VarError("File doesn't exist: %s" % str(filepath)) from error

    except IOError as error:
        raise VarError("Unable to read: %s" % str(filepath)) from error


def write_temp_conf_path_var(path):
    filepath = Path(envs.TEMP_CONFIG_PATH_VAR_PATH)
    os.makedirs(filepath.parent, exist_ok=True)

    try:
        with open(envs.TEMP_CONFIG_PATH_VAR_PATH, 'w') as writefile:
            writefile.write(path)

    except IOError as error:
        raise VarError("Unable to write to: %s" % envs.TEMP_CONFIG_PATH_VAR_PATH) from error


def remove_temp_conf_path_var():
    try:
        os.remove(envs.TEMP_CONFIG_PATH_VAR_PATH)

    except FileNotFoundError:
        pass


def write_acpi_call_strings(call_strings_list):
    filepath = Path(envs.ACPI_CALL_STRING_VAR_PATH)
    os.makedirs(filepath.parent, exist_ok=True)

    try:
        with open(filepath, 'w') as writefile:
            json.dump(call_strings_list, writefile)

    except IOError as error:
        raise VarError("Unable to write to: %s" % str(filepath)) from error


def read_acpi_call_strings():
    filepath = Path(envs.ACPI_CALL_STRING_VAR_PATH)

    try:
        with open(filepath, 'r') as readfile:
            return json.load(readfile)

    except FileNotFoundError as error:
        raise VarError("File doesn't exist: %s" % str(filepath)) from error

    except (IOError, json.decoder.JSONDecodeError) as error:
        raise VarError("Unable to read: %s" % str(filepath)) from error


def write_last_acpi_call_state(state):
    filepath = Path(envs.LAST_ACPI_CALL_STATE_VAR)
    os.makedirs(filepath.parent, exist_ok=True)

    try:
        with open(filepath, 'w') as writefile:
            writefile.write(state)

    except IOError as error:
        raise VarError("Unable to write to: %s" % str(filepath)) from error


def read_last_acpi_call_state():
    filepath = Path(envs.LAST_ACPI_CALL_STATE_VAR)

    try:
        with open(filepath, 'r') as readfile:
            return readfile.read().strip()

    except FileNotFoundError as error:
        raise VarError("File doesn't exist: %s" % str(filepath)) from error

    except IOError as error:
        raise VarError("Unable to read: %s" % str(filepath)) from error


def make_daemon_run_id():
    return time.strftime("%Y%m%dT%H%M%S")


def make_switch_id():
    return time.strftime("%Y%m%dT%H%M%S")


def write_daemon_run_id(daemon_run_id):
    filepath = Path(envs.CURRENT_DAEMON_RUN_ID)
    os.makedirs(filepath.parent, exist_ok=True)

    with open(filepath, "w") as writefile:
        writefile.write(str(daemon_run_id))


def load_daemon_run_id():
    try:
        with open(envs.CURRENT_DAEMON_RUN_ID, "r") as readfile:
            return readfile.read().strip()

    except FileNotFoundError:
        return None


def write_state(state):
    logger = get_logger()
    logger.info("Writing state: %s", str(state))
    filepath = Path(envs.STATE_FILE_PATH)
    os.makedirs(filepath.parent, exist_ok=True)

    with open(filepath, "w") as writefile:
        json.dump(state, writefile)

    try:
        os.chmod(filepath, mode=0o666)

    except PermissionError:
        pass


def load_state():
    try:
        with open(envs.STATE_FILE_PATH, "r") as readfile:
            return json.load(readfile)

    except FileNotFoundError:
        return None


def cleanup_tmp_vars():
    shutil.rmtree(envs.TMP_VARS_FOLDER_PATH, ignore_errors=True)
