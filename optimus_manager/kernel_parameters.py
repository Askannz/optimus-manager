import re
from .log_utils import get_logger


def get_kernel_parameters():

    logger = get_logger()

    with open("/proc/cmdline", "r") as f:
        cmdline = f.read()

    for item in cmdline.split():
        if re.fullmatch("optimus-manager\\.startup=[^ ]+", item):
            logger.info("Kernel parameter found: %s", item)
            startup_mode = item.split("=")[-1]
            if startup_mode not in ["igpu", "nvidia", "hybrid", "auto"]:
                logger.error(
                    "Invalid startup mode in kernel parameter : \"%s\"."
                    " Ignored.", startup_mode)
                startup_mode = None
            break
    else:
        startup_mode = None

    return {"startup_mode": startup_mode}
