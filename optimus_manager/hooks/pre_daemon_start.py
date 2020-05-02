import sys
from ..config import load_config, copy_user_config
from .. import envs
from .. import var
from ..xorg import cleanup_xorg_conf
from ..checks import is_ac_power_connected
from ..log_utils import set_logger_config, get_logger


def main():

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
        config = load_config()

        try:
            startup_mode = var.get_startup_mode()
        except var.VarError as e:
            logger.warning(
                "Cannot read startup mode : %s.\n"
                "Using default startup mode %s instead.",
                str(e), envs.DEFAULT_STARTUP_MODE)
            startup_mode = envs.DEFAULT_STARTUP_MODE
            var.write_startup_mode(startup_mode)

        logger.info("Startup mode is: %s", startup_mode)

        if startup_mode == "ac_auto":
            ac_auto_battery_option = config["optimus"]["ac_auto_battery_mode"]
            startup_mode = "nvidia" if is_ac_power_connected() else ac_auto_battery_option
            logger.info("Effective mode is: %s", startup_mode)

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


if __name__ == "__main__":
    main()
