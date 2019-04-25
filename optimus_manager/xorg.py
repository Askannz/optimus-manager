import os
from optimus_manager.bash import exec_bash, BashError
import optimus_manager.envs as envs
from optimus_manager.pci import get_bus_ids
from optimus_manager.config import load_extra_xorg_options
from optimus_manager import manjaro_hacks


class XorgSetupError(Exception):
    pass


def configure_xorg(config, requested_gpu_mode):

    bus_ids = get_bus_ids()
    xorg_extra = load_extra_xorg_options()

    if requested_gpu_mode == "nvidia":
        xorg_conf_text = _generate_nvidia(config, bus_ids, xorg_extra)
    elif requested_gpu_mode == "intel":
        xorg_conf_text = _generate_intel(config, bus_ids, xorg_extra)

    manjaro_hacks.remove_mhwd_conf()
    _write_xorg_conf(xorg_conf_text)


def cleanup_xorg_conf():

    try:
        os.remove(envs.XORG_CONF_PATH)
        print("Removed %s" % envs.XORG_CONF_PATH)
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


def _generate_nvidia(config, bus_ids, xorg_extra):

    text = "Section \"Module\"\n" \
           "\tLoad \"modesetting\"\n" \
           "EndSection\n\n" \
           "Section \"Device\"\n" \
           "\tIdentifier \"nvidia\"\n" \
           "\tDriver \"nvidia\"\n"

    text += "\tBusID \"%s\"\n" % bus_ids["nvidia"]
    text += "\tOption \"AllowEmptyInitialConfiguration\"\n"

    options = config["nvidia"]["options"].replace(" ", "").split(",")

    if "overclocking" in options:
        text += "\tOption \"Coolbits\" \"28\"\n"

    if "triple_buffer" in options:
        text += "\tOption \"TripleBuffer\" \"true\"\n"

    if "nvidia" in xorg_extra.keys():
        for line in xorg_extra["nvidia"]:
            text += ("\t" + line + "\n")

    text += "EndSection\n"

    return text


def _generate_intel(config, bus_ids, xorg_extra):

    text = "Section \"Device\"\n" \
           "\tIdentifier \"intel\"\n"

    text += "\tDriver \"%s\"\n" % config["intel"]["driver"]

    text += "\tBusID \"%s\"\n" % bus_ids["intel"]

    if config["intel"]["accel"] != "":
        text += "\tOption \"AccelMethod\" \"%s\"\n" % config["intel"]["accel"]

    if config["intel"]["tearfree"] != "":
        bool_str = {"yes": "true", "no": "false"}[config["intel"]["tearfree"]]
        text += "\tOption \"TearFree\" \"%s\"\n" % bool_str

    dri = int(config["intel"]["DRI"])
    text += "\tOption \"DRI\" \"%d\"\n" % dri

    if "intel" in xorg_extra.keys():
        for line in xorg_extra["intel"]:
            text += ("\t" + line + "\n")

    text += "EndSection\n"

    return text


def _write_xorg_conf(xorg_conf_text):

    try:
        with open(envs.XORG_CONF_PATH, 'w') as f:
            print("Writing to %s" % envs.XORG_CONF_PATH)
            f.write(xorg_conf_text)
    except IOError:
        raise XorgSetupError("Cannot write Xorg conf at %s" % envs.XORG_CONF_PATH)
