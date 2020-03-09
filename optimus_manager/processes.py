from .bash import exec_bash, BashError


class ProcessesError(Exception):
    pass


def get_PIDs_from_process_names(processes_names_list):

    PIDs_list = []

    for p_name in processes_names_list:

        try:
            process_PIDs_str = exec_bash("pidof %s" % p_name).stdout.decode('utf-8')[:-1]
        except BashError:
            continue

        try:
            process_PIDs_list = [int(pid_str) for pid_str in process_PIDs_str.split(" ")]
        except ValueError:
            print("Warning : cannot parse pidof output for process %s : invalid value : %s" % (p_name, process_PIDs_str))
            continue

        PIDs_list += process_PIDs_list

    return PIDs_list


def get_PID_user(PID_value):

    try:
        user = exec_bash("ps -o uname= -p %d" % PID_value).stdout.decode('utf-8')[:-1]
    except BashError:
        raise ProcessesError("PID %d does not exist" % PID_value)

    return user


def kill_PID(PID_value, signal):

    try:
        exec_bash("kill %s %d" % (signal, PID_value))
    except BashError:
        raise ProcessesError("Cannot kill PID %d" % PID_value)
