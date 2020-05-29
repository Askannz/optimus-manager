import argparse


def parse_args():

    parser = argparse.ArgumentParser(description="Client program for optimus-manager.\n"
                                                 "https://github.com/Askannz/optimus-manager")
    parser.add_argument('-v', '--version', action='store_true', help='Print version and exit.')

    parser.add_argument('--status', action='store_true',
                        help="Print current status of optimus-manager")
    parser.add_argument('--print-mode', action='store_true',
                        help="Print the GPU mode that your current desktop session is running on.")
    parser.add_argument('--print-next-mode', action='store_true',
                        help="Print the GPU mode that will be used the next time you log into your session.")
    parser.add_argument('--print-startup', action='store_true',
                        help="Print the GPU mode that will be used on startup.")

    parser.add_argument('--switch', metavar='MODE', action='store',
                        help="Set the GPU mode to MODE. You need to log out then log in to apply the change."
                             "Possible modes : igpu, nvidia, amd, hybrid")
    parser.add_argument('--set-startup', metavar='STARTUP_MODE', action='store',
                        help="Deprecated argument. Set the startup mode through the configuration file instead.")

    parser.add_argument('--temp-config', metavar='PATH', action='store',
                        help="Set a path to a temporary configuration file to use for the next reboot ONLY. Useful for testing"
                             " power switching configurations without ending up with an unbootable setup.")
    parser.add_argument('--unset-temp-config', action='store_true', help="Undo --temp-config (unset temp config path)")


    parser.add_argument('--no-confirm', action='store_true',
                        help="Do not ask for confirmation and skip all warnings when switching GPUs.")
    parser.add_argument('--cleanup', action='store_true',
                        help="Remove auto-generated configuration files left over by the daemon.")

    return parser.parse_args()
