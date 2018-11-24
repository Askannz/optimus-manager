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
