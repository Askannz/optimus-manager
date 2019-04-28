#!/usr/bin/env python
import sys
import os
import argparse
import socket
import optimus_manager.envs as envs
import optimus_manager.checks as checks
from optimus_manager.config import load_config, ConfigError
from optimus_manager.var import read_requested_mode, read_startup_mode, VarError
from optimus_manager.xorg import cleanup_xorg_conf, is_there_a_default_xorg_conf_file, is_there_a_MHWD_file
from optimus_manager.sessions import logout_all_desktop_sessions, is_there_a_wayland_session, SessionsError


def main():

    # Arguments parsing
    parser = argparse.ArgumentParser(description="Client program for the Optimus Manager tool.\n"
                                                 "https://github.com/Askannz/optimus-manager")
    parser.add_argument('-v', '--version', action='store_true', help='Print version and exit.')

    parser.add_argument('--print-mode', action='store_true',
                        help="Print the GPU mode that your current desktop session is running on.")
    parser.add_argument('--print-next-mode', action='store_true',
                        help="Print the GPU mode that will be used the next time you log into your session.")
    parser.add_argument('--print-startup', action='store_true',
                        help="Print the GPU mode that will be used on startup.")

    parser.add_argument('--switch', metavar='MODE', action='store',
                        help="Set the GPU mode to MODE. You need to log out then log in to apply the change."
                             "Possible modes : intel, nvidia, auto (checks the current mode and switch to the other).")
    parser.add_argument('--set-startup', metavar='STARTUP_MODE', action='store',
                        help="Set the startup mode to STARTUP_MODE. Possible modes : "
                             "intel, nvidia, nvidia_once (starts with Nvidia and reverts to Intel for the next boot)")

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
        _print_version_and_exit()

    elif args.print_mode:
        _print_current_mode_and_exit()

    elif args.print_next_mode:
        _print_next_mode_and_exit()

    elif args.print_startup:
        _print_startup_mode_and_exit()

    elif args.switch:

        _check_daemon_active()

        switch_mode = _get_switch_mode(args.switch)

        _check_bbswitch_module(config)
        _check_nvidia_module(switch_mode)
        _check_patched_GDM()
        _check_wayland()
        _check_bumblebeed()
        _check_xorg_conf()
        _check_MHWD_conf()
        _check_intel_xorg_module(config, switch_mode)

        if args.no_confirm:
            _send_command(switch_mode)
            logout_all_desktop_sessions()
        else:
            print("You are about to switch GPUs. This will forcibly close all graphical sessions"
                  " and all your applications WILL CLOSE.\n"
                  "(you can pass the --no-confirm option to disable this warning)\n"
                  "Continue ? (y/N)")

            confirmation = _ask_confirmation()
            if confirmation:
                _send_command(switch_mode)
                logout_all_desktop_sessions()
            else:
                sys.exit(0)

        sys.exit(0)

    elif args.set_startup:
        _set_startup_and_exit(args.set_startup)

    elif args.cleanup:
        _cleanup_xorg_and_exit()

    else:
        print("Invalid arguments.")


def _get_config():

    try:
        config = load_config()
    except ConfigError as e:
        print("Error loading config file : %s" % str(e))
        sys.exit(1)

    return config


def _print_version_and_exit():

    print("Optimus Manager (Client) version %s" % envs.VERSION)
    sys.exit(0)


def _print_current_mode_and_exit():

    try:
        mode = checks.read_gpu_mode()
    except checks.CheckError as e:
        print("Error reading mode : %s" % str(e))
        sys.exit(1)

    print("Current GPU mode : %s" % mode)
    sys.exit(0)


def _print_next_mode_and_exit():

    try:
        requested_mode = read_requested_mode()
    except VarError as e:
        print("Error reading requested GPU mode : %s" % str(e))
        sys.exit(1)

    print("GPU mode requested for next login : %s" % requested_mode)
    sys.exit(0)


def _print_startup_mode_and_exit():

    try:
        startup_mode = read_startup_mode()
    except VarError as e:
        print("Error reading startup mode : %s" % str(e))
        sys.exit(1)

    print("Current startup GPU mode : %s" % startup_mode)
    sys.exit(0)


def _check_daemon_active():

    if not checks.is_daemon_active():
        print("The optimus-manager service is not running. Please enable and start it with :\n\n"
              "sudo systemctl enable optimus-manager\n"
              "sudo systemctl start optimus-manager\n")
        sys.exit(1)


def _get_switch_mode(switch_arg):

    if switch_arg not in ["auto", "intel", "nvidia"]:
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
        else:
            switch_mode = "nvidia"

        print("Switching to : %s" % switch_mode)

    else:
        switch_mode = switch_arg

    return switch_mode


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
        wayland_session_present = is_there_a_wayland_session()
    except SessionsError as e:
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
        print("WARNING : The Bumblebee service (bumblebeed.service) is running, and this can interfere with optimus-manager."
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
        print("WARNING : The Xorg driver \"intel\" is selected in the configuration file but this driver is not installed."
              " optimus-manager will default to the \"modesetting\" driver instead. You can install the \"intel\" driver from"
              " the package \"xf86-video-intel.\"\n"
              "Continue ? (y/N)")

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


def _send_command(cmd):

    try:
        client = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)
        client.connect(envs.SOCKET_PATH)
        client.send(cmd.encode('utf-8'))
        client.close()

    except (ConnectionRefusedError, OSError):
        print("Cannot connect to the UNIX socket at %s. Is optimus-manager-daemon running ?\n"
              "\nYou can enable and start it by running those commands as root :\n"
              "\nsystemctl enable optimus-manager.service\n"
              "systemctl start optimus-manager.service\n" % envs.SOCKET_PATH)
        sys.exit(1)


def _set_startup_and_exit(startup_arg):

    if startup_arg not in ["intel", "nvidia", "nvidia_once"]:
        print("Invalid startup mode : %s" % startup_arg)
        sys.exit(1)

    _send_command("startup_" + startup_arg)
    sys.exit(0)


def _cleanup_xorg_and_exit():

    if os.geteuid() != 0:
        print("You need to execute the command as root for this action.")
        sys.exit(1)

    cleanup_xorg_conf()
    sys.exit(0)


if __name__ == '__main__':
    main()
