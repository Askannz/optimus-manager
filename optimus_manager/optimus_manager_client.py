#!/usr/bin/env python3
import sys
import os
import argparse
import socket
import json
import optimus_manager.envs as envs
import optimus_manager.checks as checks
from optimus_manager.config import load_config, ConfigError
from optimus_manager.kernel_parameters import get_kernel_parameters
from optimus_manager.var import read_requested_mode, read_startup_mode, read_temp_conf_path_var, VarError
from optimus_manager.xorg import cleanup_xorg_conf, is_there_a_default_xorg_conf_file, is_there_a_MHWD_file
from optimus_manager.checks import _detect_init_system
import optimus_manager.sessions as sessions


def main():
    # Arguments parsing
    parser = argparse.ArgumentParser(description="Client program for the Optimus Manager tool.\n"
                                                 "https://github.com/Askannz/optimus-manager")
    parser.add_argument('-v', '--version', action='store_true', help='Print version and exit.')

    parser.add_argument('--status', action='store_true',
                        help="Print current status of optimus-manager")
    parser.add_argument('--print-mode', action='store_true',
                        help="Print the GPU mode that your current desktop session is running on.")
    parser.add_argument('--print-next-mode', action='store_true',
                        help="Print the GPU mode that will be used the next time you log into your session.")
    parser.add_argument('--print-startup', action='store_true',
                        help="Print the GPU mode that will be used on startup.")

    parser.add_argument('--switch', metavar='MODE', action='store',
                        help="Set the GPU mode to MODE. You need to log out then log in to apply the change."
                             "Possible modes : intel, nvidia, hybrid, auto (auto-detects the mode you may want to switch to).")
    parser.add_argument('--set-startup', metavar='STARTUP_MODE', action='store',
                        help="Set the startup mode to STARTUP_MODE. Possible modes : "
                             "intel, nvidia, hybrid")

    parser.add_argument('--temp-config', metavar='PATH', action='store',
                        help="Set a path to a temporary configuration file to use for the next reboot ONLY. Useful for testing"
                             " power switching configurations without ending up with an unbootable setup.")
    parser.add_argument('--unset-temp-config', action='store_true', help="Undo --temp-config (unset temp config path)")

    parser.add_argument('--no-confirm', action='store_true',
                        help="Do not ask for confirmation and skip all warnings when switching GPUs.")
    parser.add_argument('--cleanup', action='store_true',
                        help="Remove auto-generated configuration files left over by the daemon.")
    args = parser.parse_args()

    # Config loading
    config = _get_config()
    print("")  # Blank line to separate errors from config parsing

    #
    # Arguments switch

    if args.version:
        _print_version()
        sys.exit(0)

    elif args.print_mode:
        _print_current_mode()
        sys.exit(0)

    elif args.print_next_mode:
        _print_next_mode()
        sys.exit(0)

    elif args.print_startup:
        _print_startup_mode()
        sys.exit(0)

    elif args.status:
        _print_status()
        sys.exit(0)

    elif args.switch:

        _check_daemon_active()
        _check_elogind_active()

        switch_mode = _get_switch_mode(args.switch)

        _check_power_switching(config)
        _check_bbswitch_module(config)
        _check_nvidia_module(switch_mode)
        _check_patched_GDM()
        _check_wayland()
        _check_bumblebeed()
        _check_xorg_conf()
        _check_MHWD_conf()
        _check_intel_xorg_module(config, switch_mode)
        _check_number_of_sessions()

        if config["optimus"]["auto_logout"] == "yes":
            if args.no_confirm:
                gpu_switch(config, switch_mode)
            else:
                print("You are about to switch GPUs. This will forcibly close all graphical sessions"
                      " and all your applications WILL CLOSE.\n"
                      "(you can pass the --no-confirm option to disable this warning)\n"
                      "Continue ? (y/N)")

                confirmation = _ask_confirmation()
                if confirmation:
                    gpu_switch(config, switch_mode)
                else:
                    sys.exit(0)

        else:
            gpu_switch(config, switch_mode)
            print("Please logout all graphical sessions then log back in to apply the change.")

        sys.exit(0)

    elif args.set_startup:
        _set_startup_and_exit(args.set_startup)

    elif args.temp_config:
        _set_temp_config_and_exit(args.temp_config)

    elif args.unset_temp_config:
        _unset_temp_config_and_exit()

    elif args.cleanup:
        _cleanup_xorg_and_exit()

    else:
        print("Invalid arguments.")


def gpu_switch(config, switch_mode):
    print("Switching to mode : %s" % switch_mode)
    command = {"type": "switch", "args": {"mode": switch_mode}}
    _send_command(command)

    if config["optimus"]["auto_logout"] == "yes":
        sessions.logout_current_desktop_session()


def _get_config():
    try:
        config = load_config()
    except ConfigError as e:
        print("Error loading config file : %s" % str(e))
        sys.exit(1)

    return config


def _print_version():
    print("Optimus Manager (Client) version %s" % envs.VERSION)


def _print_current_mode():
    try:
        mode = checks.read_gpu_mode()
        print("Current GPU mode : %s" % mode)
    except checks.CheckError as e:
        print("Error reading current mode : %s" % str(e))


def _print_next_mode():
    try:
        requested_mode = read_requested_mode()
    except VarError as e:
        print("Error reading requested GPU mode : %s" % str(e))

    print("GPU mode requested for next login : %s" % requested_mode)


def _print_startup_mode():
    kernel_parameters = get_kernel_parameters()

    try:
        startup_mode = read_startup_mode()
    except VarError as e:
        print("Error reading startup mode : %s" % str(e))

    print("GPU mode for next startup : %s" % startup_mode)

    if kernel_parameters["startup_mode"] is not None:
        print("\nNote : the startup mode for the current boot was set to \"%s\" with"
              " a kernel parameter. Kernel parameters override the value above.\n" % kernel_parameters["startup_mode"])


def _print_temp_config_path():
    try:
        path = read_temp_conf_path_var()
    except VarError:
        print("Temporary config path: no")
    else:
        print("Temporary config path: %s" % path)


def _print_status():
    _print_version()
    print("")
    _print_current_mode()
    _print_next_mode()
    _print_startup_mode()
    _print_temp_config_path()


def _check_elogind_active():
    if not checks.is_elogind_active():
        if not _detect_init_system(init="systemd"):
            print("The Elogind service was not detected but is required to use optimus-manager, please install, enable and start it.")
        sys.exit(1)


def _check_daemon_active():
    if not checks.is_daemon_active():
        if _detect_init_system(init="openrc"):
            print("The optimus-manager service is not running. Please enable and start it with :\n\n"
                  "sudo rc-service enable optimus-manager\n"
                  "sudo rc-service start optimus-manager\n")
        elif _detect_init_system(init="runit"):
            print("The optimus-manager service is not running. Please enable and start it with :\n\n"
                  "sudo ln -s /etc/runit/run/sv/optimus-manager /var/run/runit\n"
                  "sudo sv u optimus-manager\n")
        elif _detect_init_system(init="systemd"):
            print("The optimus-manager service is not running. Please enable and start it with :\n\n"
                  "sudo systemctl enable optimus-manager\n"
                  "sudo systemctl start optimus-manager\n")
        else:
            print("ERROR: unsupported init system detected!")
        sys.exit(1)


def _get_switch_mode(switch_arg):
    if switch_arg not in ["auto", "intel", "nvidia", "hybrid"]:
        print("Invalid mode : %s" % switch_arg)
        sys.exit(1)

    if switch_arg == "auto":
        try:
            gpu_mode = checks.read_gpu_mode()
        except checks.CheckError as e:
            print("Error reading current GPU mode: %s" % str(e))
            sys.exit(1)

        if gpu_mode == "nvidia":
            switch_mode = "intel"
        elif gpu_mode == "intel":
            switch_mode = "nvidia"
        elif gpu_mode == "hybrid":
            switch_mode = "intel"

        print("Switching to : %s" % switch_mode)

    else:
        switch_mode = switch_arg

    return switch_mode


def _check_power_switching(config):
    if config["optimus"]["switching"] == "none" and config["optimus"]["pci_power_control"] == "no":
        print("WARNING : no power management option is currently enabled (this is the default since v1.2)."
              " Switching between GPUs will work but you will likely experience poor battery life.\n"
              "Follow instructions at https://github.com/Askannz/optimus-manager/wiki/A-guide--to-power-management-options"
              " to enable power management.\n"
              "If you have already enabled the new Runtime D3 power management inside the Nvidia driver (for Turing+ GPU + Coffee Lake+ CPU),"
              " you can safely ignore this warning.")


def _check_bbswitch_module(config):
    if config["optimus"]["switching"] == "bbswitch" and not checks.is_module_available("bbswitch"):
        print("WARNING : bbswitch is enabled in the configuration file but the bbswitch module does"
              " not seem to be available for the current kernel. Power switching will not work.\n"
              "You can install bbswitch for the default kernel with \"sudo pacman -S bbswitch\" or"
              " for all kernels with \"sudo pacman -S bbswitch-dkms\".\n")


def _check_nvidia_module(switch_mode):
    if switch_mode == "nvidia" and not checks.is_module_available("nvidia"):
        print("WARNING : the nvidia module does not seem to be available for the current kernel."
              " It is likely the Nvidia driver was not properly installed. GPU switching will probably fail,\n"
              " continue anyway ? (y/N)")

        confirmation = _ask_confirmation()

        if not confirmation:
            sys.exit(0)


def _check_wayland():
    try:
        wayland_session_present = sessions.is_there_a_wayland_session()
    except sessions.SessionsError as e:
        print("ERROR : cannot check for Wayland session : %s" % str(e))
        return

    if wayland_session_present:
        print("WARNING : there is at least one Wayland session running on this computer."
              " Wayland is not supported by this optimus-manager, so GPU switching may fail.\n"
              "Continue anyway ? (y/N)")

        confirmation = _ask_confirmation()

        if not confirmation:
            sys.exit(0)


def _check_xorg_conf():
    if is_there_a_default_xorg_conf_file():
        print("WARNING : Found a Xorg config file at /etc/X11/xorg.conf. If you did not"
              " create it yourself, it was likely generated by your distribution or by an Nvidia utility.\n"
              "This file may contain hard-coded GPU configuration that could interfere with optimus-manager,"
              " so it is recommended that you delete it before proceeding.\n"
              "Ignore this warning and proceed with GPU switching ? (y/N)")

        confirmation = _ask_confirmation()

        if not confirmation:
            sys.exit(0)


def _check_MHWD_conf():
    if is_there_a_MHWD_file():
        print("WARNING : Found a Xorg config file at /etc/X11/xorg.conf.d/90-mhwd.conf that was auto-generated"
              " by the Manjaro driver utility (MHWD). This will likely interfere with GPU switching, so"
              " optimus-manager will delete this file automatically if you proceded with GPU switching.\n"
              "Proceed ? (y/N)")

        confirmation = _ask_confirmation()

        if not confirmation:
            sys.exit(0)


def _check_bumblebeed():
    if checks.is_bumblebeed_service_active():
        print(
            "WARNING : The Bumblebee service (bumblebeed.service) is running, and this can interfere with optimus-manager."
            " Before attempting a GPU switch, it is recommended that you disable this service (sudo systemctl disable bumblebeed.service)"
            " then REBOOT your computer.\n"
            "Ignore this warning and proceed with GPU switching now ? (y/N)")

        confirmation = _ask_confirmation()

        if not confirmation:
            sys.exit(0)


def _check_patched_GDM():
    try:
        dm_name = checks.get_current_display_manager()
    except checks.CheckError as e:
        print("ERROR : cannot get current display manager name : %s" % str(e))
        return

    if dm_name == "gdm" and not checks.using_patched_GDM():
        print("WARNING : It does not seem like you are using a version of the Gnome Display Manager (GDM)"
              " that has been patched for Prime switching. Follow instructions at https://github.com/Askannz/optimus-manager"
              " to install a patched version. Without a patched GDM version, GPU switching will likely fail.\n"
              "Continue anyway ? (y/N)")

        confirmation = _ask_confirmation()

        if not confirmation:
            sys.exit(0)


def _check_intel_xorg_module(config, switch_mode):
    if switch_mode == "intel" and config["intel"]["driver"] == "intel" and not checks.is_xorg_intel_module_available():
        print(
            "WARNING : The Xorg driver \"intel\" is selected in the configuration file but this driver is not installed."
            " optimus-manager will default to the \"modesetting\" driver instead. You can install the \"intel\" driver from"
            " the package \"xf86-video-intel.\"\n"
            "Continue ? (y/N)")

        confirmation = _ask_confirmation()

        if not confirmation:
            sys.exit(0)


def _check_number_of_sessions():
    nb_desktop_sessions = sessions.get_number_of_desktop_sessions(ignore_gdm=True)

    if nb_desktop_sessions > 1:
        print(
            "WARNING : There are %d other desktop sessions open. The GPU switch will not become effective until you have manually"
            " logged out from ALL desktop sessions.\n"
            "Continue ? (y/N)" % (nb_desktop_sessions - 1))

        confirmation = _ask_confirmation()

        if not confirmation:
            sys.exit(0)


def _ask_confirmation():
    ans = input("> ").lower()

    if ans == "y":
        return True
    elif ans == "n" or ans == "N":
        print("Aborting.")
        return False
    else:
        print("Invalid choice. Aborting")
        return False


def _send_command(command):
    msg = json.dumps(command).encode('utf-8')

    try:
        client = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)
        client.connect(envs.SOCKET_PATH)
        client.send(msg)
        client.close()

    except (ConnectionRefusedError, OSError):
        if _detect_init_system(init="systemd"):
            print("Cannot connect to the UNIX socket at %s. Is optimus-manager-daemon running ?\n"
                  "\nYou can enable and start it by running those commands as root :\n"
                  "\nsystemctl enable optimus-manager.service\n"
                  "systemctl start optimus-manager.service\n" % envs.SOCKET_PATH)
        elif _detect_init_system(init="openrc"):
            print("Cannot connect to the UNIX socket at %s. Is optimus-manager-daemon running ?\n"
                  "\nYou can enable and start it by running those commands as root :\n"
                  "\nrc-update add optimus-manager default\n"
                  "rc-service optimus-manager start\n" % envs.SOCKET_PATH)
        elif _detect_init_system(init="runit"):
            print("Cannot connect to the UNIX socket at %s. Is optimus-manager-daemon running ?\n"
                  "\nYou can enable it by running this command as root :\n"
                  "sv u optimus-manager\n" % envs.SOCKET_PATH)
        sys.exit(1)


def _set_startup_and_exit(startup_arg):
    if startup_arg not in ["intel", "nvidia", "hybrid"]:
        print("Invalid startup mode : %s" % startup_arg)
        sys.exit(1)

    print("Setting startup mode to : %s" % startup_arg)
    command = {"type": "startup", "args": {"mode": startup_arg}}
    _send_command(command)
    sys.exit(0)


def _set_temp_config_and_exit(rel_path):
    abs_path = os.path.join(os.getcwd(), rel_path)

    if not os.path.isfile(abs_path):
        print("ERROR : no such config file : %s" % abs_path)
        sys.exit(1)

    print("Setting temp config file path to : %s" % abs_path)
    command = {"type": "temp_config", "args": {"path": abs_path}}
    _send_command(command)
    sys.exit(0)


def _unset_temp_config_and_exit():
    print("Unsetting temp config path")
    command = {"type": "temp_config", "args": {"path": ""}}
    _send_command(command)
    sys.exit(0)


def _cleanup_xorg_and_exit():
    if os.geteuid() != 0:
        print("You need to execute the command as root for this action.")
        sys.exit(1)

    cleanup_xorg_conf()
    sys.exit(0)


if __name__ == '__main__':
    main()
