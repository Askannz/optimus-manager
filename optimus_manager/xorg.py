import os
from pathlib import Path
from optimus_manager.bash import exec_bash, BashError
import optimus_manager.envs as envs
from .pci import get_gpus_bus_ids
from .config import load_extra_xorg_options
from .hacks.manjaro import remove_mhwd_conf
from .log_utils import get_logger


class XorgSetupError(Exception):
    pass


def configure_xorg(config, requested_gpu_mode):

    bus_ids = get_gpus_bus_ids()
    xorg_extra = load_extra_xorg_options()

    if requested_gpu_mode == "nvidia":
        xorg_conf_text = _generate_nvidia(config, bus_ids, xorg_extra)
    elif requested_gpu_mode == "intel":
        xorg_conf_text = _generate_intel(config, bus_ids, xorg_extra)
    elif requested_gpu_mode == "hybrid":
        xorg_conf_text = _generate_hybrid(config, bus_ids, xorg_extra)

    remove_mhwd_conf()
    _write_xorg_conf(xorg_conf_text)


def cleanup_xorg_conf():

    logger = get_logger()

    logger.info("Removing %s (if present)", envs.XORG_CONF_PATH)

    try:
        os.remove(envs.XORG_CONF_PATH)
    except FileNotFoundError:
        pass


def is_xorg_running():

    try:
        exec_bash("pidof X")
        return True
    except BashError:
        pass

    try:
        exec_bash("pidof Xorg")
        return True
    except BashError:
        pass

    return False


def is_there_a_default_xorg_conf_file():
    return os.path.isfile("/etc/X11/xorg.conf")


def is_there_a_MHWD_file():
    return os.path.isfile("/etc/X11/xorg.conf.d/90-mhwd.conf")


def do_xsetup(requested_mode):

    logger = get_logger()

    if requested_mode == "nvidia":

        logger.info("Running xrandr commands")

        try:
            exec_bash("xrandr --setprovideroutputsource modesetting NVIDIA-0")
            exec_bash("xrandr --auto")
        except BashError as e:
            logger.error("Cannot setup PRIME : %s", str(e))

    script_path = envs.XSETUP_SCRIPTS_PATHS[requested_mode]
    logger.info("Running %s", script_path)
    try:
        exec_bash(script_path)
    except BashError as e:
        logger.error("ERROR : cannot run %s : %s", script_path, str(e))


def set_DPI(config):

    dpi_str = config["nvidia"]["dpi"]

    if dpi_str == "":
        return

    try:
        exec_bash("xrandr --dpi %s" % dpi_str)
    except BashError as e:
        raise XorgSetupError("Cannot set DPI : %s" % str(e))


def _generate_nvidia(config, bus_ids, xorg_extra):

    text = "Section \"Files\"\n" \
           "\tModulePath \"/usr/lib/nvidia\"\n" \
           "\tModulePath \"/usr/lib32/nvidia\"\n" \
           "\tModulePath \"/usr/lib32/nvidia/xorg/modules\"\n" \
           "\tModulePath \"/usr/lib32/xorg/modules\"\n" \
           "\tModulePath \"/usr/lib64/nvidia/xorg/modules\"\n" \
           "\tModulePath \"/usr/lib64/nvidia/xorg\"\n" \
           "\tModulePath \"/usr/lib64/xorg/modules\"\n" \
           "EndSection\n\n"

    text += "Section \"ServerLayout\"\n" \
            "\tIdentifier \"layout\"\n" \
            "\tScreen 0 \"nvidia\"\n" \
            "\tInactive \"intel\"\n" \
            "EndSection\n\n"

    text += _make_nvidia_device_section(config, bus_ids, xorg_extra)

    text += "Section \"Screen\"\n" \
            "\tIdentifier \"nvidia\"\n" \
            "\tDevice \"nvidia\"\n" \
            "\tOption \"AllowEmptyInitialConfiguration\"\n"

    if config["nvidia"]["allow_external_gpus"] == "yes":
        text += "\tOption \"AllowExternalGpus\"\n"

    text += "EndSection\n\n"

    text += "Section \"Device\"\n" \
            "\tIdentifier \"intel\"\n" \
            "\tDriver \"modesetting\"\n"
    text += "\tBusID \"%s\"\n" % bus_ids["intel"]
    text += "EndSection\n\n"

    text += "Section \"Screen\"\n" \
            "\tIdentifier \"intel\"\n" \
            "\tDevice \"intel\"\n" \
            "EndSection\n\n"

    text += _make_server_flags_section(config)

    return text


def _generate_intel(config, bus_ids, xorg_extra):
    text = _make_intel_device_section(config, bus_ids, xorg_extra)
    return text

def _generate_hybrid(config, bus_ids, xorg_extra):

    text = "Section \"ServerLayout\"\n" \
           "\tIdentifier \"layout\"\n" \
           "\tScreen 0 \"intel\"\n" \
           "\tInactive \"nvidia\"\n" \
           "\tOption \"AllowNVIDIAGPUScreens\"\n" \
           "EndSection\n\n"

    text += _make_intel_device_section(config, bus_ids, xorg_extra)

    text += "Section \"Screen\"\n" \
           "\tIdentifier \"intel\"\n" \
           "\tDevice \"intel\"\n"

    if config["nvidia"]["allow_external_gpus"] == "yes":
        text += "\tOption \"AllowExternalGpus\"\n"

    text += "EndSection\n\n"

    text += _make_nvidia_device_section(config, bus_ids, xorg_extra)

    text += "Section \"Screen\"\n" \
           "\tIdentifier \"nvidia\"\n" \
           "\tDevice \"nvidia\"\n" \
           "EndSection\n\n"

    text += _make_server_flags_section(config)

    return text

def _make_nvidia_device_section(config, bus_ids, xorg_extra):

    options = config["nvidia"]["options"].replace(" ", "").split(",")

    text = "Section \"Device\"\n" \
           "\tIdentifier \"nvidia\"\n" \
           "\tDriver \"nvidia\"\n"
    text += "\tBusID \"%s\"\n" % bus_ids["nvidia"]
    if "overclocking" in options:
        text += "\tOption \"Coolbits\" \"28\"\n"
    if "triple_buffer" in options:
        text += "\tOption \"TripleBuffer\" \"true\"\n"
    if "nvidia" in xorg_extra.keys():
        for line in xorg_extra["nvidia"]:
            text += ("\t" + line + "\n")
    text += "EndSection\n\n"

    return text

def _make_intel_device_section(config, bus_ids, xorg_extra):

    logger = get_logger()

    if config["intel"]["driver"] == "intel" and not _is_intel_module_available():
        logger.warning("The Xorg intel module is not available. Defaulting to modesetting.")
        driver = "modesetting"
    else:
        driver = config["intel"]["driver"]

    dri = int(config["intel"]["dri"])

    text = "Section \"Device\"\n" \
           "\tIdentifier \"intel\"\n"
    text += "\tDriver \"%s\"\n" % driver
    text += "\tBusID \"%s\"\n" % bus_ids["intel"]
    if config["intel"]["accel"] != "":
        text += "\tOption \"AccelMethod\" \"%s\"\n" % config["intel"]["accel"]
    if config["intel"]["tearfree"] != "":
        tearfree_enabled_str = {"yes": "true", "no": "false"}[config["intel"]["tearfree"]]
        text += "\tOption \"TearFree\" \"%s\"\n" % tearfree_enabled_str
    text += "\tOption \"DRI\" \"%d\"\n" % dri
    if "intel" in xorg_extra.keys():
        for line in xorg_extra["intel"]:
            text += ("\t" + line + "\n")
    text += "EndSection\n\n"

    return text

def _make_server_flags_section(config):
    if config["nvidia"]["ignore_abi"] == "yes":
        return (
            "Section \"ServerFlags\"\n"
            "\tOption \"IgnoreABI\" \"1\"\n"
            "EndSection\n\n"
        )
    return ""

def _write_xorg_conf(xorg_conf_text):

    logger = get_logger()

    filepath = Path(envs.XORG_CONF_PATH)

    try:
        os.makedirs(filepath.parent, mode=0o755, exist_ok=True)
        with open(filepath, 'w') as f:
            logger.info("Writing to %s", envs.XORG_CONF_PATH)
            f.write(xorg_conf_text)
    except IOError:
        raise XorgSetupError("Cannot write Xorg conf at %s" % str(filepath))


def _is_intel_module_available():
    return os.path.isfile("/usr/lib/xorg/modules/drivers/intel_drv.so")
