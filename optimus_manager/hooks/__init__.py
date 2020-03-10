from ..config import load_config, copy_user_config
from ..kernel import setup_kernel_state
from .. import var
from ..xorg import configure_xorg, cleanup_xorg_conf, do_xsetup, set_DPI
from ..hacks.gdm import kill_gdm_server
from ..logging import logging


def setup_pre_daemon_start():

    startup_id = var.make_startup_id()

    with logging("startup", startup_id):

        try:
            cleanup_xorg_conf()
            copy_user_config()
            var.remove_last_acpi_call_state()
            startup_mode = var.get_startup_mode()

        except Exception as e:

            print("Daemon startup error: %s" % str(e))

            state = {
                "type": "startup_failed",
                "startup_mode": startup_mode,
                "startup_id": startup_id
            }

        else:

            state = {
                "type": "pending_pre_xorg_start",
                "requested_mode": startup_mode
            }

    var.write_state(state)
    setup_pre_xorg_start()


def setup_pre_xorg_start():

    prev_state = var.load_state()

    if prev_state is None or prev_state["type"] != "pending_pre_xorg_start":
        return

    attempt_id = var.make_attempt_id()

    with logging("switch", attempt_id):

        try:
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

        except Exception as e:

            print("Xorg pre-start setup error: %s" % str(e))

            cleanup_xorg_conf()

            state = {
                "type": "pre_xorg_start_failed",
                "attempt_id": attempt_id,
                "requested_mode": requested_mode
            }

    var.write_state(state)


def setup_post_xorg_start():

    prev_state = var.load_state()

    if prev_state is None or prev_state["type"] != "pending_post_xorg_start":
        return

    attempt_id = prev_state["attempt_id"]

    with logging("switch", attempt_id):

        try:
            requested_mode = prev_state["requested_mode"]

            do_xsetup(requested_mode)
            config = load_config()
            set_DPI(config)

            state = {
                "type": "done",
                "attempt_id": attempt_id,
                "requested_mode": requested_mode
            }

        except Exception as e:

            print("Xorg post-start setup error: %s" % str(e))

            state = {
                "type": "post_xorg_start_failed",
                "attempt_id": attempt_id,
                "requested_mode": requested_mode
            }

    var.write_state(state)
