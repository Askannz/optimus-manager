import configparser
import copy
import json
import os
import shutil
from pathlib import Path
from . import envs
from . import var
from .log_utils import get_logger


class ConfigError(Exception):
    pass


def load_config():
    config = _load_config()
    config = _convert_deprecated(config)
    return config


def _load_config():
    logger = get_logger()
    base_config = configparser.ConfigParser()
    base_config.read(envs.DEFAULT_CONFIG_PATH)
    base_config = _parsed_config_to_dict(base_config)
    _validate_config(base_config)

    if not os.path.isfile(envs.USER_CONFIG_COPY_PATH):
        return base_config

    try:
        user_config = configparser.ConfigParser()
        user_config.read([envs.DEFAULT_CONFIG_PATH, envs.USER_CONFIG_COPY_PATH])
        user_config = _parsed_config_to_dict(user_config)

    except configparser.ParsingError as error:
        logger.error(
            "Falling back to default config: Defective user config: %s: %s",
            envs.USER_CONFIG_COPY_PATH, str(error))

        return base_config

    corrected_config = _validate_config(user_config, fallback_config=base_config)
    return corrected_config


def _convert_deprecated(config):
    if config["optimus"]["startup_mode"] == "intel":
        config["optimus"]["startup_mode"] = "integrated"

    if config["optimus"]["startup_auto_battery_mode"] == "intel":
        config["optimus"]["startup_auto_battery_mode"] = "integrated"

    if config["optimus"]["startup_auto_extpower_mode"] == "intel":
        config["optimus"]["startup_auto_extpower_mode"] = "integrated"

    return config


def copy_user_config():
    logger = get_logger()

    try:
        temp_config_path = var.read_temp_conf_path_var()

    except var.VarError:
        config_path = envs.USER_CONFIG_PATH

    else:
        logger.info("Using temporary configuration: %s", temp_config_path)
        var.remove_temp_conf_path_var()

        if os.path.isfile(temp_config_path):
            config_path = temp_config_path

        else:
            logger.warning(
                "Falling back to default user config: Temporary config doesn't exist: %s",
                temp_config_path)
            config_path = envs.USER_CONFIG_PATH

    if os.path.isfile(config_path):
        copy_path = Path(envs.USER_CONFIG_COPY_PATH)
        os.makedirs(copy_path.parent, exist_ok=True)
        logger.info("Copying \"%s\" into \"%s\"", config_path, copy_path)
        shutil.copy(config_path, copy_path)


def _validate_config(config, fallback_config=None):
    logger = get_logger()
    folder_path = os.path.dirname(os.path.abspath(__file__))
    schema_path = os.path.join(folder_path, "config_schema.json")

    with open(schema_path, "r") as schemapath:
        schema = json.load(schemapath)

    corrected_config = copy.deepcopy(config)

    # Checking for required sections and options
    for section in schema.keys():
        if section not in config.keys():
            raise ConfigError("No header for section: [%s]" % section)

        for option in schema[section].keys():
            if option not in config[section].keys():
                raise ConfigError("Missing option \"%s\" in section \"[%s]\"" % (option, section))

            valid, msg = _validate_option(schema[section][option], config[section][option])

            if not valid:
                error_msg = "Invalid option \"%s\" in section \"[%s]\": %s" % (option, section, msg)

                if fallback_config is not None:
                    logger.error(error_msg)
                    logger.info("Falling back to default value: %s", fallback_config[section][option])
                    corrected_config[section][option] = fallback_config[section][option]

                else:
                    raise ConfigError(error_msg)

    # Checking for unknown sections or options
    for section in config.keys():
        if section not in schema.keys():
            logger.warning("Ignoring unknown section: [%s]", section)
            continue

        for option in config[section].keys():
            if option not in schema[section].keys():
                logger.warning("Ignoring unknown option \"%s\" in section \"[%s]\"", option, section)
                del corrected_config[section][option]

    return corrected_config


def _parsed_config_to_dict(config):
    config_dict = {}

    for section in config.keys():
        if section == "DEFAULT":
            continue

        config_dict[section] = {}

        for option in config[section].keys():
            config_dict[section][option] = config[section][option]

    return config_dict


def _validate_option(schema_option_info, config_option_value):
    parameter_type = schema_option_info[0]
    assert parameter_type in ["multi_words", "single_word", "integer"]

    if parameter_type == "multi_words":
        valid, msg = _validate_multi_words(schema_option_info, config_option_value)

    elif parameter_type == "single_word":
        valid, msg = _validate_single_word(schema_option_info, config_option_value)

    elif parameter_type == "integer":
        valid, msg = _validate_integer(schema_option_info, config_option_value)

    return valid, msg


def _validate_multi_words(schema_option_info, config_option_value):
    parameter_type, allowed_values, can_be_blank = schema_option_info
    assert parameter_type == "multi_words"
    values = config_option_value.replace(" ", "").split(",")

    if values == ['']:
        if not can_be_blank:
            msg = "At least one parameter required"
            return False, msg

    else:
        for value in values:
            if value not in allowed_values:
                msg = "Invalid value: %s" % value
                return False, msg

    return True, None


def _validate_single_word(schema_option_info, config_option_value):
    parameter_type, allowed_values, can_be_blank = schema_option_info
    assert parameter_type == "single_word"
    val = config_option_value.replace(" ", "")

    if val == "":
        if not can_be_blank:
            msg = "Non-blank value required"
            return False, msg

    else:
        if val not in allowed_values:
            msg = "Invalid value: %s" % val
            return False, msg

    return True, None


def _validate_integer(schema_option_info, config_option_value):
    parameter_type, can_be_blank = schema_option_info
    assert parameter_type == "integer"
    value = config_option_value.replace(" ", "")

    if value == "":
        if not can_be_blank:
            msg = "Value can't be blank"
            return False, msg

    else:
        try:
            v = int(value)
            if v < 0:
                raise ValueError
        except ValueError:
            msg = f"Positive integer required: {value}"
            return False, msg

    return True, None


def load_extra_xorg_options():
    logger = get_logger()
    xorg_extra = {}

    for mode, path_by_gpu in envs.EXTRA_XORG_OPTIONS_PATHS.items():
        xorg_extra[mode] = {}

        for gpu, path in path_by_gpu.items():
            try:
                config_lines = _load_extra_xorg_file(path)

            except FileNotFoundError:
                config_lines = []

            if len(config_lines) > 0:
                logger.info("Loaded extra %s Xorg options: %d", mode, len(config_lines))

            xorg_extra[mode][gpu] = config_lines

    return xorg_extra


def _load_extra_xorg_file(path):
    with open(path, 'r') as filepath:
        config_lines = []

        for line in filepath:
            line = line.strip()
            line_nospaces = line.replace(" ", "")

            if len(line_nospaces) == 0 or line_nospaces[0] == "#":
                continue

            config_lines.append(line)

        return config_lines
