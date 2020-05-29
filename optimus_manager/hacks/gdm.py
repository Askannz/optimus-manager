from .. import processes
from ..log_utils import get_logger
from ..checks import _detect_init_system, using_patched_GDM
from ..bash import BashError, exec_bash


def kill_gdm_server():

    logger = get_logger()

    logger.info("Checking for GDM display servers")

    try:
        xorg_PIDs_list = processes.get_PIDs_from_process_names(["Xorg", "X"])

        for PID_value in xorg_PIDs_list:
            user = processes.get_PID_user(PID_value)
            if user == "gdm" or user == "root":
                logger.info("Found a Xorg GDM process (PID %d), killing it...", PID_value)
                processes.kill_PID(PID_value, signal="-KILL")

    except processes.ProcessesError as e:
        raise RuntimeError("Error : cannot check for or kill the GDM display server : %s" % str(e))

def restart_gdm_server():

    logger = get_logger()

    if using_patched_GDM() and _detect_init_system("runit-void") or _detect_init_system(init="runit-artix"):
        try:
            logger.info("Restarting GDM server")
            exec_bash("sv restart gdm")
        except BashError:
            pass
