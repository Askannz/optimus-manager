import argparse


def parse_args():
    parser = argparse.ArgumentParser(description="optimus-manager client")

    parser.add_argument('-v', '--version', action='store_true', help='Prints the version')

    parser.add_argument('--status', action='store_true',
                        help="Prints the current status")

    parser.add_argument('--print-mode', action='store_true',
                        help="Prints the current GPU mode")

    parser.add_argument('--print-next-mode', action='store_true',
                        help="Prints the GPU mode that will be used on the next login")

    parser.add_argument('--print-startup', action='store_true',
                        help="Prints the GPU mode that will be used on startup")

    parser.add_argument('--switch', metavar='MODE', action='store',
                        help="Sets the GPU mode for future logins"
                             "Options: nvidia, integrated, hybrid")

    parser.add_argument('--temp-config', metavar='PATH', action='store',
                        help="Sets the temporary configuration file to use only on next boot")

    parser.add_argument('--unset-temp-config', action='store_true', help="Reverts --temp-config")

    parser.add_argument('--no-confirm', action='store_true',
                        help="Skips the confirmation for loggin out")

    parser.add_argument('--cleanup', action='store_true',
                        help="Removes auto-generated configuration files left over by the daemon")

    return parser.parse_args()
