#!/usr/bin/env python
import sys
import argparse
import socket
import optimus_manager.envs as envs


def send_command(cmd):

    try:
        client = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)
        client.connect(envs.SOCKET_PATH)
        client.send(cmd.encode('utf-8'))
        client.close()

    except ConnectionRefusedError:
        print("Cannot connect to the UNIX socket at %s. Is optimus-manager-daemon running ?" % envs.SOCKET_PATH)
        sys.exit(1)


def main():

    # Arguments parsing
    parser = argparse.ArgumentParser()
    parser.add_argument('--switch', metavar='MODE', action='store',
                        help="Set the GPU mode to MODE (\"intel\" or \"nvidia\") and restart the display manager."
                             "WARNING : All your applications will close ! Be sure to save your work.")
    parser.add_argument('--set-startup', metavar='STARTUP_MODE', action='store',
                        help="Set the startup mode to STARTUP_MODE. Possible modes : "
                             "intel, nvidia, nvidia_once (starts with Nvidia and reverts to Intel for the next boot")
    args = parser.parse_args()

    if args.switch:

        if args.switch not in ["intel", "nvidia"]:
            print("Invalid mode : %s" % args.switch)
            sys.exit(1)

        send_command(args.switch)

    if args.set_startup:

        if args.set_startup not in ["intel", "nvidia", "nvidia_once"]:
            print("Invalid startup mode : %s" % args.set_startup)
            sys.exit(1)

        send_command(args.set_startup)


if __name__ == '__main__':
    main()
