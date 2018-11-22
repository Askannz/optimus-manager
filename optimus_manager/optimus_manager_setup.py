#!/usr/bin/env python
import sys
import argparse
import optimus_manager.envs as envs
from optimus_manager.config import load_config
from optimus_manager.var import read_startup_mode, write_startup_mode, read_requested_mode, remove_request_mode_var, VarError
from optimus_manager.switching import switch_to_intel, switch_to_nvidia, SwitchError
from optimus_manager.checks import is_xorg_running
from optimus_manager.cleanup import clean_all


def main():

    # Arguments parsing
    parser = argparse.ArgumentParser(description="Display Manager setup service for the Optimus Manager tool.\n"
                                                 "https://github.com/Askannz/optimus-manager")
    parser.add_argument('--setup-start', action='store_true', help='Setup Optimus before the login manager starts.')
    parser.add_argument('--setup-stop', action='store_true', help='Cleanup Optimus after the login manager stops.')

    args = parser.parse_args()

    print("Optimus Manager (DM setup service) version %s" % envs.VERSION)

    if args.setup_start:

        print("Setting up Optimus configuration")

        # Config
        config = load_config()

        if not is_xorg_running():

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

        else:

            print("Xorg server is already running, aborting setup !")

    elif args.setup_stop:

        print("Cleaning up Optimus configuration")
        clean_all()

    else:

        print("Invalid argument")


if __name__ == '__main__':
    main()
