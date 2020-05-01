import re
from .log_utils import get_logger


def get_kernel_parameters():

    logger = get_logger()

    with open("/proc/cmdline", "r") as f:
        cmdline = f.read()

    for item in cmdline.split():
        if re.fullmatch("optimus-manager\\.startup=[^ ]+", item):
            startup_mode = item.split("=")[-1]
<<<<<<< HEAD
            if startup_mode not in ["intel", "nvidia", "hybrid", "ac_auto"]:
                logger.error(
                    "Invalid startup mode in kernel parameter : \"%s\"."
                    " Ignored.", startup_mode)
=======
            if startup_mode not in ["nvidia", "amd", "intel", "hybrid-amd", "hybrid-intel", "ac_auto"]:
                print("ERROR : invalid startup mode in kernel parameter : \"%s\". Ignored." % startup_mode)
>>>>>>> 1bbdd19faeb1dcd961c39523bc518ae47df4bde8
                startup_mode = None
            break
    else:
        startup_mode = None

    return {"startup_mode": startup_mode}
