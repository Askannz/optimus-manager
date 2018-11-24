import os
import configparser
import optimus_manager.envs as envs


def load_config():

    if os.path.isfile(envs.USER_CONFIG_PATH):
        user_config_path = envs.USER_CONFIG_PATH
    elif os.path.isfile(envs.DEPRECATED_USER_CONFIG_PATH):
        print("Warning : Your configuration file is at the deprecated location %s.\n"
              "Please move it to %s" % (envs.DEPRECATED_USER_CONFIG_PATH, envs.USER_CONFIG_PATH))
        user_config_path = envs.DEPRECATED_USER_CONFIG_PATH
    else:
        user_config_path = None

    config = configparser.ConfigParser()

    if user_config_path is not None:
        config.read([envs.DEFAULT_CONFIG_PATH, user_config_path])
    else:
        config.read(envs.DEFAULT_CONFIG_PATH)

    return config


def load_extra_xorg_options():

    xorg_extra = {}

    try:
        config_lines = _load_extra_xorg_file(envs.EXTRA_XORG_OPTIONS_INTEL_PATH)
        print("Loaded extra Intel Xorg options (%d lines)" % len(config_lines))
        xorg_extra["intel"] = config_lines
    except FileNotFoundError:
        pass

    try:
        config_lines = _load_extra_xorg_file(envs.EXTRA_XORG_OPTIONS_NVIDIA_PATH)
        print("Loaded extra Nvidia Xorg options (%d lines)" % len(config_lines))
        xorg_extra["nvidia"] = config_lines
    except FileNotFoundError:
        pass

    return xorg_extra


def _load_extra_xorg_file(path):

    with open(path, 'r') as f:

        config_lines = []

        for line in f:

            line = line.strip()
            line_nospaces = line.replace(" ", "")

            if len(line_nospaces) == 0 or line_nospaces[0] == "#":
                continue

            else:
                config_lines.append(line)

        return config_lines
