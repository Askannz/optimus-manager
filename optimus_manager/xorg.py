import optimus_manager.envs as envs
from optimus_manager.detection import get_bus_ids


class XorgError(Exception):
    pass


def configure_xorg(config, mode):

    bus_ids = get_bus_ids()

    if mode == "nvidia":
        xorg_conf_text = _generate_nvidia(bus_ids, options=config["nvidia"]["options"])
    elif mode == "intel":
        xorg_conf_text = _generate_intel(bus_ids, options=config["intel"]["options"])

    _write_xorg_conf(xorg_conf_text)


def _generate_nvidia(bus_ids, options):

    text = "Section \"Module\"\n" \
           "\tLoad \"modesetting\"\n" \
           "EndSection\n\n" \
           "Section \"Device\"\n" \
           "\tIdentifier \"nvidia\"\n" \
           "\tDriver \"nvidia\"\n"

    text += "\tBusID \"%s\"\n" % bus_ids["nvidia"]
    text += "\tOption \"AllowEmptyInitialConfiguration\"\n"

    if "overclocking" in options:
        text += "\tOption \"Coolbits\" \"28\"\n"

    if "triple_buffer" in options:
        text += "\"TripleBuffer\" \"true\"\n"

    text += "EndSection\n"

    return text


def _generate_intel(bus_ids, options):

    text = "Section \"Device\"\n" \
           "\tIdentifier \"intel\"\n" \
           "\tDriver \"modesetting\"\n"

    text += "\tBusID \"%s\"\n" % bus_ids["intel"]

    if "dri_3" in options:
        text += "\tOption \"DRI\" \"3\"\n"

    text += "EndSection\n"

    return text


def _write_xorg_conf(xorg_conf_text):

    try:
        with open(envs.XORG_CONF_PATH, 'w') as f:
            f.write(xorg_conf_text)
    except IOError:
        raise XorgError("Cannot write Xorg conf at %s" % envs.XORG_CONF_PATH)
