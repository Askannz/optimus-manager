import sys
import traceback
from ..config import load_config, copy_user_config
from ..kernel import setup_kernel_state
from .. import var
from ..xorg import configure_xorg, cleanup_xorg_conf, do_xsetup, set_DPI
from ..hacks.gdm import kill_gdm_server
from ..log_utils import set_logger_config, get_logger


def setup_pre_daemon_start():

    var.cleanup_tmp_vars()

    daemon_run_id = var.make_daemon_run_id()
    var.write_daemon_run_id(daemon_run_id)

    set_logger_config("daemon", daemon_run_id)
    logger = get_logger()

    startup_mode = None

    try:
        logger.info("# Daemon pre-start hook")

        cleanup_xorg_conf()
        copy_user_config()
        var.remove_last_acpi_call_state()
        startup_mode = var.get_startup_mode()

        logger.info("Startup mode is: %s", startup_mode)

        state = {
            "type": "pending_pre_xorg_start",
            "requested_mode": startup_mode,
            "current_mode": None
        }

        var.write_state(state)

    # pylint: disable=W0703
    except Exception:

        logger.exception("Daemon startup error")

        state = {
            "type": "startup_failed",
            "startup_mode": startup_mode,
            "daemon_run_id": daemon_run_id
        }

        var.write_state(state)
        sys.exit(1)

    else:
        logger.info("Daemon pre-start hook completed successfully.")
        logger.info("Calling Xorg pre-start hook.")


def setup_pre_xorg_start():

    prev_state = var.load_state()

    if prev_state is None or prev_state["type"] != "pending_pre_xorg_start":
        return

    switch_id = var.make_switch_id()

    set_logger_config("switch", switch_id)
    logger = get_logger()

    requested_mode = None

    try:
        logger.info("# Xorg pre-start hook")

        requested_mode = prev_state["requested_mode"]

        logger.info("Requested mode is: %s", requested_mode)

        kill_gdm_server()
        config = load_config()
        setup_kernel_state(config, prev_state, requested_mode)
        configure_xorg(config, requested_mode)

        state = {
            "type": "pending_post_xorg_start",
            "switch_id": switch_id,
            "requested_mode": requested_mode,
        }

        var.write_state(state)

    # pylint: disable=W0703
    except Exception:

        logger.exception("Xorg pre-start setup error")

        cleanup_xorg_conf()

        state = {
            "type": "pre_xorg_start_failed",
            "switch_id": switch_id,
            "requested_mode": requested_mode
        }

        var.write_state(state)
        sys.exit(1)

    else:
        logger.info("Xorg pre-start hook completed successfully.")


def setup_post_xorg_start():

    prev_state = var.load_state()

    if prev_state is None or prev_state["type"] != "pending_post_xorg_start":
        return

    switch_id = prev_state["switch_id"]

    set_logger_config("switch", switch_id)
    logger = get_logger()

    requested_mode = None

    try:
        logger.info("# Xorg post-start hook")

        requested_mode = prev_state["requested_mode"]

        do_xsetup(requested_mode)
        config = load_config()
        set_DPI(config)

        state = {
            "type": "done",
            "switch_id": switch_id,
            "current_mode": requested_mode
        }

        var.write_state(state)

    # pylint: disable=W0703
    except Exception:

        logger.exception("Xorg post-start setup error")

        state = {
            "type": "post_xorg_start_failed",
            "switch_id": switch_id,
            "requested_mode": requested_mode
        }

        var.write_state(state)
        sys.exit(1)

    else:
        logger.info("Xorg post-start hook completed successfully.")


def cleanup_post_daemon_stop():
    var.cleanup_tmp_vars()
