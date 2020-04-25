import os
from pathlib import Path
import re
import dbus
from optimus_manager.bash import exec_bash, BashError


class CheckError(Exception):
    pass


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


def is_pat_available():
    try:
        exec_bash("grep -E '^flags.+ pat( |$)' /proc/cpuinfo")
        return True
    except BashError:
        return False


def read_gpu_mode():

    if _is_gl_provider_nvidia():
        return "nvidia"
    else:
        if _is_offloading_available():
            return "hybrid"
        else:
            return "intel"


def is_module_available(module_name):

    try:
        exec_bash("modinfo %s" % module_name)
    except BashError:
        return False
    else:
        return True


def is_module_loaded(module_name):

    try:
        exec_bash("lsmod | grep -E \"^%s \"" % module_name)
    except BashError:
        return False
    else:
        return True


def detect_os():
    return os.path.isdir("/run/runit/service")


def _detect_init_system(init):
    try:
        exec_bash("systemctl")
        return init == "systemd"
    except BashError:
        pass
    try:
        exec_bash("rc-status")
        return init == "openrc"
    except BashError:
        pass
    try:
        exec_bash("command -v sv")
        if detect_os():
            return init == "runit-artix"
        elif not detect_os():
            return init == "runit-void"
    except BashError:
        pass
    try:
        exec_bash("command -v s6-rc")
        return init == "s6"
    except BashError:
        pass
    return False


def get_current_display_manager():

    if not _detect_init_system(init="systemd"):
        return _get_openrc_display_manager()
    else:
        pass

    if not os.path.isfile("/etc/systemd/system/display-manager.service"):
        raise CheckError("No display-manager.service file found")

    dm_service_path = os.path.realpath("/etc/systemd/system/display-manager.service")
    dm_service_filename = os.path.split(dm_service_path)[-1]
    dm_name = os.path.splitext(dm_service_filename)[0]

    return dm_name


def _get_openrc_display_manager():

    if not _detect_init_system(init="openrc"):
        return using_patched_GDM()
    if not os.path.isfile("/etc/init.d/xdm"):
        raise CheckError("No xdm init script fle found")

    dm_service_path = os.path.realpath("/etc/init.d/xdm")
    dm_service_filename = os.path.split(dm_service_path)[-1]
    dm_name = os.path.splitext(dm_service_filename)[0]

    return dm_name


def using_patched_GDM():

    folder_path_1 = "/etc/gdm/Prime"
    folder_path_2 = "/etc/gdm3/Prime"

    return os.path.isdir(folder_path_1) or os.path.isdir(folder_path_2)


def _is_offloading_available():

    try:
        ret = exec_bash("xrandr --listproviders")
    except BashError as e:
        raise CheckError("Cannot list xrand providers : %s" % str(e))

    stdout = ret.stdout.decode('utf-8')[:-1]

    for line in stdout.splitlines():
        if re.search("^Provider [0-9]+:", line) and "name:NVIDIA-G0" in line:
            return True
    return False


def is_xorg_intel_module_available():
    return os.path.isfile("/usr/lib/xorg/modules/drivers/intel_drv.so")


def is_login_manager_active():
    return _is_service_active("display-manager")


def is_elogind_active():
    return _is_service_active("elogind")

def is_lxdm_active():
    return _is_service_active("lxdm")

def is_daemon_active():
    return _is_service_active("optimus-manager")


def is_bumblebeed_service_active():
    return _is_service_active("bumblebeed")


def _is_gl_provider_nvidia():

    try:
        ret = exec_bash("glxinfo")
    except BashError as e:
        raise CheckError("Cannot run glxinfo : %s" % str(e))

    stdout = ret.stdout.decode('utf-8')[:-1]

    for line in stdout.splitlines():
        if "server glx vendor string: NVIDIA Corporation" in line:
            return True
    return False


def _is_elogind_present():
    return os.path.isfile("/usr/lib/libelogind.so.0")


def _is_service_active(service_name):

    if _is_elogind_present():
        return _is_service_active_bash(service_name)
    else:
        pass

    try:
        system_bus = dbus.SystemBus()
    except dbus.exceptions.DBusException:
        print("WARNING : Cannot communicate with the DBus system bus to check status of %s."
              " Is DBus running ? Falling back to bash commands" % service_name)
        return _is_service_active_bash(service_name)
    else:
        return _is_service_active_dbus(system_bus, service_name)


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

    if _detect_init_system(init="systemd"):
        try:
            exec_bash("systemctl is-active %s" % service_name)
        except BashError:
            return False
        else:
            return True

    if _detect_init_system(init="openrc"):
        try:
            exec_bash("rc-service %s status" % service_name)
        except BashError:
            return False
        else:
            return True

    if _detect_init_system(init="runit"):
        try:
            exec_bash("sudo cat /var/service/%s/supervise/stat | grep run" % service_name)
        except BashError:
            return False
        else:
            return True

    if _detect_init_system(init="runit-void"):
        try:
            exec_bash("sudo cat /var/service/%s/supervise/stat | grep run" % service_name)
        except BashError:
            return False
        else:
            return True
            
    if _detect_init_system(init="runit-artix"):
        try:
            exec_bash("sudo cat /run/runit/service/%s/supervise/stat | grep run" % service_name)
        except BashError:
            return False
        else:
            return True
    
    if _detect_init_system(init="s6"):
        try:
            exec_bash("pstree | grep %s" % service_name)
        except BashError:
            return False
        else:
            return True




