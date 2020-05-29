import sys
from ..config import load_config
from ..kernel import setup_kernel_state
from .. import var
from ..xorg import configure_xorg, cleanup_xorg_conf
from ..hacks.gdm import kill_gdm_server, restart_gdm_server
from ..log_utils import set_logger_config, get_logger


def main():

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
        restart_gdm_server()

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


if __name__ == "__main__":
    main()
