import os
import json
import optimus_manager.envs as envs


class VarError(Exception):
    pass


def read_requested_mode():

    try:
        with open(envs.REQUESTED_MODE_VAR_PATH, 'r') as f:
            content = f.read()

            if len(content) > 0 and content[-1] == "\n":
                content = content[:-1]

            if content in ["intel", "nvidia", "hybrid"]:
                mode = content
            else:
                raise VarError("Invalid mode request : %s" % content)

    except FileNotFoundError:
        raise VarError("File %s not found." % envs.REQUESTED_MODE_VAR_PATH)
    except IOError:
        raise VarError("Cannot open or read %s" % envs.REQUESTED_MODE_VAR_PATH)

    return mode


def write_requested_mode(mode):

    assert mode in ["intel", "nvidia", "hybrid"]

    folder_path, filename = os.path.split(envs.REQUESTED_MODE_VAR_PATH)

    if not os.path.isdir(folder_path):
        os.makedirs(folder_path)

    try:
        with open(envs.REQUESTED_MODE_VAR_PATH, 'w') as f:
            f.write(mode)
    except IOError:
        raise VarError("Cannot open or write to %s" % envs.REQUESTED_MODE_VAR_PATH)


def remove_requested_mode_var():

    try:
        os.remove(envs.REQUESTED_MODE_VAR_PATH)
    except FileNotFoundError:
        pass


def read_startup_mode():

    try:
        with open(envs.STARTUP_MODE_VAR_PATH, 'r') as f:
            content = f.read()

            if len(content) > 0 and content[-1] == "\n":
                content = content[:-1]

            if content in ["intel", "nvidia", "hybrid"]:
                mode = content
            else:
                raise VarError("Invalid value : %s" % content)
    except IOError:
        raise VarError("Cannot open or read %s" % envs.STARTUP_MODE_VAR_PATH)

    return mode


def write_startup_mode(mode):

    assert mode in ["intel", "nvidia", "hybrid"]

    folder_path, filename = os.path.split(envs.STARTUP_MODE_VAR_PATH)

    if not os.path.isdir(folder_path):
        os.makedirs(folder_path)

    try:
        with open(envs.STARTUP_MODE_VAR_PATH, 'w') as f:
            f.write(mode)
    except IOError:
        raise VarError("Cannot open or write to %s" % envs.STARTUP_MODE_VAR_PATH)


def remove_startup_mode_var():

    try:
        os.remove(envs.STARTUP_MODE_VAR_PATH)
    except FileNotFoundError:
        pass


def write_dpi_var(dpi):

    folder_path, filename = os.path.split(envs.DPI_VAR_PATH)

    if not os.path.isdir(folder_path):
        os.makedirs(folder_path)

    try:
        with open(envs.DPI_VAR_PATH, 'w') as f:
            f.write(str(dpi))
    except IOError:
        raise VarError("Cannot open or write to %s" % envs.DPI_VAR_PATH)


def remove_dpi_var():

    try:
        os.remove(envs.DPI_VAR_PATH)
    except FileNotFoundError:
        pass

def read_temp_conf_path_var():

    try:
        with open(envs.TEMP_CONFIG_PATH_VAR_PATH, 'r') as f:
            content = f.read()

            if len(content) > 0 and content[-1] == "\n":
                content = content[:-1]

            return content

    except FileNotFoundError:
        raise VarError("File %s not found." % envs.TEMP_CONFIG_PATH_VAR_PATH)
    except IOError:
        raise VarError("Cannot open or read %s" % envs.TEMP_CONFIG_PATH_VAR_PATH)

def write_temp_conf_path_var(path):

    folder_path, filename = os.path.split(envs.TEMP_CONFIG_PATH_VAR_PATH)

    if not os.path.isdir(folder_path):
        os.makedirs(folder_path)

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

    folder_path, filename = os.path.split(envs.ACPI_CALL_STRING_VAR_PATH)

    if not os.path.isdir(folder_path):
        os.makedirs(folder_path)

    try:
        with open(envs.ACPI_CALL_STRING_VAR_PATH, 'w') as f:
            json.dump(call_strings_list, f)
    except IOError:
        raise VarError("Cannot open or write to %s" % envs.ACPI_CALL_STRING_VAR_PATH)

def read_acpi_call_strings():

    try:
        with open(envs.ACPI_CALL_STRING_VAR_PATH, 'r') as f:
            call_strings_list = json.load(f)

        return call_strings_list

    except FileNotFoundError:
        raise VarError("File %s not found." % envs.ACPI_CALL_STRING_VAR_PATH)
    except (IOError, json.decoder.JSONDecodeError):
        raise VarError("Cannot open or read %s" % envs.ACPI_CALL_STRING_VAR_PATH)

def write_last_acpi_call_state(state):

    folder_path, filename = os.path.split(envs.LAST_ACPI_CALL_STATE_VAR)

    if not os.path.isdir(folder_path):
        os.makedirs(folder_path)

    try:
        with open(envs.LAST_ACPI_CALL_STATE_VAR, 'w') as f:
            f.write(state)
    except IOError:
        raise VarError("Cannot open or write to %s" % envs.LAST_ACPI_CALL_STATE_VAR)

def read_last_acpi_call_state():

    try:
        with open(envs.LAST_ACPI_CALL_STATE_VAR, 'r') as f:
            content = f.read()

            if len(content) > 0 and content[-1] == "\n":
                content = content[:-1]

            return content

    except FileNotFoundError:
        raise VarError("File %s not found." % envs.LAST_ACPI_CALL_STATE_VAR)
    except IOError:
        raise VarError("Cannot open or read %s" % envs.LAST_ACPI_CALL_STATE_VAR)

def remove_last_acpi_call_state():

    try:
        os.remove(envs.LAST_ACPI_CALL_STATE_VAR)
    except FileNotFoundError:
        pass
