import os
from optimus_manager.bash import exec_bash
from optimus_manager.detection import get_bus_ids, DetectionError


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

    if not is_xorg_running():
        raise CheckError("Xorg is not running")

    try:
        bus_ids = get_bus_ids(notation_fix=False)
    except DetectionError as e:
        raise CheckError("PCI detection error : %s" % str(e))

    nvidia_used = _does_xorg_use_card(bus_ids["nvidia"])
    intel_used = _does_xorg_use_card(bus_ids["intel"])

    if nvidia_used and intel_used:
        raise CheckError("Both GPUs are in use by Xorg")
    elif not nvidia_used and not intel_used:
        raise CheckError("No GPUs is in use by Xorg")
    elif nvidia_used:
        return "nvidia"
    elif intel_used:
        return "intel"


def is_daemon_active():

    state = exec_bash("systemctl is-active optimus-manager").stdout.decode('utf-8')[:-1]
    return (state == "active")


def _does_xorg_use_card(bus_id):

    dri_pci_filename = "pci-0000:" + bus_id + "-card"

    dri_path = os.path.join("/dev", "dri", "by-path", dri_pci_filename)

    ret = exec_bash("lsof %s | grep Xorg" % dri_path).returncode

    return (ret == 0)
