#! /usr/bin/env python3
import argparse
import json
import os
import socket
import sys
from .args import parse_args
from .error_reporting import report_errors
from .client_checks import run_switch_checks
from .. import checks
from .. import envs
from .. import sessions
from ..config import load_config, ConfigError
from ..kernel_parameters import get_kernel_parameters
from ..var import read_temp_conf_path_var, load_state, VarError
from ..xorg import cleanup_xorg_conf


def main():
    args = parse_args()
    state = load_state()
    fatal = report_errors(state)
    config = _get_config()

    if args.version:
        _print_version()

    elif args.print_startup:
        _print_startup_mode(config)

    elif args.temp_config:
        _set_temp_config_and_exit(args.temp_config)

    elif args.unset_temp_config:
        _unset_temp_config_and_exit()

    elif args.cleanup:
        _cleanup_xorg_and_exit()

    else:
        if fatal:
            sys.exit(1)

        elif args.print_mode:
            _print_current_mode(state)

        elif args.print_next_mode:
            _print_next_mode(state)

        elif args.status:
            _print_status(config, state)

        elif args.switch:
            _gpu_switch(config, args.switch, args.no_confirm)

        else:
            print("Invalid arguments")
            sys.exit(1)

    sys.exit(0)


def _ask_confirmation():
    ans = input("> ").lower()

    if ans == "y":
        return True

    else:
        if ans != "n":
            print("Invalid choice")

        print("Canceled")
        return False


def _gpu_switch(config, switch_mode, no_confirm):
    if switch_mode not in ["integrated", "nvidia", "hybrid", "intel"]:
        print("Invalid mode: %s" % switch_mode)
        sys.exit(1)

    if switch_mode == "intel":
        switch_mode = "integrated"

    run_switch_checks(config, switch_mode)

    if config["optimus"]["auto_logout"] == "yes":
        if no_confirm:
            confirmation = True

        else:
            print("This will close all desktops and applications\n"
                  "(Disable this warning with: --no-confirm)\n"
                  "Continue? (y/N)")
            confirmation = _ask_confirmation()

        if confirmation:
            _send_switch_command(config, switch_mode)

        else:
            sys.exit(1)

    else:
        _send_switch_command(config, switch_mode)
        print("The change will apply on next login")


def _send_switch_command(config, requested_mode):
    print("Switching to mode : %s" % requested_mode)
    command = {"type": "switch", "args": {"mode": requested_mode}}
    _send_command(command)

    if config["optimus"]["auto_logout"] == "yes":
        sessions.logout_current_desktop_session()


def _get_config():
    try:
        config = load_config()

    except ConfigError as error:
        print("Error loading config file: %s" % str(error))
        sys.exit(1)

    return config


def _print_version():
    print("Version: %s" % envs.VERSION)


def _print_current_mode(state):
    print("Current mode: %s" % state["current_mode"])


def _print_next_mode(state):
    if state["type"] == "pending_pre_xorg_start":
        res_str = state["requested_mode"]

    else:
        res_str = "Current"

    print("Mode for next login: %s" % res_str)


def _print_startup_mode(config):
    startup_mode = config["optimus"]["startup_mode"]
    kernel_parameters = get_kernel_parameters()

    print("Startup mode: %s" % startup_mode)

    if kernel_parameters["startup_mode"] is not None:
        print("Startup mode overriden by kernel parameter: %s"
            % kernel_parameters["startup_mode"])


def _print_temp_config_path():
    try:
        path = read_temp_conf_path_var()

    except VarError:
        print("Temporary config: None")

    else:
        print("Temporary config: %s" % path)


def _print_status(config, state):
    _print_version()
    print("")
    _print_current_mode(state)
    _print_next_mode(state)
    _print_startup_mode(config)
    _print_temp_config_path()


def _send_command(command):
    msg = json.dumps(command).encode('utf-8')

    try:
        client = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)
        client.connect(envs.SOCKET_PATH)
        client.send(msg)
        client.close()

    except (ConnectionRefusedError, OSError):
        print("Socket unavailable: %s" % envs.SOCKET_PATH)
        sys.exit(1)


def _set_temp_config_and_exit(rel_path):
    abs_path = os.path.join(os.getcwd(), rel_path)

    if not os.path.isfile(abs_path):
        print("Temp config file doesn't exist: %s" % abs_path)
        sys.exit(1)

    print("Temp config file: %s" % abs_path)
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
        print("Not root")
        sys.exit(1)

    cleanup_xorg_conf()
    sys.exit(0)


if __name__ == '__main__':
    main()
