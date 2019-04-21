#!/usr/bin/env python
import sys
import os
import signal
import argparse
import select
import socket
import optimus_manager.envs as envs
from optimus_manager.config import load_config, ConfigError
from optimus_manager.var import read_startup_mode, write_startup_mode, write_requested_mode, VarError
from optimus_manager.xorg import cleanup_xorg_conf
import optimus_manager.optimus_manager_setup as optimus_manager_setup


class SignalHandler:
    def __init__(self, server):
        self.server = server

    def handler(self, signum, frame):

        print("\nProcess stop requested")

        print("Closing and removing the socket...")
        self.server.close()
        os.remove(envs.SOCKET_PATH)

        print("Cleaning up Xorg conf...")
        cleanup_xorg_conf()

        print("Goodbye !")
        sys.exit(0)


def _write_gpu_mode(config, mode):

    try:
        print("Writing requested mode")
        write_requested_mode(mode)

    except VarError as e:
        print("Cannot write requested mode : %s" % str(e))


def _write_startup_mode(mode):

    try:
        write_startup_mode(mode)

    except VarError as e:
        print("Cannot write startup mode : %s" % str(e))


def main():

    # Arguments parsing
    parser = argparse.ArgumentParser(description="Daemon program for the Optimus Manager tool.\n"
                                                 "https://github.com/Askannz/optimus-manager")
    parser.parse_args()

    print("Optimus Manager (Daemon) version %s" % envs.VERSION)

    print("Cleaning up leftover Xorg conf")
    cleanup_xorg_conf()

    # Config
    print("Loading config file")
    try:
        config = load_config()
    except ConfigError as e:
        print("Error loading config file : %s" % str(e))

    # GPU setup at boot

    print("Initial GPU setup")

    try:
        startup_mode = read_startup_mode()
    except VarError as e:
        print("Cannot read startup mode : %s.\nUsing default startup mode %s instead." % (str(e), envs.DEFAULT_STARTUP_MODE))
        startup_mode = envs.DEFAULT_STARTUP_MODE

    _write_gpu_mode(config, startup_mode)

    optimus_manager_setup.main()

    # UNIX socket

    print("Opening UNIX socket")

    if os.path.exists(envs.SOCKET_PATH):
        print("Warning : the UNIX socket file %s already exists ! Either another "
              "daemon instance is running or the daemon was not exited gracefully "
              "last time.\nRemoving the file and moving on..." % envs.SOCKET_PATH)
        os.remove(envs.SOCKET_PATH)

    server = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)
    server.settimeout(envs.SOCKET_TIMEOUT)
    server.bind(envs.SOCKET_PATH)
    os.chmod(envs.SOCKET_PATH, 0o666)

    # Signal hander
    handler = SignalHandler(server)
    signal.signal(signal.SIGTERM, handler.handler)
    signal.signal(signal.SIGINT, handler.handler)

    print("Awaiting commands")
    while True:

        r, _, _ = select.select([server], [], [])
        datagram = server.recv(1024)
        msg = datagram.decode('utf-8')

        print("Received command : %s" % msg)

        # Switching
        if msg == "intel":
            _write_gpu_mode(config, "intel")
        elif msg == "nvidia":
            _write_gpu_mode(config, "nvidia")

        # Startup modes
        elif msg == "startup_nvidia":
            _write_startup_mode("nvidia")
        elif msg == "startup_intel":
            _write_startup_mode("intel")
        elif msg == "startup_nvidia_once":
            _write_startup_mode("nvidia_once")
        else:
            print("Invalid command !")


if __name__ == '__main__':
    main()
