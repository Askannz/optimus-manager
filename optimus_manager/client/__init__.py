#!/usr/bin/env python3
import sys
import os
import argparse
import socket
import json
from .. import envs
from .. import checks
from ..config import load_config, ConfigError
from ..kernel_parameters import get_kernel_parameters
from ..var import read_startup_mode, read_temp_conf_path_var, load_state, VarError
from ..xorg import cleanup_xorg_conf, is_there_a_default_xorg_conf_file, is_there_a_MHWD_file, set_DPI
from .. import sessions
from .args import parse_args
from .utils import ask_confirmation
from .error_reporting import report_errors
from .client_checks import run_switch_checks, _check_daemon_active


def main():

    args = parse_args()
    state = load_state()
    fatal = report_errors(state)

    config = _get_config()
    print("")

    if args.version:
        _print_version()
    elif args.print_startup:
        _print_startup_deperecation_and_exit()
    elif args.set_startup:
        _print_startup_mode(config)
    elif args.temp_config:
        _set_temp_config_and_exit(args.temp_config)
    elif args.unset_temp_config:
        _unset_temp_config_and_exit()
    elif args.cleanup:
        _cleanup_xorg_and_exit()

    else:

        if fatal:
            print("Cannot execute command because of previous errors.\n")
            return _check_daemon_active()

        if args.print_mode:
            _print_current_mode(state)
        elif args.print_next_mode:
            _print_next_mode(state)
        elif args.status:
            _print_status(config, state)
        elif args.switch:
            _gpu_switch(config, args.switch, args.no_confirm)
        else:
            print("Invalid arguments.")
            sys.exit(1)

    sys.exit(0)


def _gpu_switch(config, switch_mode, no_confirm):

    if switch_mode not in ["intel", "nvidia", "hybrid-intel", "hybrid-amd", "amd"]:
        print("Invalid mode : %s" % switch_mode)
        sys.exit(1)

    run_switch_checks(config, switch_mode)

    if config["optimus"]["auto_logout"] == "yes":

        if no_confirm:
            confirmation = True
        else:
            print("You are about to switch GPUs. This will forcibly close all graphical sessions"
                  " and all your applications WILL CLOSE.\n"
                  "(you can pass the --no-confirm option to disable this warning)\n"
                  "Continue ? (y/N)")
            
            confirmation = ask_confirmation()

        if confirmation:
            _send_switch_command(config, switch_mode)

    else:
        _send_switch_command(config, switch_mode)
        print("Please logout all graphical sessions then log back in to apply the change.")


def _send_switch_command(config, requested_mode):

    print("Switching to mode : %s" % requested_mode)
    command = {"type": "switch", "args": {"mode": requested_mode}}
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


def _print_current_mode(state):
    print("Current GPU mode : %s" % state["current_mode"])

def _print_next_mode(state):

    if state["type"] == "pending_pre_xorg_start":
        res_str = state["requested_mode"]
    else:
        res_str = "no change"

    print("GPU mode requested for next login : %s" % res_str)

def _print_startup_deperecation_and_exit():
    print(
        "The argument --set-startup is deprecated. Set startup_mode through the\n"
        "configuration file at %s instead" % envs.USER_CONFIG_PATH)
    sys.exit(1)


def _print_startup_mode(config):

    startup_mode = config["optimus"]["startup_mode"]
    kernel_parameters = get_kernel_parameters()

    print("The argument --set-startup is deprecated. Set startup_mode through the\n"
          "configuration file at %s instead." % envs.USER_CONFIG_PATH)
    print("GPU at startup : %s" % startup_mode)

    if kernel_parameters["startup_mode"] is not None:
        print(
            "\nNote : the startup mode for the current boot was set to \"%s\" with"
            " a kernel parameter. Kernel parameters override the value above.\n"
            % kernel_parameters["startup_mode"])


def _print_temp_config_path():

    try:
        path = read_temp_conf_path_var()
    except VarError:
        print("Temporary config path: no")
    else:
        print("Temporary config path: %s" % path)

def _print_status(config, state):

    _print_version()
    print("")
    _print_current_mode(state)
    _print_next_mode(state)
    _print_startup_mode(config)
    _print_temp_config_path()


def _get_switch_mode(state, switch_arg):

    if switch_arg not in ["auto", "intel", "amd", "nvidia", "hybrid-intel", "hybrid-amd"]:
        print("Invalid mode : %s" % switch_arg)
        sys.exit(1)

    if switch_arg == "auto":

        requested_mode = {
            "nvidia": "intel",
            "intel": "nvidia",
            "hybrid-intel": "intel",
            "hybrid-amd": "amd",
            "amd": "nvidia"
        }[state["current_mode"]]

        print("Switching to : %s" % requested_mode)

    else:
        requested_mode = switch_arg

    return requested_mode

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
            if checks.detect_os():
                print("Cannot connect to the UNIX socket at %s. Is optimus-manager-daemon running ?\n"
                    "\nYou can enable and start it by running this command as root :\n"
                    "ln -s /etc/runit/sv/optimus-manager /var/run/runit/service\n"
                    "sv u optimus-manager\n" % envs.SOCKET_PATH)
            elif not checks.detect_os():
                print("Cannot connect to the UNIX socket at %s. Is optimus-manager-daemon running ?\n"
                        "\nYou can enable and start it by running this command as root :\n"
                        "ln -s /etc/sv/optimus-manager /var/service\n"
                        "sv u optimus-manager\n" % envs.SOCKET_PATH)
        elif _detect_init_system(init="s6"):
            print("Cannot connect to the UNIX socket at %s. Is optimus-manager-daemon running ?\n"
                  "\nYou can enable and start it by running this command as root :\n"
                  "s6-rc-bundle-update add default optimus-manager\n"
                  "s6-rc -u change optimus-manager\n" % envs.SOCKET_PATH)
        sys.exit(1)

def _set_startup_and_exit(startup_arg):

    if startup_arg not in ["intel", "amd", "nvidia", "hybrid-intel", "hybrid-amd"]:
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
