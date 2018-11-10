import optimus_manager.checks as checks
from optimus_manager.bash import exec_bash
from optimus_manager.xorg import configure_xorg
from optimus_manager.login_managers import configure_login_managers


# TODO : Add some error checking on exec_bash


class SwitchError(Exception):
    pass


def switch_to_intel(config):

    print("Switching to Intel")

    # Nvidia modules
    print("Unloading Nvidia modules")
    exec_bash("rmmod nvidia_drm nvidia_modeset nvidia")
    if not checks.are_nvidia_modules_unloaded():
        raise SwitchError("Cannot unload Nvidia modules")

    # bbswitch module
    if not checks.is_bbswitch_loaded():
        print("bbswitch not loaded, loading it...")
        exec_bash("modprobe bbswitch")
    if not checks.is_bbswitch_loaded():
        raise SwitchError("Cannot load bbswitch")

    # bbswitch switching
    print("Ordering OFF via bbswitch")
    exec_bash("echo OFF | tee /proc/acpi/bbswitch")
    if checks.is_gpu_powered():
        raise SwitchError("bbswitch refuses to turn OFF the GPU")
    else:
        print("bbswitch reports that the GPU is OFF")

    # Xorg configuration
    print("Configuring Xorg...")
    configure_xorg(config, mode="intel")

    # Login managers configuration
    print("Configuring login managers..")
    configure_login_managers(mode="intel")


def switch_to_nvidia(config):

    print("Switching to Nvidia")

    # bbswitch module
    if not checks.is_bbswitch_loaded():
        print("bbswitch not loaded, loading it...")
        exec_bash("modprobe bbswitch")
    if not checks.is_bbswitch_loaded():
        raise SwitchError("Cannot load bbswitch")

    # bbswitch switching
    print("Ordering ON via bbswitch")
    exec_bash("echo ON | tee /proc/acpi/bbswitch")
    if not checks.is_gpu_powered():
        raise SwitchError("bbswitch refuses to turn ON the GPU")
    else:
        print("bbswitch reports that the GPU is ON")

    # Nvidia modules
    print("Loading Nvidia modules")
    modeset_value = {"yes": 1, "no": 0}[config["nvidia"]["modeset"]]
    exec_bash("modprobe nvidia_drm modeset=%d" % modeset_value)
    exec_bash("modprobe nvidia_modeset nvidia")
    if not checks.are_nvidia_modules_loaded():
        raise SwitchError("Cannot load Nvidia modules")

    # Xorg configuration
    print("Configuring Xorg...")
    configure_xorg(config, mode="nvidia")

    # Login managers configuration
    print("Configuring login managers..")
    configure_login_managers(mode="nvidia")
