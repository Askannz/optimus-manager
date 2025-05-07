import argparse


def parse_args():
    parser = argparse.ArgumentParser(description="optimus-manager client")

    # SWITCHING OPTIONS

    parser.add_argument('--switch', metavar='MODE', action='store',
                        help="Sets the GPU mode for future logins"
                             "Options: nvidia, integrated, hybrid")

    parser.add_argument('--no-confirm', '--now', action='store_true',
                        help="Skips the confirmation for loggin out")

    # PRINT OPTIONS

    parser.add_argument('--status', action='store_true',
                        help="Prints the current status")

    parser.add_argument('--print-mode', '--current-mode', action='store_true',
                        help="Prints the current GPU mode")

    parser.add_argument('--print-next-mode', '--next-mode', action='store_true',
                        help="Prints the GPU mode that will be used on the next login")

    parser.add_argument('--print-startup', '--startup-mode', action='store_true',
                        help="Prints the GPU mode that will be used on startup")

    parser.add_argument('-v', '--version', action='store_true',
                        help='Prints the version')

    # CONFIG OPTIONS

    parser.add_argument('--temp-config', '--config', metavar='PATH', action='store',
                        help="Sets the temporary configuration file to use only on next boot")

    parser.add_argument('--unset-temp-config', '--unset-config', action='store_true',
                        help="Reverts \"--config\"")

    parser.add_argument('--cleanup', action='store_true',
                        help="Removes auto-generated configuration files left over by the daemon")

    return parser.parse_args()
