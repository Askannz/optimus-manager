#!/usr/bin/env python
import sys
import os
import signal
import argparse
import select
import socket
import optimus_manager.envs as envs
from optimus_manager.config import load_config
from optimus_manager.var import write_startup_mode, write_requested_mode, VarError
from optimus_manager.login_managers import restart_login_manager, LoginManagerError


class SignalHandler:
    def __init__(self, server):
        self.server = server

    def handler(self, signum, frame):
        print("\nProcess stop requested")
        print("Closing and removing the socket...")
        self.server.close()
        os.remove(envs.SOCKET_PATH)
        print("Goodbye !")
        sys.exit(0)


def gpu_switch(config, mode):

    try:
        print("Writing requested mode")
        write_requested_mode(mode)
        print("Restarting login manager")
        restart_login_manager(config)

    except VarError as e:
        print("Cannot write requested mode : %s" % str(e))

    except LoginManagerError as e:
        print("Cannot restart login manager : %s" % str(e))


def set_startup(mode):

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

    # Config
    config = load_config()

    # UNIX socket

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
            gpu_switch(config, "intel")
        elif msg == "nvidia":
            gpu_switch(config, "nvidia")

        # Startup modes
        elif msg == "startup_nvidia":
            set_startup("nvidia")
        elif msg == "startup_intel":
            set_startup("intel")
        elif msg == "startup_nvidia_once":
            set_startup("nvidia_once")
        else:
            print("Invalid command !")


if __name__ == '__main__':
    main()
