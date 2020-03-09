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
from ..var import read_startup_mode, read_temp_conf_path_var, VarError
from ..xorg import cleanup_xorg_conf, is_there_a_default_xorg_conf_file, is_there_a_MHWD_file
from .. import sessions
from .args import parse_args
from .utils import ask_confirmation
from .client_checks import run_switch_checks
from ..state import load_state


def main():

    args = parse_args()

    config = _get_config()
    print("")

    if args.version:
        _print_version()
    elif args.print_mode:
        _print_current_mode()
    elif args.print_next_mode:
        _print_next_mode()
    elif args.print_startup:
        _print_startup_mode()
    elif args.status:
        _print_status()
    elif args.switch:
        _gpu_switch(config, args.switch, args.no_confirm)
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
        sys.exit(1)

    sys.exit(0)


def _gpu_switch(config, switch_mode, no_confirm):


    switch_mode = _get_switch_mode(switch_mode)

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


def _send_switch_command(config, switch_mode):

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

    state = load_state()

    if state is not None and state["type"] == "pending_pre_xorg_start":
        res_str = state["requested_mode"]
    else:
        res_str = "no change"

    print("GPU mode requested for next login : %s" % res_str)


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

def _check_daemon_active():

    if not checks.is_daemon_active():
        print("The optimus-manager service is not running. Please enable and start it with :\n\n"
              "sudo systemctl enable optimus-manager\n"
              "sudo systemctl start optimus-manager\n")
        sys.exit(1)


def _get_switch_mode(switch_arg):

    if switch_arg not in ["auto", "intel", "nvidia", "hybrid", "ac_auto"]:
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

def _send_command(command):

    msg = json.dumps(command).encode('utf-8')

    try:
        client = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)
        client.connect(envs.SOCKET_PATH)
        client.send(msg)
        client.close()

    except (ConnectionRefusedError, OSError):
        print("Cannot connect to the UNIX socket at %s. Is optimus-manager-daemon running ?\n"
              "\nYou can enable and start it by running those commands as root :\n"
              "\nsystemctl enable optimus-manager.service\n"
              "systemctl start optimus-manager.service\n" % envs.SOCKET_PATH)
        sys.exit(1)


def _set_startup_and_exit(startup_arg):

    if startup_arg not in ["intel", "nvidia", "hybrid", "ac_auto"]:
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
