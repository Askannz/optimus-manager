#!/usr/bin/env python
import sys
import argparse
import optimus_manager.envs as envs
from optimus_manager.config import load_config, ConfigError
from optimus_manager.var import read_startup_mode, read_requested_mode, write_requested_mode, VarError
from optimus_manager.prime import enable_PRIME
from optimus_manager.kernel import setup_kernel_state, KernelSetupError
from optimus_manager.xorg import configure_xorg, is_xorg_running, XorgSetupError


def main():

    parser = argparse.ArgumentParser(description="Display Manager setup service for the Optimus Manager tool.\n"
                                                 "https://github.com/Askannz/optimus-manager")
    parser.add_argument('--setup-boot', action='store_true')
    parser.add_argument('--setup-prime', action='store_true')
    parser.add_argument('--setup-gpu', action='store_true')

    args = parser.parse_args()

    print("Optimus Manager (GPU setup) version %s" % envs.VERSION)

    print("Loading config")
    config = _get_config()

    if args.setup_boot:
        print("Setting up boot")

        print("Reading startup mode")
        startup_mode = _get_startup_mode()
        print("Startup mode is : %s" % startup_mode)

        print("Writing startup mode to requested GPU mode")
        _write_gpu_mode(config, startup_mode)

        print("Initial GPU setup")
        _run_initial_gpu_setup(config, startup_mode)

    elif args.setup_prime:
        print("Setting up PRIME")
        enable_PRIME()

    elif args.setup_gpu:
        print("Setting up the GPU")
        requested_mode = _get_requested_mode()
        print("Requested mode :", requested_mode)
        _setup_gpu(config, requested_mode)


def _get_config():

    try:
        config = load_config()
    except ConfigError as e:
        print("Error loading config file : %s" % str(e))
        sys.exit(1)

    return config


def _get_startup_mode():

    try:
        startup_mode = read_startup_mode()
    except VarError as e:
        print("Cannot read startup mode : %s.\nUsing default startup mode %s instead." % (str(e), envs.DEFAULT_STARTUP_MODE))
        startup_mode = envs.DEFAULT_STARTUP_MODE

    return startup_mode


def _write_gpu_mode(config, mode):

    try:
        print("Writing requested mode")
        write_requested_mode(mode)

    except VarError as e:
        print("Cannot write requested mode : %s" % str(e))


def _run_initial_gpu_setup(config, requested_mode):

    if not is_xorg_running():
        _setup_gpu(config, requested_mode)
    else:
        print("Error : the daemon was started while a X server is already running ! Skipping initial GPU setup.")


def _get_requested_mode():

    try:
        requested_mode = read_requested_mode()
    except VarError as e:
        print("Cannot read requested mode : %s" % str(e))
        sys.exit(1)

    return requested_mode


def _setup_gpu(config, requested_mode):

    try:
        setup_kernel_state(config, requested_mode)
        configure_xorg(config, requested_mode)

    except KernelSetupError as e:
        print("Cannot setup GPU : kernel setup error : %s" % str(e))
        sys.exit(1)

    except XorgSetupError as e:
        print("Cannot setup GPU : Xorg setup error : %s" % str(e))
        sys.exit(1)


if __name__ == '__main__':
    main()
