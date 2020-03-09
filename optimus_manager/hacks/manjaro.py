import os

MHWD_CONF_PATH = "/etc/X11/xorg.conf.d/90-mhwd.conf"


def remove_mhwd_conf():

    try:
        os.remove(MHWD_CONF_PATH)
        print("Found MHWD-generated Xorg config file at %s. Removing." % MHWD_CONF_PATH)
    except FileNotFoundError:
        pass
