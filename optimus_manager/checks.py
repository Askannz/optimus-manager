import dbus
import os
import re
import subprocess
from ctypes import byref, c_int, c_uint, c_void_p, CDLL, POINTER, Structure
from pathlib import Path
from .log_utils import get_logger


class CheckError(Exception):
    pass


def check_running_graphical_session():
    return subprocess.run(
        "xhost",
        shell=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    ).returncode == 0


def is_ac_power_connected():
    for power_source_path in Path("/sys/class/power_supply/").iterdir():
        try:
            with open(power_source_path / "type", 'r') as f:
                if f.read().strip() != "Mains":
                    continue

            with open(power_source_path / "online", 'r') as f:
                if f.read(1) == "1":
                    return True

        except IOError:
            continue

    return False


class NvCfgPciDevice(Structure):
    _fields_ = [("domain", c_int), ("bus", c_int), ("slot", c_int), ("function", c_int)]


NvCfgPciDevicePtr = POINTER(NvCfgPciDevice)


def is_nvidia_display_connected():
    num_gpus = c_int()
    gpus = NvCfgPciDevicePtr()

    try:
        nvcfg_lib = CDLL("libnvidia-cfg.so")

    except OSError:
        raise CheckError("Missing nvidia-utils component: libnvidia-cfg.so")

    if nvcfg_lib.nvCfgGetPciDevices(byref(num_gpus), byref(gpus)) != 1:
        return False

    for i in range(num_gpus.value):
        device_handle = c_void_p()

        try:
            if nvcfg_lib.nvCfgOpenPciDevice(gpus[i].domain, gpus[i].bus, gpus[i].slot,
                                            c_int(0), byref(device_handle)) != 1:
                continue

            mask = c_uint()

            if nvcfg_lib.nvCfgGetDisplayDevices(device_handle, byref(mask)) != 1:
                continue

            if mask.value != 0:
                return True

        finally:
            nvcfg_lib.nvCfgCloseDevice(device_handle)
            # Ignores if the function fails

    return False


def is_pat_available():
    return subprocess.run(
        "grep -E '^flags.+ pat( |$)' /proc/cpuinfo",
        shell=True, stdout=subprocess.DEVNULL
    ).returncode == 0


def get_active_renderer():
    if _is_gl_provider_nvidia():
        return "nvidia"
    else:
        return "integrated"


def get_integrated_provider():
    try:
        out = subprocess.check_output(
                "xrandr --listproviders", shell=True, text=True, stderr=subprocess.PIPE).strip()

    except subprocess.CalledProcessError as error:
        raise CheckError(f"No xrandr provider: {error.stderr}") from error

    for line in out.splitlines():
        for _p in line.split():
            if _p in ["AMD", "Intel"]:
                return line.split("name:")[1]

    return "modesetting"


def is_module_available(module_name):
    return subprocess.run(
        f"modinfo -n {module_name}",
        shell=True, stdout=subprocess.DEVNULL
    ).returncode == 0


def is_module_loaded(module_name):
    return subprocess.run(
        f"lsmod | grep -E \"^{module_name}\"",
        shell=True, stdout=subprocess.DEVNULL
    ).returncode == 0


def get_current_display_manager():
    if not os.path.isfile("/etc/systemd/system/display-manager.service"):
        raise CheckError("Missing: display-manager.service")

    dm_service_path = os.path.realpath("/etc/systemd/system/display-manager.service")
    dm_service_filename = os.path.split(dm_service_path)[-1]
    dm_name = os.path.splitext(dm_service_filename)[0]
    return dm_name


def using_patched_GDM():
    folder_path_1 = "/etc/gdm/Prime"
    folder_path_2 = "/etc/gdm3/Prime"
    return os.path.isdir(folder_path_1) or os.path.isdir(folder_path_2)


def check_offloading_available():
    try:
        out = subprocess.check_output(
            "xrandr --listproviders", shell=True, text=True, stderr=subprocess.PIPE).strip()

    except subprocess.CalledProcessError as error:
        raise CheckError(f"Unable to list xrandr providers: {error.stderr}") from error

    for line in out.splitlines():
        if re.search("^Provider [0-9]+:", line) and "name:NVIDIA-G0" in line:
            return True

    return False


def is_xorg_intel_module_available():
    return os.path.isfile("/usr/lib/xorg/modules/drivers/intel_drv.so")


def is_xorg_amdgpu_module_available():
    return os.path.isfile("/usr/lib/xorg/modules/drivers/amdgpu_drv.so")


def is_login_manager_active():
    return _is_service_active("display-manager")


def is_daemon_active():
    return _is_service_active("optimus-manager")


def is_bumblebeed_service_active():
    return _is_service_active("bumblebeed")


def _is_gl_provider_nvidia():
    try:
        out = subprocess.check_output(
            "__NV_PRIME_RENDER_OFFLOAD=0 glxinfo",
            shell=True, text=True, stderr=subprocess.PIPE).strip()

    except subprocess.CalledProcessError as error:
        raise CheckError(f"glxinfo failed: {error.stderr}") from error

    for line in out.splitlines():
        if "server glx vendor string: NVIDIA Corporation" in line:
            return True

    return False


def _is_service_active(service_name):
    logger = get_logger()

    if subprocess.run(f"which sv", shell=True).returncode == 0:
        return _is_service_active_sv(service_name)

    if subprocess.run(f"which rc-status", shell=True).returncode == 0:
        return _is_service_active_openrc(service_name)

    if subprocess.run(f"which s6-svstat", shell=True).returncode == 0:
        return _is_service_active_s6(service_name)

    if subprocess.run(f"which systemctl", shell=True).returncode == 0:
        try:
            system_bus = dbus.SystemBus()

        except dbus.exceptions.DBusException:
            logger.warning(
                "Falling back to Bash commands: No DBus for: %s", service_name)

            return _is_service_active_bash(service_name)

        else:
            return _is_service_active_dbus(system_bus, service_name)

    return False # No service manager found


def _is_service_active_dbus(system_bus, service_name):
    systemd = system_bus.get_object("org.freedesktop.systemd1", "/org/freedesktop/systemd1")

    try:
        unit_path = systemd.GetUnit("%s.service" % service_name, dbus_interface="org.freedesktop.systemd1.Manager")

    except dbus.exceptions.DBusException:
        return False

    optimus_manager_interface = system_bus.get_object("org.freedesktop.systemd1", unit_path)
    properties_manager = dbus.Interface(optimus_manager_interface, 'org.freedesktop.DBus.Properties')
    state = properties_manager.Get("org.freedesktop.systemd1.Unit", "SubState")
    return state == "running"


def _is_service_active_bash(service_name):
    return subprocess.run(
        f"systemctl is-active {service_name}", shell=True
    ).returncode == 0


def _is_service_active_openrc(service_name):
    if subprocess.run(f"rc-status --nocolor default | grep -E '%s.*started'" % service_name, shell=True).returncode == 0:
        return True
    return False


def _is_service_active_s6(service_name):
    # TODO: Check if s6 service is running
    return True


def _is_service_active_sv(service_name):
    if subprocess.run(f"sv status %s | grep 'up: '" % service_name, shell=True).returncode == 0:
        return True

    return False
