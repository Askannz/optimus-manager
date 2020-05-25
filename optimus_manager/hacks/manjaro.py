import os
from ..log_utils import get_logger

MHWD_CONF_PATH = "/etc/X11/xorg.conf.d/90-mhwd.conf"


def remove_mhwd_conf():

    logger = get_logger()

    try:
        os.remove(MHWD_CONF_PATH)
        logger.info(
            "Found MHWD-generated Xorg config file at %s. Removing.", MHWD_CONF_PATH)
    except FileNotFoundError:
        pass
