import optimus_manager.envs as envs
from optimus_manager.detection import get_bus_ids
from optimus_manager.config import load_extra_xorg_options
from optimus_manager.bash import exec_bash, BashError
from optimus_manager.polling import poll_block


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


def get_xorg_servers_pids():

    try:
        x_pids = exec_bash("pidof X")
    except BashError:
        x_pids = ""

    try:
        xorg_pids = exec_bash("pidof Xorg")
    except BashError:
        xorg_pids = ""

    pids_str_list = (x_pids.split() + xorg_pids.split())

    return [int(p_str) for p_str in pids_str_list]


def kill_current_xorg_servers():

    pids_list = get_xorg_servers_pids()

    if len(pids_list) > 0:
        print("There are %d X11 servers remaining, terminating them manually" % len(pids_list))

    for pid in pids_list:
        try:
            exec_bash("kill -9 %d" % pid)
        except BashError:
            pass

    success = poll_block(_is_xorg_running)

    if not success:
        raise XorgError("Failed to kill all X11 servers")


def _is_xorg_running():
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
