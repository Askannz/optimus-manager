#!/usr/bin/env python
import sys
import time
import argparse
import optimus_manager.envs as envs
from optimus_manager.config import load_config, ConfigError
from optimus_manager.var import read_startup_mode, write_startup_mode, read_requested_mode, remove_request_mode_var, VarError
from optimus_manager.switching import switch_to_intel, switch_to_nvidia, SwitchError
from optimus_manager.cleanup import clean_all
from optimus_manager.bash import exec_bash, BashError
import optimus_manager.checks as checks
import optimus_manager.pci as pci


def _wait_xorg_stop():

    POLL_TIME = 0.5
    TIMEOUT = 10.0

    t0 = time.time()
    t = t0
    while abs(t - t0) < TIMEOUT:
        if not checks.is_xorg_running():
            return True
        else:
            time.sleep(POLL_TIME)
            t = time.time()

    return False


def _terminate_sessions():

    print("Terminating X11 sessions")
    try:
        exec_bash("for session in $(loginctl list-sessions --no-legend | awk '{print $1}'); do "
                  "if loginctl show-session $session | grep -q x11; "
                  "then loginctl terminate-session $session; "
                  "fi; done;")

        exec_bash("for session in $(loginctl list-sessions --no-legend | awk '{print $1}'); do "
                  "if loginctl show-session $session | grep -q x11; "
                  "then loginctl kill-session $session -s SIGKILL; "
                  "fi; done;")
    except BashError:
        print("Cannot terminate user processes. Skipping ...")
        pass

    print("Stopping the remaining X servers")
    exec_bash("for pid in $(pidof X); do kill -9 $pid; done;")
    exec_bash("for pid in $(pidof Xorg); do kill -9 $pid; done;")


def main():

    # Arguments parsing
    parser = argparse.ArgumentParser(description="Display Manager setup service for the Optimus Manager tool.\n"
                                                 "https://github.com/Askannz/optimus-manager")
    parser.add_argument('--setup-start', action='store_true', help='Setup Optimus before the login manager starts.')
    parser.add_argument('--setup-stop', action='store_true', help='Cleanup Optimus after the login manager stops.')

    args = parser.parse_args()

    print("Optimus Manager (DM setup) version %s" % envs.VERSION)

    # Config
    try:
        config = load_config()
    except ConfigError as e:
        print("Error loading config file : %s" % str(e))
        sys.exit(1)

    if args.setup_start:

        print("Setting up Optimus configuration")

        # Cleanup
        clean_all()

        try:
            requested_mode = read_requested_mode()
        except VarError as e:

            print("Cannot read requested mode : %s.\nUsing startup mode instead." % str(e))

            try:
                startup_mode = read_startup_mode()
            except VarError as e:
                print("Cannot read startup mode : %s.\nUsing default startup mode %s instead." % (str(e), envs.DEFAULT_STARTUP_MODE))
                startup_mode = envs.DEFAULT_STARTUP_MODE

            print("Startup mode :", startup_mode)
            if startup_mode == "nvidia_once":
                requested_mode = "nvidia"
                write_startup_mode("intel")
            else:
                requested_mode = startup_mode

        # We are done reading the command
        remove_request_mode_var()

        print("Requested mode :", requested_mode)

        try:
            if requested_mode == "nvidia":
                switch_to_nvidia(config)
            elif requested_mode == "intel":
                switch_to_intel(config)
        except SwitchError as e:
            print("Cannot switch GPUS : %s" % str(e))
            sys.exit(0)

    elif args.setup_stop:

        print("Cleaning up Optimus configuration")
        clean_all()

        # Terminate X11 sessions and closing X servers
        _terminate_sessions()

        # Killing systemd-logind (there is a known bug causing it to keep ownership of the GPU
        # and prevents module unloading)
        try:
            exec_bash("pkill systemd-logind")
        except BashError:
            pass

        print("Waiting for Xorg servers to stop")
        stopped = _wait_xorg_stop()
        if not stopped:
            print("Cannot stop X servers !")
            sys.exit(1)

        # Unload all GPU modules
        print("Unloading kernel modules")
        try:
            exec_bash("modprobe -r nvidia_drm nvidia_modeset nvidia_uvm nvidia nouveau")
        except BashError as e:
            print("Cannot unload modules : %s" % str(e))
            sys.exit(1)

        # Reset the PCI device corresponding to the Nvidia GPU
        print("Resetting the GPU")
        if config["optimus"]["pci_reset"] == "yes":
            try:
                pci.reset_gpu()
            except pci.PCIError as e:
                print("Error resetting the PCI device : %s" % str(e))

    else:

        print("Invalid argument")


if __name__ == '__main__':
    main()
