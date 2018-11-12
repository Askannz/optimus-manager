#!/usr/bin/env python
import sys
import os
import signal
import argparse
import select
import socket
import optimus_manager.envs as envs
from optimus_manager.config import load_config
from optimus_manager.var import read_startup_mode, write_startup_mode, VarError
from optimus_manager.switching import switch_to_intel, switch_to_nvidia, SwitchError
from optimus_manager.login_managers import stop_login_manager, restart_login_manager


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

    print("Stopping login manager")
    stop_login_manager(config)

    try:
        if mode == "intel":
            switch_to_intel(config)
        elif mode == "nvidia":
            switch_to_nvidia(config)

        print("Restarting login manager")
        restart_login_manager(config)

    except SwitchError as e:
        print("Cannot switch GPU : %s" % str(e))


def main():

    # Arguments parsing
    parser = argparse.ArgumentParser(description="Daemon program for the Optimus Manager tool.\n"
                                                 "https://github.com/Askannz/optimus-manager")
    parser.add_argument('--startup', action='store_true', help='Startup mode (configure GPU when daemon starts).')
    args = parser.parse_args()

    print("Optimus Manager (Daemon) version %s" % envs.VERSION)

    # Config
    config = load_config()

    # Startup
    if args.startup:

        try:
            startup_mode = read_startup_mode()
        except VarError as e:
            print("ERROR : Cannot read startup mode : %s" % str(e))
            print("Defaulting to %s" % envs.DEFAULT_STARTUP_MODE)
            startup_mode = envs.DEFAULT_STARTUP_MODE

        print("Startup mode :", startup_mode)
        if startup_mode == "nvidia_once":
            write_startup_mode("intel")
            switch_to_nvidia(config)
        elif startup_mode == "nvidia":
            switch_to_nvidia(config)
        elif startup_mode == "intel":
            switch_to_intel(config)

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
        print("Receiving")
        datagram = server.recv(1024)
        msg = datagram.decode('utf-8')

        if msg not in ["intel", "nvidia", "startup_nvidia_once",
                       "startup_nvidia", "startup_intel"]:
            print("Invalid command received !")

        else:

            try:
                # Switching
                if msg == "intel":
                    gpu_switch(config, "intel")
                elif msg == "nvidia":
                    gpu_switch(config, "nvidia")

                # Startup modes
                if msg == "startup_nvidia_once":
                    write_startup_mode("nvidia_once")
                elif msg == "startup_nvidia":
                    write_startup_mode("nvidia")
                elif msg == "startup_intel":
                    write_startup_mode("intel")

            except SwitchError as e:

                print("Cannot switch GPU : %s" % str(e))


if __name__ == '__main__':
    main()
