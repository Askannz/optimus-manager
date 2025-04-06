import os
import sys
from .. import var
from ..config import load_config
from ..kernel import setup_kernel_state
from ..log_utils import get_logger, set_logger_config
from ..xorg import cleanup_xorg_conf, configure_xorg, is_xorg_running


def main():
    prev_state = var.load_state()

    if prev_state is None:
        return

    elif prev_state["type"] == "pending_pre_xorg_start":
        switch_id = var.make_switch_id()
        setup_kernel = True
        requested_mode = prev_state["requested_mode"]

    elif prev_state["type"] == "done":
        switch_id = prev_state["switch_id"]
        setup_kernel = False
        requested_mode = prev_state["current_mode"]

    else:
        return

    set_logger_config("switch", switch_id)
    logger = get_logger()

    try:
        if os.environ.get("RUNNING_UNDER_GDM", False) and is_xorg_running():
            sys.exit(0)

        logger.info("Running Xorg pre-start hook")
        logger.info("Previous state was: %s", str(prev_state))
        logger.info("Requested mode is: %s", requested_mode)
        config = load_config()

        if setup_kernel:
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
        logger.exception("Xorg pre-start hook failed")
        cleanup_xorg_conf()

        state = {
            "type": "pre_xorg_start_failed",
            "switch_id": switch_id,
            "requested_mode": requested_mode
        }

        var.write_state(state)
        sys.exit(1)

    else:
        logger.info("Xorg pre-start hook completed")


if __name__ == "__main__":
    main()
