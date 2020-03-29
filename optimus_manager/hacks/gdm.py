from .. import processes
from ..log_utils import get_logger


def kill_gdm_server():

    logger = get_logger()

    logger.info("Checking for GDM display servers")

    try:
        xorg_PIDs_list = processes.get_PIDs_from_process_names(["Xorg", "X"])

        for PID_value in xorg_PIDs_list:
            user = processes.get_PID_user(PID_value)
            if user == "gdm":
                logger.info("Found a Xorg GDM process (PID %d), killing it...", PID_value)
                processes.kill_PID(PID_value, signal="-KILL")

    except processes.ProcessesError as e:
        raise RuntimeError("Error : cannot check for or kill the GDM display server : %s" % str(e))
