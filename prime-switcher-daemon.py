#!/usr/bin/env python
import os
import socket
from switching import switch_to_intel, switch_to_nvidia
from bash import exec_bash

SOCKET_PATH = "/tmp/prime-switcher"


def main():

    server = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)
    server.bind(SOCKET_PATH)
    os.chmod(SOCKET_PATH, 0o666)

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
