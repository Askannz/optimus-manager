import os
import optimus_manager.envs as envs
from optimus_manager.bash import exec_bash


class VarError(Exception):
    pass


def read_requested_mode():

    try:
        with open(envs.REQUESTED_MODE_FILE_PATH, 'r') as f:
            content = f.read()

            if content[-1] == "\n":
                content = content[:-1]

            if content in ["intel", "nvidia"]:
                mode = content
            else:
                raise VarError("Invalid mode request : %s" % content)

    except FileNotFoundError:
        raise VarError("File %s not found." % envs.REQUESTED_MODE_FILE_PATH)
    except IOError:
        raise VarError("Cannot open or read %s" % envs.REQUESTED_MODE_FILE_PATH)

    return mode


def write_requested_mode(mode):

    assert mode in ["intel", "nvidia"]

    folder_path, filename = os.path.split(envs.REQUESTED_MODE_FILE_PATH)

    if not os.path.isdir(folder_path):
        os.makedirs(folder_path)

    try:
        with open(envs.REQUESTED_MODE_FILE_PATH, 'w') as f:
            f.write(mode)
    except IOError:
        raise VarError("Cannot open or write to %s" % envs.REQUESTED_MODE_FILE_PATH)


def remove_request_mode_var():

    try:
        os.remove(envs.REQUESTED_MODE_FILE_PATH)
    except FileNotFoundError:
        pass


def read_mode():
    ret = exec_bash("glxinfo").returncode
    if ret != 0:
        raise VarError("Cannot find current mode because mesa_demos is not installed")
    else:
        ret = exec_bash("glxinfo | grep NVIDIA").returncode
        if ret == 0:
            return "nvidia"
        else:
            return "intel"


def read_startup_mode():

    try:
        with open(envs.STARTUP_MODE_FILE_PATH, 'r') as f:
            content = f.read()

            if content[-1] == "\n":
                content = content[:-1]

            if content in ["intel", "nvidia", "nvidia_once"]:
                mode = content
            else:
                raise VarError("Invalid value : %s" % content)
    except IOError:
        raise VarError("Cannot open or read %s" % envs.STARTUP_MODE_FILE_PATH)

    return mode


def write_startup_mode(mode):

    assert mode in ["intel", "nvidia", "nvidia_once"]

    folder_path, filename = os.path.split(envs.STARTUP_MODE_FILE_PATH)

    if not os.path.isdir(folder_path):
        os.makedirs(folder_path)

    try:
        with open(envs.STARTUP_MODE_FILE_PATH, 'w') as f:
            f.write(mode)
    except IOError:
        raise VarError("Cannot open or write to %s" % envs.STARTUP_MODE_FILE_PATH)
