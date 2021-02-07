import subprocess
from .log_utils import get_logger


class ProcessesError(Exception):
    pass


def get_PIDs_from_process_names(processes_names_list):

    logger = get_logger()

    PIDs_list = []

    for p_name in processes_names_list:

        try:
            process_PIDs_str = subprocess.check_output(
                f"pidof {p_name}", shell=True, text=True).strip()
        except subprocess.CalledProcessError:
            continue

        try:
            process_PIDs_list = [
                int(pid_str)
                for pid_str in process_PIDs_str.split(" ")
            ]
        except ValueError:
            logger.warning(
                f"Cannot parse pidof output for process {p_name} : "
                f"invalid value : {process_PIDs_str}")
            continue

        PIDs_list += process_PIDs_list

    return PIDs_list


def get_PID_user(PID_value):

    try:
        user = subprocess.check_output(
            f"ps -o uname= -p {PID_value}", shell=True, text=True).strip()
    except subprocess.CalledProcessError as e:
        raise ProcessesError("PID %d does not exist" % PID_value) from e

    return user


def kill_PID(PID_value, signal):

    try:
        subprocess.check_call(
            f"kill {signal} {PID_value}", shell=True, text=True,
            stderr=subprocess.PIPE, stdout=subprocess.DEVNULL)
    except subprocess.CalledProcessError as e:
        raise ProcessesError(f"Cannot kill PID {PID_value}: {e.stderr}") from e
