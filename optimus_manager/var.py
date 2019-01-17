import os
import optimus_manager.envs as envs


class VarError(Exception):
    pass


def read_requested_mode():

    try:
        with open(envs.REQUESTED_MODE_VAR_PATH, 'r') as f:
            content = f.read()

            if len(content) > 0 and content[-1] == "\n":
                content = content[:-1]

            if content in ["intel", "nvidia"]:
                mode = content
            else:
                raise VarError("Invalid mode request : %s" % content)

    except FileNotFoundError:
        raise VarError("File %s not found." % envs.REQUESTED_MODE_VAR_PATH)
    except IOError:
        raise VarError("Cannot open or read %s" % envs.REQUESTED_MODE_VAR_PATH)

    return mode


def write_requested_mode(mode):

    assert mode in ["intel", "nvidia"]

    folder_path, filename = os.path.split(envs.REQUESTED_MODE_VAR_PATH)

    if not os.path.isdir(folder_path):
        os.makedirs(folder_path)

    try:
        with open(envs.REQUESTED_MODE_VAR_PATH, 'w') as f:
            f.write(mode)
    except IOError:
        raise VarError("Cannot open or write to %s" % envs.REQUESTED_MODE_VAR_PATH)


def remove_request_mode_var():

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

            if content in ["intel", "nvidia", "nvidia_once"]:
                mode = content
            else:
                raise VarError("Invalid value : %s" % content)
    except IOError:
        raise VarError("Cannot open or read %s" % envs.STARTUP_MODE_VAR_PATH)

    return mode


def write_startup_mode(mode):

    assert mode in ["intel", "nvidia", "nvidia_once"]

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
