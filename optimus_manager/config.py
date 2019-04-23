import os
import json
import configparser
import optimus_manager.envs as envs


class ConfigError(Exception):
    pass


def load_config():

    config = configparser.ConfigParser()

    try:
        if os.path.isfile(envs.USER_CONFIG_PATH):
            config.read([envs.DEFAULT_CONFIG_PATH, envs.USER_CONFIG_PATH])
        else:
            config.read(envs.DEFAULT_CONFIG_PATH)

    except configparser.ParsingError as e:
        raise ConfigError("Parsing error : %s" % str(e))

    validate_config(config)

    return config


def validate_config(config):

    folder_path = os.path.dirname(os.path.abspath(__file__))
    schema_path = os.path.join(folder_path, "config_schema.json")

    with open(schema_path, "r") as f:
        schema = json.load(f)

    # Checking if the config file has the required sections and options
    for section in schema.keys():

        if section not in config.keys():
            raise ConfigError("Cannot find header for section [%s]" % section)

        for option in schema[section].keys():

            if option not in config[section].keys():
                raise ConfigError("Cannot find option \"%s\" in section [%s]" % (option, section))

            parameter_type = schema[section][option][0]

            assert parameter_type in ["multi_words", "single_word", "integer"]

            # Multiple-words parameters
            if parameter_type == "multi_words":
                allowed_values = schema[section][option][1]
                can_be_blank = schema[section][option][2]

                values = config[section][option].replace(" ", "").split(",")

                if len(values) == ['']:
                    if not can_be_blank:
                        raise ConfigError("Option \"%s\" in section [%s] requires at least one parameter" % (option, section))

                else:
                    for val in values:
                        if val not in allowed_values:
                            raise ConfigError("Invalid value \"%s\" for option \"%s\" in section [%s]" % (val, option, section))

            # Single-word parameters
            elif parameter_type == "single_word":
                allowed_values = schema[section][option][1]
                can_be_blank = schema[section][option][2]

                val = config[section][option].replace(" ", "")

                if val == "":
                    if not can_be_blank:
                        raise ConfigError("Option \"%s\" in section [%s] requires a non-blank value" % (option, section))

                else:
                    if val not in allowed_values:
                        raise ConfigError("Invalid value \"%s\" for option \"%s\" in section [%s]" % (val, option, section))

            # Integer parameter
            elif parameter_type == "integer":
                can_be_blank = schema[section][option][1]

                val = config[section][option].replace(" ", "")

                if val == "":
                    if not can_be_blank:
                        raise ConfigError("Option \"%s\" in section [%s] requires a non-blank integer value" % (option, section))

                else:
                    try:
                        v = int(val)
                        if v <= 0:
                            raise ValueError
                    except ValueError:
                        raise ConfigError("Option \"%s\" in section [%s] requires a non-blank integer value" % (option, section))

    # Checking if the config file has no unknown section or option
    for section in config.keys():

        if section == "DEFAULT":
            continue

        if section not in schema.keys():
            raise ConfigError("Unknown section %s" % section)

        for option in config[section].keys():

            if option not in schema[section].keys():
                print("Config parsing : unknown option %s in section %s. Ignoring." % (option, section))
                del schema[section][option]


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
