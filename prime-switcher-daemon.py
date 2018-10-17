#!/usr/bin/env python
import os
import socket
from switching import switch_to_intel, switch_to_nvidia
from bash import exec_bash
import envs


def main():

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
