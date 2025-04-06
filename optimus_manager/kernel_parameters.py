import re
from .log_utils import get_logger

def get_kernel_parameters():
    logger = get_logger()

    with open("/proc/cmdline", "r") as cmdfile:
        cmdline = cmdfile.read()

    index = 0
    parameters = cmdline.split()
    startup_mode = None

    while startup_mode is None and index < len(parameters):
        if re.fullmatch("optimus-manager\\.startup=[^ ]+", parameters[index]):
            logger.info("Kernel parameter: %s", parameters[index])
            potential_mode = parameters[index].split("=")[-1]

            if potential_mode in ["auto", "hybrid", "integrated", "nvidia"]:
                startup_mode = potential_mode

            else:
                logger.error(
                    "Ignored invalid startup mode in kernel parameter: %s", potential_mode)

        index += 1

    return {"startup_mode": startup_mode}
