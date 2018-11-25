import optimus_manager.envs as envs
from optimus_manager.detection import get_bus_ids
from optimus_manager.config import load_extra_xorg_options


class XorgError(Exception):
    pass


def configure_xorg(config, mode):

    bus_ids = get_bus_ids()
    xorg_extra = load_extra_xorg_options()

    if mode == "nvidia":
        xorg_conf_text = _generate_nvidia(config, bus_ids, xorg_extra)
    elif mode == "intel":
        xorg_conf_text = _generate_intel(config, bus_ids, xorg_extra)

    _write_xorg_conf(xorg_conf_text)


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

    dri = int(config["nvidia"]["DRI"])
    text += "\tOption \"DRI\" \"%d\"\n" % dri

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
            f.write(xorg_conf_text)
    except IOError:
        raise XorgError("Cannot write Xorg conf at %s" % envs.XORG_CONF_PATH)
