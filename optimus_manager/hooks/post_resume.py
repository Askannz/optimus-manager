import sys
from .. import var
from ..config import load_config
from ..kernel import get_available_modules, nvidia_power_down
from ..log_utils import get_logger, set_logger_config


def main():
    prev_state = var.load_state()

    if prev_state is None or prev_state["type"] != "pending_post_resume":
        return

    switch_id = prev_state["switch_id"]
    set_logger_config("switch", switch_id)
    logger = get_logger()
    current_mode = prev_state["current_mode"]

    try:
        logger.info("Running post-resume hook")
        logger.info("Previous state was: %s", str(prev_state))
        config = load_config()
        switching_option = config["optimus"]["switching"]

        if current_mode == "integrated":
            logger.info("Turning Nvidia GPU off again")
            available_modules = get_available_modules()
            nvidia_power_down(config, available_modules)

        state = {
            "type": "done",
            "switch_id": switch_id,
            "current_mode": current_mode,
        }

        var.write_state(state)

    # pylint: disable=W0703
    except Exception:
        logger.exception("Post-resume hook failed")

        state = {
            "type": "post_resume_failed",
            "switch_id": switch_id,
            "current_mode": current_mode
        }

        var.write_state(state)
        sys.exit(1)

    else:
        logger.info("Post-resume hook completed")


if __name__ == "__main__":
    main()
