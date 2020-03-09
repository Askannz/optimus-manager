from .config import load_config, copy_user_config
from .kernel import setup_kernel_state
from .var import remove_last_acpi_call_state
from .xorg import configure_xorg, cleanup_xorg_conf, do_xsetup, set_DPI
from .gdm import kill_gdm_server
from .utils import get_startup_mode
from .state import make_attempt_id, write_state, load_state


def setup_pre_daemon_start():

    try:
        cleanup_xorg_conf()
        copy_user_config()
        remove_last_acpi_call_state()
        startup_mode = get_startup_mode()

    except Exception:

        state = {
            "type": "startup_failed",
            "startup_mode": startup_mode
        }

        write_state(state)

    else:

        state = {
            "type": "pending_pre_xorg_start",
            "requested_mode": startup_mode
        }

        write_state(state)
        setup_pre_xorg_start()


def setup_pre_xorg_start():

    attempt_id = make_attempt_id()

    try:
        prev_state = load_state()

        if prev_state["type"] == "pending_pre_xorg_start":

            requested_mode = prev_state["requested_mode"]
            kill_gdm_server()
            config = load_config()
            setup_kernel_state(config, requested_mode)
            configure_xorg(config, requested_mode)

            state = {
                "type": "pending_post_xorg_start",
                "attempt_id": attempt_id,
                "requested_mode": requested_mode
            }

    except Exception:

        cleanup_xorg_conf()

        state = {
            "type": "pre_xorg_start_failed",
            "attempt_id": attempt_id,
            "requested_mode": requested_mode
        }

    finally:
        write_state(state)


def setup_post_xorg_start():

    try:
        prev_state = load_state()

        if prev_state["type"] == "pending_post_xorg_start":

            attempt_id = prev_state["attempt_id"]
            requested_mode = prev_state["requested_mode"]

            do_xsetup(requested_mode)
            config = load_config()
            set_DPI(config)

            state = {
                "type": "done",
                "attempt_id": attempt_id,
                "requested_mode": requested_mode
            } 

    except Exception:

        state = {
            "type": "post_xorg_start_failed",
            "attempt_id": attempt_id,
            "requested_mode": requested_mode
        }

    finally:
        write_state(state)
