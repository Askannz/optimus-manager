#! /usr/bin/env python3
import json
import os
import select
import signal
import socket
import sys
from . import envs
from . import var
from .log_utils import get_logger, set_logger_config


def main():
    daemon_run_id = var.load_daemon_run_id()
    no_id = False

    if daemon_run_id is None:
        no_id = True
        daemon_run_id = var.make_daemon_run_id()
        var.write_daemon_run_id(daemon_run_id)

    set_logger_config("daemon", daemon_run_id)
    logger = get_logger()

    try:
        logger.info("Starting daemon")

        if no_id:
            logger.warning(
                "Created a new daemon ID: The daemon pre-start hook failed to do so")

        server_socket = _open_server_socket(logger)
        _setup_signal_handler(logger, server_socket)
        logger.info("Ready to receive commands")

        while True:
            msg = _wait_for_command(server_socket)
            logger.info("Received command: %s", msg)
            _process_command(logger, msg)

    # pylint: disable=W0703
    except Exception:
        logger.exception("Daemon crashed")


def _open_server_socket(logger):
    if os.path.exists(envs.SOCKET_PATH):
        logger.warning("Overwriting existing socket: %s" % envs.SOCKET_PATH)
        os.remove(envs.SOCKET_PATH)

    server_socket = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)
    server_socket.settimeout(envs.SOCKET_TIMEOUT)
    server_socket.bind(envs.SOCKET_PATH)
    os.chmod(envs.SOCKET_PATH, 0o666)
    return server_socket


def _setup_signal_handler(logger, server_socket):
    handler = _SignalHandler(logger, server_socket)
    signal.signal(signal.SIGTERM, handler.handler)
    signal.signal(signal.SIGINT, handler.handler)


def _wait_for_command(server_socket):
    select.select([server_socket], [], [])
    datagram = server_socket.recv(1024)
    msg = datagram.decode('utf-8')
    return msg


def _process_command(logger, msg):
    try:
        command = json.loads(msg)
    except json.decoder.JSONDecodeError:
        logger.error("JSON decode failed: Invalid command: %s" % msg)
        return

    try:
        if command["type"] == "switch":
            mode = command["args"]["mode"]
            logger.info("Writing requested GPU mode: %s" % mode)
            state = var.load_state()

            if state is None:
                logger.error("Unable to switch: State file doesn't exist")
                return

            new_state = {
                "type": "pending_pre_xorg_start",
                "requested_mode": mode,
                "current_mode": state["current_mode"]
            }

            var.write_state(new_state)

        elif command["type"] == "temp_config":
            if command["args"]["path"] == "":
                logger.info("Removing temporary config file")
                var.remove_temp_conf_path_var()
            else:
                logger.info("Writing temporary config file: %s" % command["args"]["path"])
                var.write_temp_conf_path_var(command["args"]["path"])

        elif command["type"] == "user_config":
            _replace_user_config(logger, command["args"]["content"])

        else:
            logger.error("Unkown command type: %s: %s" % (command["type"], msg))

    except KeyError as error:
        logger.error("Invalid command key: %s: %s" % (str(error), msg))


def _replace_user_config(logger, config_content):
    logger.info("Replacing user config at: %s" % envs.USER_CONFIG_PATH)

    with open(envs.USER_CONFIG_PATH, "w") as f:
        f.write(config_content)


class _SignalHandler:
    def __init__(self, logger, server_socket):
        self.logger = logger
        self.server_socket = server_socket

    def handler(self, signum, frame):
        #pylint: disable=unused-argument
        self.logger.info("Stopping daemon...")
        self.server_socket.close()
        os.remove(envs.SOCKET_PATH)
        self.logger.info("Stopped")
        sys.exit(0)


if __name__ == '__main__':
    main()
