from optimus_manager.bash import exec_bash


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
    return (ret1 == 0) and (ret2 == 0) and (ret3 == 0)


def are_nvidia_modules_unloaded():
    ret1 = exec_bash("lsmod | grep nvidia_drm").returncode
    ret2 = exec_bash("lsmod | grep nvidia_modeset").returncode
    ret3 = exec_bash("lsmod | grep nvidia").returncode
    return (ret1 != 0) and (ret2 != 0) and (ret3 != 0)


def is_gpu_powered():

    state = exec_bash("cat /proc/acpi/bbswitch | cut -d' ' -f 2").stdout.decode('utf-8')[:-1]
    return (state == "ON")


def is_login_manager_active():

    state = exec_bash("systemctl is-active display-manager").stdout.decode('utf-8')[:-1]
    return (state == "active")
