#!/usr/bin/env python3
import sys
import os
import signal
import select
import socket
import optimus_manager.envs as envs
from optimus_manager.config import load_config, ConfigError
from optimus_manager.var import write_startup_mode, write_requested_mode, VarError
from optimus_manager.xorg import cleanup_xorg_conf
from optimus_manager.logging import crop_logs


def main():

    print("Optimus Manager (Daemon) version %s" % envs.VERSION)

    print("Automatic log cropping")
    crop_logs()

    print("Loading config file")
    config = _get_config()

    print("Opening UNIX socket")
    server_socket = _open_server_socket()

    _setup_signal_handler(server_socket)

    print("Awaiting commands")

    while True:

        msg = _wait_for_command(server_socket)
        print("Received command : %s" % msg)

        _process_command(config, msg)


def _get_config():

    try:
        config = load_config()
    except ConfigError as e:
        print("Error loading config file : %s" % str(e))
        sys.exit(1)

    return config


def _open_server_socket():

    if os.path.exists(envs.SOCKET_PATH):
        print("Warning : the UNIX socket file %s already exists ! Either another "
              "daemon instance is running or the daemon was not exited gracefully "
              "last time.\nRemoving the file and moving on..." % envs.SOCKET_PATH)
        os.remove(envs.SOCKET_PATH)

    server_socket = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)
    server_socket.settimeout(envs.SOCKET_TIMEOUT)
    server_socket.bind(envs.SOCKET_PATH)
    os.chmod(envs.SOCKET_PATH, 0o666)

    return server_socket


def _setup_signal_handler(server_socket):

    handler = _SignalHandler(server_socket)
    signal.signal(signal.SIGTERM, handler.handler)
    signal.signal(signal.SIGINT, handler.handler)


def _wait_for_command(server_socket):

    r, _, _ = select.select([server_socket], [], [])
    datagram = server_socket.recv(1024)
    msg = datagram.decode('utf-8')

    return msg


def _process_command(config, msg):

    # GPU switching
    if msg == "intel" or msg == "nvidia":
        _write_gpu_mode(config, msg)

    # Startup modes
    elif msg == "startup_nvidia":
        _write_startup_mode("nvidia")
    elif msg == "startup_intel":
        _write_startup_mode("intel")
    else:
        print("Invalid command !")


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


class _SignalHandler:
    def __init__(self, server_socket):
        self.server_socket = server_socket

    def handler(self, signum, frame):

        print("\nProcess stop requested")

        print("Closing and removing the socket...")
        self.server_socket.close()
        os.remove(envs.SOCKET_PATH)

        print("Cleaning up Xorg conf...")
        cleanup_xorg_conf()

        print("Goodbye !")
        sys.exit(0)


if __name__ == '__main__':
    main()
