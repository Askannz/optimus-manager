import os
import shutil
import checks
from bash import exec_bash

SYSTEM_CONFIGS_PATH = "/etc/prime_switcher/configs/"


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
    reference_config_folder = os.path.join(SYSTEM_CONFIGS_PATH, "intel/xorg")
    xorg_config_folder = "/etc/X11/xorg.conf.d/"
    for f in os.listdir(xorg_config_folder):
        filepath = os.path.join(xorg_config_folder, f)
        os.remove(filepath)
    for f in os.listdir(reference_config_folder):
        if "prime-switcher" in f:
            orig_filepath = os.path.join(reference_config_folder, f)
            dest_filepath = os.path.join(xorg_config_folder, f)
            shutil.copy(orig_filepath, dest_filepath)


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
    reference_config_folder = os.path.join(SYSTEM_CONFIGS_PATH, "nvidia/xorg")
    xorg_config_folder = "/etc/X11/xorg.conf.d/"
    for f in os.listdir(xorg_config_folder):
        filepath = os.path.join(xorg_config_folder, f)
        os.remove(filepath)
    for f in os.listdir(reference_config_folder):
        if "prime-switcher" in f:
            orig_filepath = os.path.join(reference_config_folder, f)
            dest_filepath = os.path.join(xorg_config_folder, f)
            shutil.copy(orig_filepath, dest_filepath)
