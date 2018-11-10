#!/usr/bin/env python
import os
import argparse
import socket
import optimus_manager.envs as envs
from optimus_manager.config import load_config
from optimus_manager.var import read_startup_mode, write_startup_mode, VarError
from optimus_manager.switching import switch_to_intel, switch_to_nvidia, SwitchError
from optimus_manager.bash import exec_bash


def gpu_switch(config, mode):

    ret = exec_bash("systemctl stop display-manager")
    if ret != 0:
        print("Warning : cannot stop login manager. Continuing...")

    try:
        if mode == "intel":
            switch_to_intel(config)
        elif mode == "nvidia":
            switch_to_nvidia(config)

        ret = exec_bash("systemctl restart display-manager")
        if ret != 0:
            print("Warning : cannot restart login manager.")

    except SwitchError as e:
        print("Cannot switch GPU : %s" % str(e))


def main():

    # Arguments parsing
    parser = argparse.ArgumentParser()
    parser.add_argument('--startup', action='store_true', help='Startup mode (configure GPU when daemon starts).')
    args = parser.parse_args()

    # Config
    config = load_config()

    # Startup
    if args.startup:

        try:
            startup_mode = read_startup_mode()
        except VarError as e:
            print("Cannot read startup mode : %s" % str(e))
            print("Overwriting with %s" % envs.DEFAULT_STARTUP_MODE)
            write_startup_mode(envs.DEFAULT_STARTUP_MODE)
            startup_mode = envs.DEFAULT_STARTUP_MODE

        print("Startup mode :", startup_mode)
        if startup_mode == "inactive":
            pass
        if startup_mode == "nvidia_once":
            write_startup_mode("intel")
            switch_to_nvidia(config)
        elif startup_mode == "nvidia":
            switch_to_nvidia(config)
        elif startup_mode == "intel":
            switch_to_intel(config)

    # UNIX socket
    server = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)
    server.bind(envs.SOCKET_PATH)
    os.chmod(envs.SOCKET_PATH, 0o666)

    while True:

        datagram = server.recv(1024)
        msg = datagram.decode('utf-8')

        if msg not in ["intel", "nvidia", "startup_inactive", "startup_nvidia_once",
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
                elif msg == "startup_inactive":
                    write_startup_mode("inactive")
                elif msg == "startup_nvidia_once":
                    write_startup_mode("nvidia_once")
                elif msg == "startup_nvidia":
                    write_startup_mode("nvidia")
                elif msg == "startup_intel":
                    write_startup_mode("intel")

            except SwitchError as e:

                print("Cannot switch GPU : %s" % str(e))

    server.close()


if __name__ == '__main__':
    main()
