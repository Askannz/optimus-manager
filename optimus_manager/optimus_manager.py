#!/usr/bin/env python
import sys
import socket

SOCKET_PATH = "/tmp/optimus-manager"


def main():

    if len(sys.argv) < 2:
        print("Please specify intel or nvidia.")
        sys.exit(1)

    mode = sys.argv[1]
    if mode not in ["intel", "nvidia"]:
        print("Invalid mode selected :", mode)
        sys.exit(1)

    client = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)
    client.connect(SOCKET_PATH)
    client.send(mode.encode('utf-8'))
    client.close()


if __name__ == '__main__':
    main()
