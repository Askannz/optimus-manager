from optimus_manager.bash import exec_bash


class CheckError(Exception):
    pass


def is_bbswitch_loaded():
    ret = exec_bash("lsmod | grep bbswitch").returncode
    return (ret == 0)


def is_nouveau_loaded():
    ret = exec_bash("lsmod | grep nouveau").returncode
    return (ret == 0)


def are_nvidia_modules_loaded():
    ret1 = exec_bash("lsmod | grep nvidia_drm").returncode
    ret2 = exec_bash("lsmod | grep nvidia_modeset").returncode
    ret3 = exec_bash("lsmod | grep nvidia").returncode
    ret4 = exec_bash("lsmod | grep nvidia_uvm").returncode
    return (ret1 == 0) and (ret2 == 0) and (ret3 == 0) and (ret4 == 0)


def are_nvidia_modules_unloaded():
    ret1 = exec_bash("lsmod | grep nvidia_drm").returncode
    ret2 = exec_bash("lsmod | grep nvidia_modeset").returncode
    ret3 = exec_bash("lsmod | grep nvidia").returncode
    ret4 = exec_bash("lsmod | grep nvidia_uvm").returncode
    return (ret1 != 0) and (ret2 != 0) and (ret3 != 0) and (ret4 != 0)


def is_gpu_powered():

    state = exec_bash("cat /proc/acpi/bbswitch | cut -d' ' -f 2").stdout.decode('utf-8')[:-1]
    return (state == "ON")


def is_login_manager_active(config):

    state = exec_bash("systemctl is-active display-manager").stdout.decode('utf-8')[:-1]
    return (state == "active")


def is_xorg_running():

    ret1 = exec_bash("pidof X").returncode
    ret2 = exec_bash("pidof Xorg").returncode

    return (ret1 == 0) or (ret2 == 0)


def is_pat_available():
    ret = exec_bash("grep -E '^flags.+ pat( |$)' /proc/cpuinfo").returncode
    return (ret == 0)


def read_gpu_mode():

    ret = exec_bash("glxinfo").returncode
    if ret != 0:
        raise CheckError("Cannot find the current mode")
    else:
        ret = exec_bash("glxinfo | grep NVIDIA").returncode
        if ret == 0:
            return "nvidia"
        else:
            return "intel"
