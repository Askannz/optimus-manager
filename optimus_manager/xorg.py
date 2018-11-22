import optimus_manager.envs as envs
from optimus_manager.detection import get_bus_ids


class XorgError(Exception):
    pass


def configure_xorg(config, mode):

    bus_ids = get_bus_ids()

    if mode == "nvidia":
        xorg_conf_text = _generate_nvidia(config, bus_ids)
    elif mode == "intel":
        xorg_conf_text = _generate_intel(config, bus_ids)

    _write_xorg_conf(xorg_conf_text)


def _generate_nvidia(config, bus_ids):

    text = "Section \"Module\"\n" \
           "\tLoad \"modesetting\"\n" \
           "EndSection\n\n" \
           "Section \"Device\"\n" \
           "\tIdentifier \"nvidia\"\n" \
           "\tDriver \"nvidia\"\n"

    text += "\tBusID \"%s\"\n" % bus_ids["nvidia"]
    text += "\tOption \"AllowEmptyInitialConfiguration\"\n"

    if "overclocking" in config["nvidia"]["options"]:
        text += "\tOption \"Coolbits\" \"28\"\n"

    if "triple_buffer" in config["nvidia"]["options"]:
        text += "\"TripleBuffer\" \"true\"\n"

    dri = int(config["nvidia"]["DRI"])
    text += "\tOption \"DRI\" \"%d\"\n" % dri

    text += "EndSection\n"

    return text


def _generate_intel(config, bus_ids):

    text = "Section \"Device\"\n" \
           "\tIdentifier \"intel\"\n"

    text += "\tDriver \"%s\"\n" % config["intel"]["driver"]

    text += "\tBusID \"%s\"\n" % bus_ids["intel"]

    if config["intel"]["accel"] != "":
        text += "\tOption \"AccelMethod\" \"%d\"\n" % config["intel"]["accel"]

    if config["intel"]["tearfree"] != "":
        text += "\tOption \"TearFree\" \"%d\"\n" % config["intel"]["tearfree"]

    dri = int(config["intel"]["DRI"])
    text += "\tOption \"DRI\" \"%d\"\n" % dri

    text += "EndSection\n"

    return text


def _write_xorg_conf(xorg_conf_text):

    try:
        with open(envs.XORG_CONF_PATH, 'w') as f:
            f.write(xorg_conf_text)
    except IOError:
        raise XorgError("Cannot write Xorg conf at %s" % envs.XORG_CONF_PATH)
