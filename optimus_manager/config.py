import os
import configparser
import optimus_manager.envs as envs


def load_config():

    config = configparser.ConfigParser()

    if os.path.isfile(envs.USER_CONFIG_PATH):
        config.read([envs.DEFAULT_CONFIG_PATH, envs.USER_CONFIG_PATH])
    else:
        config.read(envs.DEFAULT_CONFIG_PATH)

    return config
