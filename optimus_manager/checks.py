from optimus_manager.bash import exec_bash, BashError


class CheckError(Exception):
    pass


def is_gpu_powered():

    state = exec_bash("cat /proc/acpi/bbswitch | cut -d' ' -f 2").stdout.decode('utf-8')[:-1]
    return state == "ON"


def is_login_manager_active(config):

    state = exec_bash("systemctl is-active display-manager").stdout.decode('utf-8')[:-1]
    return state == "active"


def is_pat_available():
    try:
        exec_bash("grep -E '^flags.+ pat( |$)' /proc/cpuinfo")
        return True
    except BashError:
        return False


def read_gpu_mode():
    try:
        exec_bash("glxinfo")
    except BashError as e:
        raise CheckError("Cannot find the current mode : %s" % str(e))

    try:
        exec_bash("glxinfo | grep NVIDIA")
        return "nvidia"
    except BashError:
        return "intel"


def is_daemon_active():
    state = exec_bash("systemctl is-active optimus-manager").stdout.decode('utf-8')[:-1]
    return state == "active"


def is_module_available(module_name):

    try:
        exec_bash("modinfo %s" % module_name)
    except BashError:
        return False
    else:
        return True
