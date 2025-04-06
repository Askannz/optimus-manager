import sys
from .. import var
from ..config import load_config
from ..kernel import get_available_modules, nvidia_power_up
from ..log_utils import get_logger, set_logger_config


def main():
    prev_state = var.load_state()

    if prev_state is None or prev_state["type"] != "done":
        return

    switch_id = prev_state["switch_id"]
    set_logger_config("switch", switch_id)
    logger = get_logger()
    current_mode = prev_state["current_mode"]

    try:
        logger.info("Running pre-suspend hook")
        logger.info("Previous state was: %s", str(prev_state))
        config = load_config()
        switching_option = config["optimus"]["switching"]
        logger.info("Switching option: %s", switching_option)

        if current_mode == "integrated":
            logger.info("Turning Nvidia GPU back on")
            available_modules = get_available_modules()
            nvidia_power_up(config, available_modules)

        state = {
            "type": "pending_post_resume",
            "switch_id": switch_id,
            "current_mode": current_mode
        }

        var.write_state(state)

    # pylint: disable=W0703
    except Exception:
        logger.exception("Pre-suspend hook failed")

        state = {
            "type": "pre_suspend_failed",
            "switch_id": switch_id,
            "current_mode": current_mode
        }

        var.write_state(state)
        sys.exit(1)

    else:
        logger.info("Pre-suspend hook completed")


if __name__ == "__main__":
    main()
