import os
import checks
import envs
from bash import exec_bash
from detection import get_bus_ids
from generation import generate_xorg_conf
from login_managers import configure_login_managers


# TODO : Add some error checking on exec_bash


class SwitchError(Exception):
    pass


def switch_to_intel():

    print("Switching to Intel")

    # Nvidia modules
    print("Unloading Nvidia modules")
    exec_bash("rmmod nvidia_drm nvidia_modeset nvidia")
    os.popen("rmmod nvidia_drm nvidia_modeset nvidia")
    if not checks.are_nvidia_modules_unloaded():
        raise SwitchError("Cannot unload Nvidia modules")

    # bbswitch module
    if not checks.is_bbswitch_loaded():
        print("bbswitch not loaded, loading it...")
        os.popen("modprobe bbswitch")
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
    print("Setting up Xorg...")
    bus_ids = get_bus_ids()
    xorg_conf_text = generate_xorg_conf(bus_ids, mode="intel", options=[])
    _write_xorg_conf(xorg_conf_text)

    # Login managers configuration
    print("Configuring login managers..")
    configure_login_managers(mode="intel")


def switch_to_nvidia():

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
    exec_bash("modprobe nvidia_drm nvidia_modeset nvidia")
    if not checks.are_nvidia_modules_loaded():
        raise SwitchError("Cannot load Nvidia modules")

    # Xorg configuration
    print("Setting up Xorg...")
    bus_ids = get_bus_ids()
    xorg_conf_text = generate_xorg_conf(bus_ids, mode="nvidia", options=[])
    _write_xorg_conf(xorg_conf_text)

    # Login managers configuration
    print("Configuring login managers..")
    configure_login_managers(mode="nvidia")


# TODO :Move that to another file
def _write_xorg_conf(xorg_conf_text):

    try:
        with open(envs.XORG_CONF_PATH, 'w') as f:
            f.write(xorg_conf_text)
    except IOError:
        raise SwitchError("Cannot write Xorg conf at %s" % envs.XORG_CONF_PATH)
