import os
import optimus_manager.envs as envs


class VarError(Exception):
    pass


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
