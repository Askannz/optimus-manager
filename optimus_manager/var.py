import os
from pathlib import Path
import json
from . import envs
from .kernel_parameters import get_kernel_parameters


class VarError(Exception):
    pass


def read_startup_mode():

    try:
        with open(envs.STARTUP_MODE_VAR_PATH, 'r') as f:
            content = f.read().strip()

            if content in ["intel", "nvidia", "hybrid", "ac_auto"]:
                mode = content
            else:
                raise VarError("Invalid value : %s" % content)
    except IOError:
        raise VarError("Cannot open or read %s" % envs.STARTUP_MODE_VAR_PATH)

    return mode


def write_startup_mode(mode):

    assert mode in ["intel", "nvidia", "hybrid", "ac_auto"]

    filepath = Path(envs.STARTUP_MODE_VAR_PATH)

    os.makedirs(filepath.parent, exist_ok=True)

    try:
        with open(filepath, 'w') as f:
            f.write(mode)
    except IOError:
        raise VarError("Cannot open or write to %s" % str(filepath))


def remove_startup_mode_var():

    try:
        os.remove(envs.STARTUP_MODE_VAR_PATH)
    except FileNotFoundError:
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

def remove_last_acpi_call_state():

    print("Removing %s (if present)" % envs.LAST_ACPI_CALL_STATE_VAR)

    try:
        os.remove(envs.LAST_ACPI_CALL_STATE_VAR)
    except FileNotFoundError:
        pass

def get_startup_mode():

    kernel_parameters = get_kernel_parameters()

    if kernel_parameters["startup_mode"] is None:
        try:
            startup_mode = read_startup_mode()
        except VarError as e:
            print("Cannot read startup mode : %s.\nUsing default startup mode %s instead." % (str(e), envs.DEFAULT_STARTUP_MODE))
            startup_mode = envs.DEFAULT_STARTUP_MODE

    else:
        print("Startup kernel parameter found : %s" % kernel_parameters["startup_mode"])
        startup_mode = kernel_parameters["startup_mode"]

    return startup_mode


def make_daemon_run_id():

    try:
        with open(envs.DAEMON_RUN_ID_GENERATOR_FILE_PATH, 'r') as f:
            new_id = int(f.read().strip())
    except (FileNotFoundError, ValueError):
        new_id = 0

    with open(envs.DAEMON_RUN_ID_GENERATOR_FILE_PATH, 'w') as f:
        f.write(str(new_id + 1))

    return new_id


def make_switch_id():

    try:
        with open(envs.SWITCH_ID_GENERATOR_FILE_PATH, 'r') as f:
            new_id = int(f.read().strip())
    except (FileNotFoundError, ValueError):
        new_id = 0

    with open(envs.SWITCH_ID_GENERATOR_FILE_PATH, 'w') as f:
        f.write(str(new_id + 1))

    return new_id


def write_daemon_run_id(daemon_run_id):

    filepath = Path(envs.CURRENT_DAEMON_RUN_ID)

    os.makedirs(filepath.parent, exist_ok=True)

    with open(filepath, "w") as f:
        f.write(str(daemon_run_id))


def load_daemon_run_id():
    with open(envs.CURRENT_DAEMON_RUN_ID, "r") as f:
        return int(f.read().strip())


def write_state(state):

    filepath = Path(envs.STATE_FILE_PATH)

    os.makedirs(filepath.parent, exist_ok=True)

    with open(filepath, "w") as f:
        json.dump(state, f)

def load_state():
    try:
        with open(envs.STATE_FILE_PATH, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return None
