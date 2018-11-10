#!/usr/bin/env python
import os
import socket
import optimus_manager.envs as envs
from optimus_manager.var import read_startup_mode, write_startup_mode, VarError
from optimus_manager.switching import switch_to_intel, switch_to_nvidia
from optimus_manager.bash import exec_bash


def main():

    # Startup
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
        switch_to_nvidia()
    elif startup_mode == "nvidia":
        switch_to_nvidia()
    elif startup_mode == "intel":
        switch_to_intel()

    # UNIX socket
    server = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)
    server.bind(envs.SOCKET_PATH)
    os.chmod(envs.SOCKET_PATH, 0o666)

    while True:

        datagram = server.recv(1024)
        msg = datagram.decode('utf-8')

        if msg not in ["intel", "nvidia"]:
            print("Invalid command received !")

        else:

            ret = exec_bash("systemctl stop sddm")

            if msg == "intel":
                switch_to_intel()
            elif msg == "nvidia":
                switch_to_nvidia()

            ret = exec_bash("systemctl restart sddm")

    server.close()


if __name__ == '__main__':
    main()
