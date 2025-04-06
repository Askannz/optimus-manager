from .. import envs
from ..checks import get_active_renderer, check_offloading_available, check_running_graphical_session, CheckError


def report_errors(state):
    if state is None:
        print("No state file")
        return True

    elif state["type"] == "startup_failed":
        print("Failed to start: optimus-manager.service")
        print("Log at %s/daemon/daemon-%s.log" % (envs.LOG_DIR_PATH, state["daemon_run_id"]))
        return True

    elif state["type"] == "pending_pre_xorg_start":
        if state["current_mode"] is None:
            print("GPU setup failed: Xorg pre-start hook did not run")
            return True

        else:
            print("GPU switch pending for next login: %s -> %s" % (state["current_mode"], state["requested_mode"]))

    elif state["type"] == "pre_xorg_start_failed":
        print("GPU setup failed: Xorg pre-start hook failed")
        print("Log at: %s/switch/switch-%s.log" % (envs.LOG_DIR_PATH, state["switch_id"]))
        return True

    elif state["type"] == "pending_post_xorg_start":
        print("GPU setup failed: Xorg post-start hook did not run")
        print("Log at: %s/switch/switch-%s.log" % (envs.LOG_DIR_PATH, state["switch_id"]))
        return True

    elif state["type"] == "post_xorg_start_failed":
        print("GPU setup failed: Xorg post-start hook failed")
        print("Log at: %s/switch/switch-%s.log" % (envs.LOG_DIR_PATH, state["switch_id"]))
        return True

    elif state["type"] == "done":
        if check_running_graphical_session():
            expected_renderer = {
                "integrated": "integrated",
                "hybrid": "integrated",
                "nvidia": "nvidia"
            }[state["current_mode"]]

            try:
                active_renderer = get_active_renderer()

            except CheckError as error:
                print("GPU setup failed: Unable to check the active card (%s): %s" % (expected_renderer, str(error)))
                print("Log at: %s/switch/switch-%s.log" % (envs.LOG_DIR_PATH, state["switch_id"]))
                return True

            if expected_renderer != active_renderer:
                print("GPU setup failed: Wrong active card: \"%s\" vs \"%s\"" % (active_renderer, expected_renderer))
                print("Log at: %s/switch/switch-%s.log" % (envs.LOG_DIR_PATH, state["switch_id"]))
                return True

            if state["current_mode"] == "hybrid" and not check_offloading_available():
                print("Hybrid mode doesn't work: the Nvidia card is unavailable for offloading")
                print("Log at: %s/switch/switch-%s.log" % (envs.LOG_DIR_PATH, state["switch_id"]))

        return False

    else:
        assert False
